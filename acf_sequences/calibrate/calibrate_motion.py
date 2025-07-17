from acf.sequence import Sequence

from artiq.experiment import *
from numpy import int32, int64
from acf.function.fitting import *
from awg_utils.transmitter import send_exp_para
import time

class Check_Motion(Sequence):

    def __init__(self):
        super().__init__()
      
    def build(self):

        self.setattr_argument("enable_calibration", 
                              BooleanValue(True),
            group="calibrate_motion",
            tooltip="enable_calibrate"
            )

        self.setattr_argument(
            "cal_num_points",
            NumberValue(default=40, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group="calibrate_motion"
        )
        self.setattr_argument(
            "cal_samples_per_freq",
            NumberValue(default=30, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group="calibrate_motion"
        )
        self.setattr_argument(
            "cal_freq_range",
            NumberValue(default=0.003*MHz, min=0*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="calibrate_motion"
        )
        self.setattr_argument(
            "cal_rabi_t",
            NumberValue(default=2000*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="calibrate_motion",
            tooltip="time_interogate_qubit"
        )
        self.setattr_argument(
            "cal_att_729_dp",
            NumberValue(default=30*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="calibrate_motion"
        )
        self.setattr_argument(
            "cal_amp_729_sp",
            NumberValue(default=0.009, min=0, max=1,  precision=8),
            tooltip="729 double pass attenuation",
            group="calibrate_motion"
        )
        self.setattr_argument(
            "cal_interval",
            NumberValue(default=400*s, min=0*s, max=1000*s, unit="s",precision=8),
            group="calibrate_motion",
            tooltip="frequency_interval"
        )
        self.cooling_option="sidebandcool_single_ion"
        self.last_time_calibrate=-5000*s
        self.freq_offset=self.get_freq_offset() # offset frequency between optical pumping and sideband cooling


    def prepare(self):
        
        # Create datasets
        self.num_samples = self.cal_num_points*2
        self.experiment_data.set_list_dataset("cal_motion_pos", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_motion_count", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_motion_freq", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('cal_motion_fit_signal', self.num_samples, broadcast=True)

        # shuffle the frequency arrays
        self.indices = [i for i in range(self.cal_num_points)]
        np.random.shuffle(self.indices)

        self.freq_729_RSB_sp=[0.0 for i in range(self.cal_num_points)]
        self.freq_729_BSB_sp=[0.0 for i in range(self.cal_num_points)]
        
    def get_sp_freq(self)->float:
        return self.exp.get_dataset('__param__frequency/729_sp', archive=False)
    def get_qubit_freq(self)->float:
        return self.exp.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_vib_freq1(self)->float:
        return self.exp.get_dataset('__param__VdP2mode/vib_freq1', archive=False)
    def get_vib_freq2(self)->float:
        return self.exp.get_dataset('__param__VdP2mode/vib_freq2', archive=False)
    def get_vib_freq0(self)->float:
        return self.exp.get_dataset('__param__VdP1mode/vib_freq', archive=False)
    def get_freq_offset(self)->float:
        return self.exp.get_dataset('__param__qubit/freq_offset', archive=False)

    @rpc
    def get_motional_freq_tracker(self, mode='mode1')->float:
        # mode1
        # mode2
        # mode_single_ion
        a=self.exp.get_dataset(f'__param__tracker/{mode}/a', archive=False)
        b=self.exp.get_dataset(f'__param__tracker/{mode}/b', archive=False)
        t=time.time()
        return a*t+b
    
    @kernel
    def check_interval(self) -> bool:
        if self.core.mu_to_seconds(now_mu())-self.last_time_calibrate>self.cal_interval and self.enable_calibration:
            self.last_time_calibrate=self.core.mu_to_seconds(now_mu())
            return True
        else:
            return False

    @kernel
    def cal_seq(self, rabi_t, wait_time, freq_729_dp, ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        #  Cool
        self.seq.doppler_cool.run()

        #sideband
        freq_diff_dp = self.exp.freq_diff_dp if ion_status_detect==2 else 0.0
        if self.cooling_option == "sidebandcool_single_ion":
            self.seq.sideband_cool.run(freq_diff_dp=freq_diff_dp)
        elif self.cooling_option == "sidebandcool":
            self.seq.sideband_cool.run(freq_offset=self.exp.freq_vib2, 
                                           att_729_here=self.exp.sideband_mode2_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.exp.sideband_mode2_att854) 
            self.seq.sideband_cool.run(freq_offset=self.exp.freq_vib1, 
                                           att_729_here=self.exp.sideband_mode1_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.exp.sideband_mode1_att854) 
            
        elif self.cooling_option == "sidebandcool2mode":
            self.seq.sideband_cool_2mode.run(freq_diff_dp=freq_diff_dp) 
        else:
            self.seq.op_pump.run(freq_diff_dp=freq_diff_dp) 
        delay(5*us)
        # rabi 
        self.cal_rabi_AWG(rabi_t, wait_time, freq_729_dp+freq_diff_dp)

    @kernel
    def cal_rabi_AWG(self,pulse_time, wait_time, freq_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(self.cal_att_729_dp)
        self.ttl_rf_switch_AWG_729SP.on()

        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        delay(wait_time)

        self.ttl_awg_trigger.pulse(1*us)
        if pulse_time>0.01*us:
            self.dds_729_dp.sw.on()
            delay(pulse_time)
            self.dds_729_dp.sw.off()
        delay(2*us)
        self.ttl_awg_trigger.pulse(1*us)

        # self.ttl_rf_switch_AWG_729SP.off()
        # self.ttl_rf_switch_DDS_729SP.on()

    @rpc(flags={'async'})
    def send_cal_para(self, freq_sp, cal_amp_729_sp):
        send_exp_para(["SingleTone",{"freq": freq_sp,"amp": cal_amp_729_sp, "num_loop":max(self.cal_samples_per_freq+100,100)}])

    @kernel
    def calibrate_freq_motion(self, 
                             cal_amp_729_sp=-1.0,
                             cal_freq_range=-1.0*MHz,
                             vib_mode="mode_single_ion", 
                             wait_time=10*us,
                             cooling_option="optical_pumping",
                             use_motion_tracking=False
                             )->np.int32:

        self.cooling_option=cooling_option
        freq_729_dp=self.exp.seq.adjust_729_freq.get_qubit_freq_tracker()-self.freq_offset*0.5

        #self.get_qubit_freq()+0.000*MHz
        freq_sp=self.get_sp_freq()
        vib_freq=0.54*MHz

        if use_motion_tracking:
            vib_freq=self.get_motional_freq_tracker(mode=vib_mode)
        else:
            if vib_mode=="mode_single_ion":
                vib_freq=self.get_vib_freq0()
            elif vib_mode=="mode1":
                vib_freq=self.get_vib_freq1()
            elif vib_mode=="mode2":
                vib_freq=self.get_vib_freq2()

        cal_amp_729_sp_here=self.cal_amp_729_sp
        if cal_amp_729_sp>0.0:
            cal_amp_729_sp_here=cal_amp_729_sp
        else:
            if vib_mode=="mode_single_ion":
                cal_amp_729_sp_here=self.cal_amp_729_sp
            elif vib_mode=="mode1":
                cal_amp_729_sp_here=self.cal_amp_729_sp*0.134/0.094
            elif vib_mode=="mode2":
                cal_amp_729_sp_here=self.cal_amp_729_sp*0.134/0.0716*1.5
                
        if cal_freq_range>0.0:
            self.cal_freq_range=cal_freq_range
        
        for i in range(self.cal_num_points):
            self.freq_729_RSB_sp[i]=freq_sp+vib_freq-self.cal_freq_range + i*(2*self.cal_freq_range)/(self.cal_num_points-1)
        for i in range(self.cal_num_points):
            self.freq_729_BSB_sp[i]=freq_sp-vib_freq-self.cal_freq_range + i*(2*self.cal_freq_range)/(self.cal_num_points-1)

        self.core.break_realtime()

        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1

        #detecting the initial position of the ion 
        # while ion_status_detect_last!=1 and ion_status_detect_last!=2:
        #     delay(2*ms)
        #     self.seq.repump_854.run()
        #     self.seq.doppler_cool.run()
        #     delay(5*us)
        #     ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
        #     self.seq.ion_store.run()
        #     delay(1*ms)
        
        if(ion_status_detect_last==3): 
            i=self.cal_num_points*2
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last
        
        self.core.break_realtime()
        i=0
        while i < self.cal_num_points*2:

            total_thresh_count = 0
            sample_num=0

            j=i//2
            if i%2==0:
                freq_729_sp =self.freq_729_RSB_sp[self.indices[j]]
            else:
                freq_729_sp =self.freq_729_BSB_sp[self.indices[j]]


            self.core.break_realtime()
            self.seq.ion_store.run()
            
           
            num_try_save_ion = 0 
            self.send_cal_para(freq_729_sp, cal_amp_729_sp_here)   
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG check motion!!!!")
                continue

            while sample_num<self.cal_samples_per_freq:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(6.5*ms)
                    delay(50*us)

                    self.cal_seq(self.cal_rabi_t, wait_time, freq_729_dp, ion_status_detect)
                  
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

                      
                    if (ion_status_detect==ion_status_detect_last  and ion_status_detect==1): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [i, sample_num],
                        #                             cam_input[0])
                        
                        if ion_status==0:
                            total_thresh_count += 1

                        #total_pmt_counts += cam_input[0]

                        self.core.break_realtime()
                    elif ion_status_detect==ion_status_detect_last and ion_status_detect==2: 
                        self.seq.rf.tickle()
                    elif (ion_status_detect==1 or ion_status_detect==2):
                        ion_status_detect_last=ion_status_detect
                        self.seq.ion_store.run()
                        delay(0.5*s)
                    
                    # print(ion_status_detect)
                    # delay(10*ms)

                else:
                    self.seq.ion_store.run()
                    self.seq.rf.save_ion()
                    self.seq.doppler_cool.run()
                    ion_status_detect=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()

                    if ion_status_detect==1 or ion_status_detect==2:
                        num_try_save_ion = 0
                        ion_status_detect_last=ion_status_detect
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>6000):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break
                    delay(1*ms)

            if i%2==0:
                self.experiment_data.insert_nd_dataset("cal_motion_freq", self.cal_num_points+self.indices[j], freq_729_sp/MHz)
                self.experiment_data.insert_nd_dataset("cal_motion_pos", self.cal_num_points+self.indices[j], 2)
                self.experiment_data.insert_nd_dataset("cal_motion_count", self.cal_num_points+self.indices[j], float(total_thresh_count) / self.cal_samples_per_freq)
            else:
                self.experiment_data.insert_nd_dataset("cal_motion_freq", self.indices[j], (freq_sp*2-freq_729_sp)/MHz)
                self.experiment_data.insert_nd_dataset("cal_motion_pos", self.indices[j], 1)
                self.experiment_data.insert_nd_dataset("cal_motion_count", self.indices[j], float(total_thresh_count) / self.cal_samples_per_freq)
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.freq_offset+=self.update_motion_freq(vib_mode)
        self.last_time_calibrate=self.core.mu_to_seconds(now_mu())
        self.core.break_realtime()

        return ion_status_detect_last

    @rpc
    def update_motion_freq(self, vib_mode)->float:
        freq=self.exp.get_dataset("cal_motion_freq")
        PMT_count=self.exp.get_dataset('cal_motion_count')

        # Calculate the average PMT count for each frequency
        try:
            success1, fitted_curve1, peak1, peak_error1 = find_peak_lorentzian_with_error(freq[:self.cal_num_points], PMT_count[:self.cal_num_points])
            success2, fitted_curve2, peak2, peak_error2 = find_peak_lorentzian_with_error(freq[self.cal_num_points:], PMT_count[self.cal_num_points:])

            if success1 and success2:

                self.exp.set_dataset('cal_motion_fit_signal', np.concatenate((fitted_curve1, fitted_curve2)), broadcast=True)
                freq_sp=self.get_sp_freq()

                freq_offset=(peak1*MHz-peak2*MHz)/2.0
                peak1=freq_sp*2-peak1*MHz #BSB
                peak2=peak2*MHz #RSB       
                peak_error=np.sqrt(peak_error1**2+peak_error2**2)*MHz

                if peak_error>0.0005*MHz:
                    print("Peak error is too large, skipping calibration")
                    return 0.0

                freq_vib=0.0*MHz
                if vib_mode=="mode_single_ion":
                    freq_vib=self.get_vib_freq0()
                elif vib_mode=="mode1":
                    freq_vib=self.get_vib_freq1()
                elif vib_mode=="mode2":
                    freq_vib=self.get_vib_freq2()

                drop_out=0.5*0

                new_freq_vib=(peak2-peak1)/2.0*(1.0-drop_out)+freq_vib*drop_out

                print("Finished Calibration of ", vib_mode, " from old frequency: ", freq_vib, " to new frequency: ", new_freq_vib)
                print("Frequency offset: ", self.freq_offset)

                self.exp.parameter_manager.set_param(
                    "qubit/freq_offset",
                    self.freq_offset,
                    "MHz"
                )

                if vib_mode=="mode_single_ion":
                    self.exp.parameter_manager.set_param(
                        "VdP1mode/vib_freq_var",
                        peak_error,
                        "MHz"
                    )
                    self.exp.parameter_manager.set_param(
                        "VdP1mode/vib_freq",
                        new_freq_vib,
                        "MHz"
                    )
                elif vib_mode=="mode1":
                    self.exp.parameter_manager.set_param(
                        "VdP2mode/vib_freq1_var",
                        peak_error,
                        "MHz"
                    )
                    self.exp.parameter_manager.set_param(
                        "VdP2mode/vib_freq1",
                        new_freq_vib,
                        "MHz"       
                    )
                elif vib_mode=="mode2":
                    self.exp.parameter_manager.set_param(
                        "VdP2mode/vib_freq2_var",
                        peak_error,
                        "MHz"
                    )
                    self.exp.parameter_manager.set_param(
                        "VdP2mode/vib_freq2",
                        new_freq_vib,
                        "MHz"
                    )
                return freq_offset
            else:
                print("Failed to find peak")
                return 0.0
        except:
            print("Failed to find peak")
            return 0.0


        

       
