from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para

class A6_att_scan_SDF_AWG_Cam(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()


        self.seq.cam_two_ions.build()
        
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=4*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="rabi"
        )
        self.setattr_argument("vib_mode", EnumerationValue(["mode1","mode2","mode_single_ion"], default="mode1"))
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )

        self.setattr_argument(
            "scan_amp_729_sp_aux",
            Scannable(
                default=RangeScan(
                    start=0.15,
                    stop=0.25, 
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
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool2mode", "opticalpumping", "sidebandcool_single_ion"], default="sidebandcool2mode"))

        self.calibration_data="__param__VdP2mode/amp_729_mode2_sp_aux"
        


        self.freq_vib1=self.get_vib_freq1()
        self.freq_vib2=self.get_vib_freq2()
        self.sideband_mode1_att729=self.parameter_manager.get_float_param('sideband2mode/mode1_att_729')
        self.sideband_mode1_att854=self.parameter_manager.get_float_param('sideband2mode/mode1_att_854')
        self.sideband_mode2_att729=self.parameter_manager.get_float_param('sideband2mode/mode2_att_729')
        self.sideband_mode2_att854=self.parameter_manager.get_float_param('sideband2mode/mode2_att_854')

        self.freq_729_dp1=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
        self.freq_729_dp2=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
        self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")
        self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")
        self.freq_729_vib=0.548*MHz

        self.att_729_dp1=14*dB
        self.att_729_dp2=14*dB

        self.amp_729_sp=0.1
  

    def get_qubit_freq(self)->float:
        return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_vib_freq1(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq1', archive=False)
    def get_vib_freq2(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq2', archive=False)
    
    def prepare(self):
        # Create datasets
        num_samples = len(self.scan_amp_729_sp_aux.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("amp_sp_aux", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="amp_sp_aux",
            pen=False,
            pos_data_name="pos",
            fit_data_name='fit_signal'
        )

        if self.vib_mode=="mode1":
            self.freq_729_vib=self.parameter_manager.get_param("VdP2mode/vib_freq1")
            self.amp_729_sp=self.parameter_manager.get_param("VdP2mode/amp_729_mode1_sp")
            self.calibration_data="VdP2mode/amp_729_mode1_sp_aux"
        elif self.vib_mode=="mode2":
            self.freq_729_vib=self.parameter_manager.get_param("VdP2mode/vib_freq2")
            self.amp_729_sp=self.parameter_manager.get_param("VdP2mode/amp_729_mode2_sp")
            self.calibration_data="VdP2mode/amp_729_mode2_sp_aux"
        else:
            self.freq_729_vib=self.parameter_manager.get_param("qubit/vib_freq")
            self.amp_729_sp=self.parameter_manager.get_param("SDF/amp_729_sp")
            self.calibration_data="SDF/amp_729_sp_aux"
        
        #for power balancer
        self.freq_729_dp1+=self.freq_729_vib/2.0
        self.freq_729_dp2-=self.freq_729_vib/2.0
        self.freq_729_sp-=self.freq_729_vib
        self.freq_729_sp_aux+=self.freq_729_vib
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




    @kernel
    def rabi_AWG(self, pulse_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)

        
        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()

        self.ttl_awg_trigger.pulse(1*us)
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)

        
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @kernel
    def exp_seq(self, freq_729_dp, att_729_dp,  ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()

        freq_diff_dp = self.freq_diff_dp if ion_status_detect==2 else 0.0
        if self.cooling_option == "sidebandcool_single_ion":
            self.seq.sideband_cool.run(freq_diff_dp=freq_diff_dp)
        elif self.cooling_option == "sidebandcool":
            self.seq.sideband_cool.run(freq_offset=self.freq_vib2, 
                                           att_729_here=self.sideband_mode2_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.sideband_mode2_att854) 
            self.seq.sideband_cool.run(freq_offset=self.freq_vib1, 
                                           att_729_here=self.sideband_mode1_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.sideband_mode1_att854) 
            
        elif self.cooling_option == "sidebandcool2mode":
            self.seq.sideband_cool_2mode.run(freq_diff_dp=freq_diff_dp) 
        else:
            self.seq.op_pump.run()
        delay(5*us)
        
        # rabi 
        self.rabi_AWG(self.rabi_t, freq_729_dp + freq_diff_dp, att_729_dp)

    @rpc(flags={'async'})
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
                "amp_sp_BSB":   amp_BSB,
                "num_loop": 500
            }])  
  

        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.rf.set_voltage(1)
        self.core.break_realtime()

        self.seq.cam_two_ions.cam_setup()
        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1
        

        #detecting the initial position of the ion 
        while ion_status_detect_last!=1 and ion_status_detect_last!=2:
            delay(2*ms)
            self.seq.repump_854.run()
            self.seq.doppler_cool.run()
            delay(5*us)
            ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
            self.seq.ion_store.run()
            delay(1*ms)
        
        if(ion_status_detect_last==3): 
            i=10000000
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last


        i=0
        while i < len(self.scan_amp_729_sp_aux.sequence):

            total_thresh_count1 = 0
            total_thresh_count2 = 0

            sample_num=0
            amp_sp_aux=self.scan_amp_729_sp_aux.sequence[i]
            num_try_save_ion = 0 

            delay(20*us)
            self.seq.ion_store.run()
            self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp,amp_sp_aux,self.amp_729_sp)   
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue
           
            for j in range(2):

                freq_729_dp=self.freq_729_dp1 if j==0 else self.freq_729_dp2
                att_729_dp=self.att_729_dp1 if j==0 else self.att_729_dp2
                sample_num=0

                while sample_num<self.samples_per_time:
                    if ion_status_detect==1 or ion_status_detect==2:
                        #line trigger
                        if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                            continue
                        
                        delay(50*us)

                        self.exp_seq(freq_729_dp, att_729_dp, ion_status_detect)
                        ################################################################################
                        ion_status=self.seq.cam_two_ions.cam_readout()
                        self.seq.ion_store.run()
                        delay(50*us)
                        ################################################################################
                        if ion_status==0: #if the ion is not bright then it's possible it's being kicked
                            # collision detection
                            self.seq.repump_854.run()
                            self.seq.doppler_cool.run()
                            ion_status_detect=self.seq.cam_two_ions.cam_readout() #by the way get the position
                            self.seq.ion_store.run()
                            delay(20*us)
                        else: 
                            ion_status_detect=ion_status

                        
                        if (ion_status_detect==ion_status_detect_last): #ion shouldn't move
                            sample_num+=1
                            # Update dataset
                            # self.experiment_data.insert_nd_dataset("pmt_counts",
                            #                             [i, sample_num],
                            #                             cam_input[0])
                            
                            if ion_status==0:
                                if j==0:
                                    total_thresh_count1 += 1
                                else:
                                    total_thresh_count2 +=1

                            #total_pmt_counts += cam_input[0]

                            delay(20*us)
                        elif (ion_status_detect==1 or ion_status_detect==2):
                            ion_status_detect_last=ion_status_detect
                            self.seq.ion_store.run()
                            delay(1*s)
                            self.seq.doppler_cool.run()
                            self.seq.ion_store.run()
                        
                        # print(ion_status_detect)
                        # delay(10*ms)

                    else:
                        self.seq.ion_store.run()
                        delay(1*s)
                        self.seq.doppler_cool.run()
                        ion_status_detect=self.seq.cam_two_ions.cam_readout()
                        self.seq.ion_store.run()

                        if ion_status_detect==1 or ion_status_detect==2:
                            num_try_save_ion = 0
                            ion_status_detect_last=ion_status_detect
                        else:
                            num_try_save_ion += 1
                        
                        if(num_try_save_ion>60):
                            print("Ion Lost!!!")
                            i=1000000
                            sample_num+=10000
                            break
                        delay(1*ms)


            self.experiment_data.append_list_dataset("amp_sp_aux", amp_sp_aux)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count1-total_thresh_count2) / self.samples_per_time)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)


        self.rf.set_voltage(0)
        self.core.break_realtime()

    def analyze(self):
        x=self.get_dataset("amp_sp_aux")
        y=self.get_dataset('pmt_counts_avg')
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

        with self.interactive("Rabi Frequency estimate for " + self.calibration_data) as inter:
            inter.setattr_argument(
                "sp_aux_amplitude",
                NumberValue(default=x_zero, min=-1.0, max=1.0, precision=8)
            )
            
        self.parameter_manager.set_param(
            self.calibration_data,
            inter.sp_aux_amplitude
        )
