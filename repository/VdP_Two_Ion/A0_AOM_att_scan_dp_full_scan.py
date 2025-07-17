
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

class A0_AOM_att_scan_dp_full_scan(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        self.setattr_device("sampler0")            

        #self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_sp")
        #.add_arg_from_param("attenuation/729_dp")

        self.setattr_argument(
            "samples_per_shot",
            NumberValue(default=200, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
        )

        self.setattr_argument(
            "scan_freq_729_dp",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")-3*self.parameter_manager.get_param("qubit/vib_freq"),
                    stop=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")+3*self.parameter_manager.get_param("qubit/vib_freq"),
                    npoints=20
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
            "scan_att_729_dp",
            Scannable(
                default=RangeScan(
                    start=10*dB,
                    stop=25*dB,
                    npoints=100
                ),
                global_min=8*dB,
                global_max=31.5*dB,
                unit="dB",
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )

        self.setattr_argument(
            "target_volt",
            NumberValue(default=1.3, precision=8),
            tooltip="target power on the photodiode"
        )



        
    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
  
        # Create datasets
        num_freq = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation_dB", num_freq, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_freq, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            x_data_name="frequencies_MHz",
            y_data_name="attenuation_dB",
            fit_data_name='fit_signal'
        )

        self.V_list=[0.0]*len(self.scan_att_729_dp.sequence)
        self.att_list=[self.scan_att_729_dp.sequence[i]/dB for i in range(len(self.scan_att_729_dp.sequence))]
        self.att_res=0.0

    @kernel
    def run(self):

        self.setup_run()
        
        self.sampler0.init()            
        self.core.break_realtime()

        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

        ##################################################################################################################################################
        #self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
       
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.on()
        self.core.break_realtime()
        ##################################################################################################################################################

        n_channels = 8                                                                                          
        for i in range(n_channels):                                                     #loops for each sampler channel 
            self.sampler0.set_gain_mu(7-i, 0)                                           #sets each channel's gain to 0db

        ##################################################################################################################################################
        smp = [0.0]*n_channels                                                            #creates list of 8 floating point variables
        self.core.break_realtime()
        delay(3*s)
    
        for freq in self.scan_freq_729_dp.sequence:
            self.dds_729_dp.set(freq)
            for att_i in range(len(self.scan_att_729_dp.sequence)):

                att=self.scan_att_729_dp.sequence[att_i]
                self.dds_729_dp.set_att(att)

                delay(5*ms)

                total_pmt_counts = 0.0
                for sample_i in range(self.samples_per_shot):

                    delay(100*us)  
                    self.dds_729_dp.sw.on()
                    delay(20*us)                                                              #90us delay to prevent uderflow in sampling stage                                   
                    self.sampler0.sample(smp)                                                #runs sampler and saves to list 
                    delay(10*us)  
                    self.dds_729_dp.sw.off()
                    delay(100*us)  
                    total_pmt_counts += smp[0]
                delay(50*us)
               

                self.V_list[att_i]= total_pmt_counts / self.samples_per_shot

            self.att_res=self.get_att(self.V_list)
            # Update the datasets
            self.experiment_data.append_list_dataset("frequencies_MHz", freq/MHz)
            self.experiment_data.append_list_dataset("attenuation_dB", self.att_res)
                
            self.core.break_realtime()
        

        #protect ion
        self.seq.ion_store.run()
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
    
    @rpc
    def get_att(self, Vlist)->float:
        #print(len(Vlist), len(self.att_list))

        ydata=savgol_filter(self.att_list, window_length=9, polyorder=3)

        interpolation_function = interp1d(Vlist, ydata, fill_value="extrapolate", kind='linear')
        
        return float(interpolation_function(self.target_volt))
    

    def analyze(self):
        num_freq = len(self.scan_freq_729_dp.sequence)
        att_sig= savgol_filter(self.get_dataset("attenuation_dB"), window_length=7, polyorder=3)

        self.set_dataset('fit_signal', att_sig, broadcast=True)


        with open(get_config_dir()/'../repository/Vdp/freq_att.txt', 'w') as f:
            for i in range(num_freq):
                f.write(f"{self.scan_freq_729_dp.sequence[i]/MHz}, {att_sig[i] }\n")




        