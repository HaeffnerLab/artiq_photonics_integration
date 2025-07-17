
from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from awg_utils.transmitter import send_exp_para

from scipy.interpolate import interp1d

import numpy as np

import pickle

class A1_two_tone_Att_scan_sp_aux_AWG(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)
        

        self.setattr_argument(
            "rabi_t",
            NumberValue(default=4.0*us, min=0.*us, max=100*us, unit='us', precision=8),
            tooltip="Ramsey pulse time if don't scan this dimension"
        )   

        self.setattr_argument(
            "freq_729_vib_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/vib_freq")
                        , min=0*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )
	
        self.setattr_argument(
            "freq_729_dp1",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
                        , min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )
        self.setattr_argument(
            "freq_729_dp2",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
                        , min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )


        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=0.1, min=1e-4, max=0.8, precision=8),
            tooltip="729 single pass amplitude"
        )
               
        self.setattr_argument(
            "scan_amp_729_sp_aux",
            Scannable(
                default=RangeScan(
                    start=0.05,#self.parameter_manager.get_param("attenuation/729_sp")-1*dB,
                    stop=0.15, #self.parameter_manager.get_param("attenuation/729_sp")+4*dB,
                    npoints=10
                ),
                global_min=0.0,
                global_max=0.8,
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )


        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=200, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    

        #will be covered in prepare process
        self.att_729_dp1=14*dB
        self.att_729_dp2=14*dB


    def prepare(self):

        self.freq_729_dp1+=self.freq_729_vib_dp
        self.freq_729_dp2-=self.freq_729_vib_dp
        self.freq_729_sp-=2*self.freq_729_vib_dp
        self.freq_729_sp_aux+=2*self.freq_729_vib_dp


        self.fitting_func.setup(len(self.scan_amp_729_sp_aux.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_amp_729_sp_aux.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("amp_sp_aux", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="amp_sp_aux",
            pen=False,
            fit_data_name='fit_signal'
        )
        
        self.setup_dp_att()



    def setup_dp_att(self):

        # Initialize empty lists to store x and y values
        freq_data =[]
        att_data = []
        # Read the file and parse each line
        with open(get_config_dir()/'../repository/Vdp/freq_att.txt', 'r') as f:
            for line in f:
               
                # Split the line by the comma and strip any extra whitespace
                x_val, y_val = line.strip().split(', ')
                freq_data.append(float(x_val))  # Convert x value to int
                att_data.append(float(y_val))  # Convert y value to float

       

        # Create the interpolation function
        interpolation_function = interp1d(freq_data, att_data, fill_value="extrapolate", kind='linear')

        self.att_729_dp1 =  float(interpolation_function(self.freq_729_dp1/MHz))*dB
        self.att_729_dp2 =  float(interpolation_function(self.freq_729_dp2/MHz))*dB

        print(self.att_729_dp1, self.att_729_dp2)

    @rpc
    def send_exp_para(
        self,
        freq_RSB,
        freq_BSB,
        amp_RSB,
        amp_BSB   
    ):
        send_exp_para(["SDF", {
                "freq_sp_RSB":   freq_RSB,
                "freq_sp_BSB":   freq_BSB,
                "amp_sp_RSB":  amp_RSB,
                "amp_sp_BSB":   amp_BSB
            }])  

    @kernel
    def rabi_AWG(self,pulse_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)

        
        self.ttl_rf_switch_AWG_729SP.on()
        self.ttl_rf_switch_DDS_729SP.off()
        self.ttl_awg_trigger.pulse(1*us)
            
        self.dds_729_sp.sw.off()
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()

        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        delay(200*us)
        for att_i in range(len(self.scan_amp_729_sp_aux.sequence)): 

            total_thresh_count1 = 0
            total_thresh_count2 = 0

            sample_num=0
            amp_sp_aux = self.scan_amp_729_sp_aux.sequence[att_i]

            delay(200*us)
            self.seq.ion_store.run()
            self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp,amp_sp_aux,self.amp_729_sp)   
            delay(25*ms)

            while sample_num<self.samples_per_time:
                
                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)

                ######################################################################
                self.seq.repump_854.run()

                #  Cool
                self.seq.doppler_cool.run()
                self.seq.sideband_cool.run()

                ######################################################################

                # Attempt Rabi flop
                self.rabi_AWG(self.rabi_t, self.freq_729_dp1 , self.att_729_dp1)
                
                #read out
                num_pmt_pulses1=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                ############################################################################ sp aux ramp up

                #  Cool
                self.seq.doppler_cool.run()
                self.seq.sideband_cool.run()

                self.rabi_AWG(self.rabi_t, self.freq_729_dp2 , self.att_729_dp2)

                #read out
                num_pmt_pulses2=self.seq.readout_397.run()
                # 854 repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()
                delay(20*us)
                ############################################################################

                # Update dataset
                # self.experiment_data.insert_nd_dataset("pmt_counts",
                #                             [att_i, sample_num],
                #                             num_pmt_pulses1-num_pmt_pulses2)
                
                if num_pmt_pulses1 < self.threshold_pmt_count:
                    total_thresh_count1 += 1
                if num_pmt_pulses2 < self.threshold_pmt_count:
                    total_thresh_count2 += 1

                delay(2*ms)
            
            self.experiment_data.append_list_dataset("amp_sp_aux", amp_sp_aux)

            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count1-total_thresh_count2) / self.samples_per_time)
            delay(2*ms)

        self.seq.ion_store.run()
    
    def analyze(self):
        x=self.get_dataset("amp_sp_aux")
        y=self.get_dataset('pmt_counts_avg_thresholded')
        #self.fitting_func.fit(rabi_time, rabi_PMT)

        coefficients = np.polyfit(x, y, 1)  # coefficients[0] is the slope, coefficients[1] is the intercept
    
        # The equation of the line is y = slope * x + intercept
        slope, intercept = coefficients
    
        # Find x where y = 0 (i.e., solving 0 = slope * x + intercept)
        if slope == 0:
            raise ValueError("The slope of the line is zero, no zero crossing.")
    
        x_zero = -intercept / slope

        fitted_array=slope*x+intercept

        self.set_dataset('fit_signal', fitted_array, broadcast=True)
        

        print("find power balance at amp_sp_aux = ", x_zero, " V")


    
    
