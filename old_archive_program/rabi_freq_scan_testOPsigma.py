from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class RabiFreqScan_testop(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        # self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump_sigma.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'Lorentzian', 218)

        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")

        self.setattr_argument("enable_pi_pulse", BooleanValue(False), group='Pi pulse excitation')
        self.setattr_argument(
            "PI_freq_729_dp",
            NumberValue(default=233.705*MHz, min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_att_729_dp",
            NumberValue(default=20*dB, min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )

        self.setattr_argument(
            "rabi_t",
            NumberValue(default=7.34*us, min=0*us, max=5*ms, unit="us",precision=6)
        )

        
        self.setattr_argument(
            "scan_freq_729_dp",
            Scannable(
                default=RangeScan(
                    start=233.5*MHz,
                    stop=233.9*MHz,
                    npoints=100
                ),
                global_min=150*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        

    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_729_dp.sequence)) 

    
  
    def prepare(self):
         # Create datasets
        num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_freq], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq_samples, broadcast=True)

        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=True,
            fit_data_name='fit_signal'
        )



    @kernel
    def run(self):

        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        freq_i = 0
        for freq_729_dp in self.scan_freq_729_dp.sequence: # scan the frequency

            self.dds_729_dp.set(freq_729_dp)

            #PMT
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            self.seq.ion_store.run()
            delay(200*us)

            while sample_num<self.samples_per_freq:
            
                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                   continue
                sample_num+=1
                
                #turn off all dds
                self.seq.off_dds.run()
                #854 repump
                self.seq.repump_854.run()
                # Cool
                self.seq.doppler_cool.run()
                self.seq.op_pump_sigma.run()
                delay(5*us)
            
                if self.enable_pi_pulse:
                    #self.rabi(self.PI_drive_time, self.freq_729_pi,0.0)
                    self.seq.rabi.run(self.PI_drive_time,
                                  self.PI_freq_729_dp,
                                  self.frequency_729_sp,
                                  self.PI_att_729_dp,
                                  self.attenuation_729_sp
                    )

                # Attempt Rabi flop
                self.seq.rabi.run(self.rabi_t,
                                  freq_729_dp,
                                  self.frequency_729_sp,
                                  self.attenuation_729_dp,
                                  self.attenuation_729_sp
                )

                #qubit readout
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()

                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [freq_i, sample_num],
                                            num_pmt_pulses)
                                            
                #update the total count & thresholded events
                total_pmt_counts += num_pmt_pulses
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(2*ms)
                     
            
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_729_dp / MHz)
            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          -float(total_pmt_counts) / self.samples_per_freq)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
            
            delay(5*ms)

        self.seq.ion_store.run()


    # def analyze(self):

    #     x=self.get_dataset("frequencies_MHz")
    #     y=self.get_dataset('pmt_counts_avg')

    #     self.fitting_func.fit(x,y)


    