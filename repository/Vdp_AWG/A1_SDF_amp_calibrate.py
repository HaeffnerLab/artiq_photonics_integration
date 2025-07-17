
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

class A1_SDF_amp_calibrate_AWG(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()


        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
                        , min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument("enable_dp_freq_compensation", BooleanValue(True))
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )
        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("SDF/amp_729_sp"), min=1e-4, max=0.8, precision=8),
            tooltip="729 single pass amplitude"
        )
        self.setattr_argument(
            "amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("SDF/amp_729_sp_aux"), min=1e-4, max=0.8, precision=8),
            tooltip="729 single pass amplitude"
        )

        self.setattr_argument("Scan_Type", EnumerationValue(['Delta_s', 'Delta_m'], default= 'Delta_s'))
        self.setattr_argument(
            "rot_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
                        , min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group = "pi/2 rotation"
        )
        self.setattr_argument(
            "rot_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group = "pi/2 rotation"
        )
        self.setattr_argument(
            "rot_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 single pass amplitude",
            group = "pi/2 rotation"
        )
        self.setattr_argument(
            "rot_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("AWG_amplitude/729_sp"), min=1e-4, max=0.8, precision=8),
            tooltip="729 single pass amplitude",
            group = "pi/2 rotation"
        )
        self.setattr_argument(
            "rot_time",
            NumberValue(default=4.0*us, min=0.*us, max=100*us, unit='us', precision=8),
            tooltip="Ramsey pulse time if don't scan this dimension",
            group = "pi/2 rotation"
        )   

        self.setattr_argument(
            "scan_amp",
            Scannable(
                default=RangeScan(
                    start=-0.01,
                    stop=0.01,
                    npoints=30
                ),
                global_min=-0.1,
                global_max=0.1,
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )
        self.setattr_argument(
            "SDF_time",
            NumberValue(default=40.0*us, min=0.*us, max=100*us, unit='us', precision=8),
            tooltip="Ramsey pulse time if don't scan this dimension"
        )   

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("enable_collision_detection", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    



    def prepare(self):
        #self.fitting_func.setup(len(self.scan_amp_729_sp_aux.sequence))
        # Create datasets
        num_amp_samples = len(self.scan_amp.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_amp_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_amp_samples, broadcast=True)
        self.experiment_data.set_list_dataset("del_amp", num_amp_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_amp_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="del_amp",
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

        self.att_729_dp =  float(interpolation_function(self.freq_729_dp/MHz))*dB

        print(self.att_729_dp)

    @rpc(flags={'async'})
    def send_exp_para(
        self,
        freq_RSB,
        freq_BSB,
        amp_RSB,
        amp_BSB   
    ):
        send_exp_para(["SDF_Square", {
                "freq_sp_RSB":   freq_RSB,
                "freq_sp_BSB":   freq_BSB,
                "amp_sp_RSB":  amp_RSB,
                "amp_sp_BSB":   amp_BSB,

                "if_x_Rot": 1 if self.Scan_Type == 'Delta_s' else 0 ,
                "freq_sp":  self.rot_freq_729_sp,
                "amp_sp":self.rot_amp_729_sp,
                "num_loop":max(self.samples_per_time+100,200)
            }])  

    # @rpc(flags={'async'})
    # def send_exp_para(self):
    #     send_exp_para(["SingleTone",{"freq": self.rot_freq_729_sp,"amp": self.rot_amp_729_sp, "num_loop":max(self.samples_per_time+100,1000)}])
  
    
    @kernel
    def rabi_AWG(self, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        
        self.ttl_rf_switch_AWG_729SP.on()
        self.ttl_rf_switch_DDS_729SP.on()

        
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        delay(5*us)

        if self.Scan_Type == 'Delta_s':
            #pi/2
            self.dds_729_dp.set_att(self.rot_att_729_dp)
            self.ttl_awg_trigger.pulse(1*us)
            delay(2*us)
            self.dds_729_dp.sw.on()
            delay(self.rot_time)
            self.dds_729_dp.sw.off()



            self.dds_729_dp.set_att(att_729_dp)
            delay(2*us) 
            for _ in range(4):
                self.ttl_awg_trigger.pulse(1*us)
                delay(2*us)
                self.dds_729_dp.sw.on()
                delay(self.SDF_time)
                self.dds_729_dp.sw.off()
                delay(2*us) 
            
            #pi/2
            self.dds_729_dp.set_att(self.rot_att_729_dp)
            self.ttl_awg_trigger.pulse(1*us)
            delay(2*us)
            self.dds_729_dp.sw.on()
            delay(self.rot_time)
            self.dds_729_dp.sw.off()

            #turn off
            self.ttl_awg_trigger.pulse(1*us)
        else:
            self.dds_729_dp.set_att(att_729_dp)
            delay(2*us) 
            for _ in range(4):
                self.ttl_awg_trigger.pulse(1*us)
                delay(2*us)
                self.dds_729_dp.sw.on()
                delay(self.SDF_time)
                self.dds_729_dp.sw.off()
                delay(2*us) 

            #turn off
            self.ttl_awg_trigger.pulse(1*us)
 

        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.off()

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        delay(200*us)
        for amp_i in range(len(self.scan_amp.sequence)): 

            total_thresh_count = 0
            sample_num=0

            # delta frequency
            del_amp = self.scan_amp.sequence[amp_i]

            self.seq.ion_store.run()
            delay(200*us)

            if self.Scan_Type == 'Delta_s':
                self.send_exp_para(self.freq_729_sp_aux , self.freq_729_sp, self.amp_729_sp_aux+del_amp, self.amp_729_sp)  
            else:
                self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp , self.amp_729_sp_aux+del_amp, self.amp_729_sp)  
            
            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue

            while sample_num<self.samples_per_time:
                if is_ion_good:
                    #line trigger
                    
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    ######################################################################
                    self.seq.repump_854.run()
                    self.seq.doppler_cool.run()
                    self.seq.sideband_cool.run()

                    # Attempt Rabi flop
                    self.rabi_AWG(self.freq_729_dp , self.att_729_dp)
                    
                    #read out
                    num_pmt_pulses=self.seq.readout_397.run()

                    if num_pmt_pulses < self.threshold_pmt_count and self.enable_collision_detection:

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
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [time_i, sample_num],
                        #                             num_pmt_pulses)
                        
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        #total_pmt_counts += num_pmt_pulses

                        delay(3*ms)
                else:
                    self.seq.ion_store.run()
                    delay(0.9*s)
                    self.seq.doppler_cool.run()
                    num_pmt_pulses_detect=self.seq.readout_397.run()
                    if num_pmt_pulses_detect >= self.threshold_pmt_count:
                        is_ion_good = True
                        num_try_save_ion = 0
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>20):
                        print("Ion Lost!!!")
                        time_i=+10000
                        sample_num+=10000
                        break

            
            self.experiment_data.append_list_dataset("del_amp", del_amp)

            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            self.core.break_realtime()

        self.seq.ion_store.run()
    
    # def analyze(self):
    #     x=self.get_dataset("amp_sp_aux")
    #     y=self.get_dataset('pmt_counts_avg_thresholded')
    #     #self.fitting_func.fit(rabi_time, rabi_PMT)

    #     coefficients = np.polyfit(x, y, 1)  # coefficients[0] is the slope, coefficients[1] is the intercept
    
    #     # The equation of the line is y = slope * x + intercept
    #     slope, intercept = coefficients
    
    #     # Find x where y = 0 (i.e., solving 0 = slope * x + intercept)
    #     if slope == 0:
    #         raise ValueError("The slope of the line is zero, no zero crossing.")
    
    #     x_zero = -intercept / slope

    #     fitted_array=slope*x+intercept

    #     self.set_dataset('fit_signal', fitted_array, broadcast=True)
        

    #     print("find power balance at amp_sp_aux = ", x_zero, " V")


    
    
