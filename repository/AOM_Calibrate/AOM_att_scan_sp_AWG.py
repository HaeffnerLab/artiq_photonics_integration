
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from scipy.interpolate import interp1d

from awg_utils.transmitter import send_exp_para

class A0_AOM_att_scan_sp_AWG(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        self.setattr_device("sampler0")            

        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_dp")

        self.setattr_argument(
            "samples_per_shot",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
        )

        self.setattr_argument(
            "scan_amp_729_sp",
            Scannable(
                default=RangeScan(
                    start=0.001,
                    stop=0.1,
                    npoints=30
                ),
                global_min=0,
                global_max=1,
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )

        self.setattr_argument(
            "target_volt",
            NumberValue(default=5.0, precision=8),
            tooltip="target power on the photodiode"
        )



        
    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
  
        # Create datasets
        num_samples = len(self.scan_amp_729_sp.sequence)
        self.experiment_data.set_list_dataset("sampler_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("amplitude", num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="sampler_avg",
            x_data_name="amplitude"
        )
    
    @rpc(flags={'async'})
    def send_exp_para(self, amp_729_sp):
        send_exp_para(["SingleTone",{"freq": self.frequency_729_sp,"amp": amp_729_sp, "num_loop":self.samples_per_shot+100}])

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
        self.dds_729_sp_aux.sw.off()
        self.dds_729_sp.sw.off()
        self.core.break_realtime()
        ##################################################################################################################################################
        n_channels = 8                                                                                          
        for i in range(n_channels):                                                     #loops for each sampler channel 
            self.sampler0.set_gain_mu(7-i, 0)                                           #sets each channel's gain to 0db
        smp = [0.0]*n_channels                                                            #creates list of 8 floating point variables
        ##################################################################################################################################################
        
        self.ttl_rf_switch_DDS_729SP.off()
        self.ttl_rf_switch_AWG_729SP.on()
        
        for amp in self.scan_amp_729_sp.sequence:

            self.send_exp_para(amp)
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue
            
            self.ttl_awg_trigger.pulse(1*us)
            self.dds_729_dp.sw.on()

            delay(1*ms)

            total_pmt_counts = 0.0
            for sample_i in range(self.samples_per_shot):
                
                delay(100*us)                                                                #90us delay to prevent uderflow in sampling stage                                   
                self.sampler0.sample(smp)                                                #runs sampler and saves to list 
                total_pmt_counts += smp[0]
            delay(50*us)
            #self.dds_729_dp.sw.off()

            pmt_counts_avg = total_pmt_counts / self.samples_per_shot
            
            # Update the datasets
            self.experiment_data.append_list_dataset("sampler_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("amplitude", amp)
            
            self.core.break_realtime()
        
        #protect ion
        self.seq.ion_store.run()
    
    def analyze(self):
        amp_sig=self.get_dataset("amplitude")
        volt_sig=self.get_dataset("sampler_avg")

        # Create the interpolation function
        interpolation_function = interp1d(volt_sig, amp_sig, fill_value="extrapolate", kind='linear')
        
        # Interpolate to find the corresponding x value for fx1
        x_value = interpolation_function(self.target_volt)

        print("The AOM amp should be set to: ", x_value, " dB.")







        