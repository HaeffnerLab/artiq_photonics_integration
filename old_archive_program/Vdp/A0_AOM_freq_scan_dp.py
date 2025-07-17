
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from scipy.interpolate import interp1d

class A0_AOM_freq_scan_dp(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        self.setattr_device("sampler0")            

        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/729_sp_aux")

        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/729_dp")

        self.setattr_argument(
            "samples_per_shot",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
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




        
    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
  
        # Create datasets
        num_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_list_dataset("sampler_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="sampler_avg",
            x_data_name="frequencies_MHz"
        )

    @kernel
    def run(self):

        self.setup_run()
        self.sampler0.init()            
        self.core.break_realtime()

        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

        ##################################################################################################################################################
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_729_sp_aux.set_att(self.attenuation_729_sp)

        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_sp_aux.set(self.frequency_729_sp_aux)

        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.on()
        self.core.break_realtime()
        ##################################################################################################################################################

        n_channels = 8                                                                                          
        for i in range(n_channels):                                                     #loops for each sampler channel 
            self.sampler0.set_gain_mu(7-i, 0)                                           #sets each channel's gain to 0db

        ##################################################################################################################################################
        smp = [0.0]*n_channels                                                            #creates list of 8 floating point variables
        
       
        for freq in self.scan_freq_729_dp.sequence:

            self.dds_729_dp.set(freq)

            total_pmt_counts = 0.0
            for sample_i in range(self.samples_per_shot):
                
                delay(90*us)                                                                #90us delay to prevent uderflow in sampling stage                                   
                self.sampler0.sample(smp)                                                #runs sampler and saves to list 
                
                total_pmt_counts += smp[0]
                
                
            pmt_counts_avg = total_pmt_counts / self.samples_per_shot
            
            # Update the datasets
            self.experiment_data.append_list_dataset("sampler_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("frequencies_MHz", freq/MHz)
            
            delay(5*ms)
    
    # def analyze(self):
    #     att_sig=self.get_dataset("attenuation_dB")
    #     volt_sig=self.get_dataset("sampler_avg")

    #     # Create the interpolation function
    #     interpolation_function = interp1d(volt_sig, att_sig, fill_value="extrapolate", kind='linear')
        
    #     # Interpolate to find the corresponding x value for fx1
    #     x_value = interpolation_function(self.target_volt)

    #     print("The AOM attenuation should be set to: ", x_value, " dB.")







        