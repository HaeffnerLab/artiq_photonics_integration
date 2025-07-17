
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from scipy.interpolate import interp1d

from awg_utils.transmitter import send_exp_para
from acf.utils import get_config_dir
from acf.function.fitting import *


class A0_AOM_freq_scan_sp(_ACFExperiment):
    def build(self):

        
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'Savgol_filter', -999)

        self.setattr_device("sampler0")            

        #self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_dp")

        	
        self.setattr_argument(
            "frequency_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "samples_per_shot",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
        )

        self.setattr_argument(
            "att_sp",
            NumberValue(default=13*dB, unit='dB', precision=8),
            tooltip="single pass awg voltage"
        )

        self.setattr_argument(
            "scan_freq_729_sp",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("frequency/729_sp")-2*MHz,
                    stop=self.parameter_manager.get_param("frequency/729_sp")+2*MHz,
                    npoints=200
                ),
                global_min=50*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )



        
    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_729_sp.sequence)) 

        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
  
        # Create datasets
        num_samples = len(self.scan_freq_729_sp.sequence)
        self.experiment_data.set_list_dataset("sampler_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("freq_sp", num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="sampler_avg",
            x_data_name="freq_sp",
            fit_data_name='fit_signal'
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
        self.dds_729_dp.set(self.frequency_729_dp)
        

        self.dds_729_dp.sw.on()
        self.core.break_realtime()
        ##################################################################################################################################################
        n_channels = 8                                                                                          
        for i in range(n_channels):                                                     #loops for each sampler channel 
            self.sampler0.set_gain_mu(7-i, 0)                                           #sets each channel's gain to 0db
        smp = [0.0]*n_channels                                                            #creates list of 8 floating point variables
        ##################################################################################################################################################
        self.ttl_rf_switch_DDS_729SP.on()
        self.ttl_rf_switch_AWG_729SP.on()
        for freq_sp in self.scan_freq_729_sp.sequence:

            self.dds_729_sp.set_att(self.att_sp)
            self.dds_729_sp.set(freq_sp)
            self.core.break_realtime()
            
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()

            delay(1*ms)

            total_pmt_counts = 0.0
            for sample_i in range(self.samples_per_shot):
                
                delay(90*us)                                                                #90us delay to prevent uderflow in sampling stage                                   
                self.sampler0.sample(smp)                                                #runs sampler and saves to list 
                total_pmt_counts += smp[0]
            delay(50*us)

            self.dds_729_dp.sw.off()
            self.dds_729_sp.sw.off()

            pmt_counts_avg = total_pmt_counts / self.samples_per_shot
            
            # Update the datasets
            self.experiment_data.append_list_dataset("sampler_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("freq_sp", freq_sp)
            
            self.core.break_realtime()
        
        #protect ion
        self.seq.ion_store.run()
        self.dds_729_dp.sw.off()
    
    def analyze(self):
        freq_sp=self.get_dataset("freq_sp")
        volt_sig=self.get_dataset("sampler_avg")

        self.fitting_func.fit(freq_sp, volt_sig)#[1]

        volt_fit=self.fitting_func.fitted_array

        with open(get_config_dir()/'../repository/Vdp/power_sp.txt', 'w') as f:
            for i in range(len(freq_sp)):
                f.write(f"{freq_sp[i]/MHz}, {volt_fit[i] }\n")

    #     # Create the interpolation function
    #     interpolation_function = interp1d(volt_sig, amp_sig, fill_value="extrapolate", kind='linear')
        
    #     # Interpolate to find the corresponding x value for fx1
    #     x_value = interpolation_function(self.target_volt)

    #     print("The AOM amp should be set to: ", x_value, " dB.")







        