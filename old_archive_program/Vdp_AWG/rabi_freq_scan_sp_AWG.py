from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

from awg_utils.transmitter import send_exp_para

class RabiFreqScan_sp(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'Lorentzian', -999)

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=40*MHz, max=360*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument("enable_dp_freq_compensation", BooleanValue(True),group="rabi")        
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=30*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=100*us, min=0*us, max=5*ms, unit="us",precision=6),
            group="rabi"
        )

        
        self.setattr_argument(
            "scan_del_freq_729_sp",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("qubit/vib_freq")*4-0.02*MHz,
                    stop=self.parameter_manager.get_param("qubit/vib_freq")*4+0.02*MHz,
                    npoints=40
                ),
                global_min=-100*MHz,
                global_max=2500*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=8
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        self.setattr_argument("enable_sideband_cool", BooleanValue(False))
        self.setattr_argument("enable_collision_detection", BooleanValue(True))
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        
    
    def prepare(self):
         # Create datasets
        num_freq_samples = len(self.scan_del_freq_729_sp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_freq], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq_samples, broadcast=True)

        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        self.fitting_func.setup(len(self.scan_del_freq_729_sp.sequence)) 

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=True,
            fit_data_name='fit_signal'
        )

    @kernel
    def rabi(self,pulse_time, 
             freq_729_dp, att_729_dp,
             freq_729_sp, att_729_sp
             ):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)
        self.dds_729_sp.set(freq_729_sp)
        self.dds_729_sp.set_att(att_729_sp)
        
        self.dds_729_sp.sw.on()
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.dds_729_sp.sw.off()


    @kernel
    def run(self):

        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        freq_i = 0
        while freq_i < len(self.scan_del_freq_729_sp.sequence):

            freq_729_sp=self.freq_729_sp+self.scan_del_freq_729_sp.sequence[freq_i]

            #PMT
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            # Cool
            self.seq.ion_store.run()

            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            delay(1*ms)


            while sample_num<self.samples_per_freq:

                if is_ion_good:
                
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    delay(50*us)
                    
                    #854 repump
                    self.seq.repump_854.run()
                    # Cool
                    self.seq.doppler_cool.run()

                    if self.enable_sideband_cool:
                        self.seq.sideband_cool.run()
                    else:
                        self.seq.op_pump.run()
                    delay(5*us)
                    
                    # if self.enable_pi_pulse:
                    #     #self.rabi(self.PI_drive_time, self.freq_729_pi,0.0)
                    #     self.seq.rabi.run(self.PI_drive_time,
                    #                 self.PI_freq_729_dp,
                    #                 self.frequency_729_sp,
                    #                 self.PI_att_729_dp,
                    #                 self.attenuation_729_sp
                    #     )

                    # rabi 
                    self.rabi(self.rabi_t, 
                              self.freq_729_dp, self.att_729_dp,
                              freq_729_sp, self.att_729_sp
                              )

                    #qubit readout
                    num_pmt_pulses=self.seq.readout_397.run()

                    if num_pmt_pulses < self.threshold_pmt_count  and self.enable_collision_detection:

                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        num_pmt_pulses_detect=self.seq.readout_397.run()
                        self.seq.ion_store.run()
                        delay(20*us)

                        if num_pmt_pulses_detect < self.threshold_pmt_count:
                            is_ion_good = False
                            
                    if is_ion_good:
                        sample_num+=1
                        # Update dataset
                        self.experiment_data.insert_nd_dataset("pmt_counts",
                                                    [freq_i, sample_num],
                                                    num_pmt_pulses)
                        
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        total_pmt_counts += num_pmt_pulses

                        delay(2*ms)
                else:
                    self.seq.ion_store.run()
                    delay(0.5*s)
                    self.seq.doppler_cool.run()
                    num_pmt_pulses_detect=self.seq.readout_397.run()
                    if num_pmt_pulses_detect >= self.threshold_pmt_count:
                        is_ion_good = True
                        num_try_save_ion = 0
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>40):
                        print("Ion Lost!!!")
                        freq_i=+100000
                        sample_num+=10000
                        break
                     
            
            self.experiment_data.append_list_dataset("frequencies_MHz", self.scan_del_freq_729_sp.sequence[freq_i] / MHz)
            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          -float(total_pmt_counts) / self.samples_per_freq)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
            
            delay(5*ms)

        self.seq.ion_store.run()


    def analyze(self):

        x=self.get_dataset("frequencies_MHz")
        y=self.get_dataset('pmt_counts_avg')

        self.fitting_func.fit(x,y)


    