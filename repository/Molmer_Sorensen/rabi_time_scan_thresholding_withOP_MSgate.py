

# calibrate for bichromatic light

# configuration 1
#                   frequency                            attenuation
# double pass:      line_freq+vib                        att1

# configuration 2
# double pass:      line_freq-vib                        att2

# step 1:
# single tone, manually change double pass frequency between line_freq+vib & line_freq-vib
# measure power with photodiode to balance power between these two frequencies

# step 2:
# do the two configuration measurement

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d

class MS_time_scan(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)
        


        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=100*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument("enable_dp_freq_compensation", BooleanValue(True))
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )


        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("enable_sideband_cool", BooleanValue(True))
      
        
        self.setattr_argument(
            "threshold_pmt_count_1ion",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    

        self.setattr_argument(
            "threshold_pmt_count_2ion",
            NumberValue(default=2*self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    


    def prepare(self):
        self.fitting_func.setup(len(self.scan_rabi_t.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_rabi_t.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
            fit_data_name='fit_signal'
        )
        
    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        delay(50*us)
        for time_i in range(len(self.scan_rabi_t.sequence)): 
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0
            rabi_t = self.scan_rabi_t.sequence[time_i]
            delay(200*us)
            self.seq.ion_store.run()
            delay(200*us)

            while sample_num<self.samples_per_time:
                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(20*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)
                self.seq.off_dds.run()
                self.seq.repump_854.run()
                #  Cool
                self.seq.doppler_cool.run()
                self.seq.sideband_cool_2mode.run()
                delay(5*us)
                
               
                self.seq.displacement.run( rabi_t,
                     self.att_729_dp, 
                     self.freq_729_dp, 
                     drive_phase_sp =0.0
                )


                #read out
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                # Update dataset
                # self.experiment_data.insert_nd_dataset("pmt_counts",
                #                             [time_i, sample_num],
                #                             num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count_1ion:
                    total_thresh_count += 2
                elif num_pmt_pulses < self.threshold_pmt_count_2ion:
                    total_pmt_counts += 1

                total_pmt_counts += num_pmt_pulses

                delay(1*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)

            
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            delay(5*ms)

        self.seq.ion_store.run()
    
    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        self.fitting_func.fit(rabi_time, rabi_PMT)


    
    
