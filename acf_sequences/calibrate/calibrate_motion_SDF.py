from acf.sequence import Sequence

from artiq.experiment import *
from numpy import int32, int64
from acf.function.fitting import *
from awg_utils.transmitter import send_exp_para
import time

class Check_Motion_SDF(Sequence):

    def __init__(self):
        super().__init__()
      
    def build(self):

        self.setattr_argument("enable_calibration", 
                              BooleanValue(True),
            group="calibrate_motion_SDF",
            tooltip="enable_calibrate"
            )

        self.setattr_argument(
            "cal_num_points",
            NumberValue(default=30, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group="calibrate_motion_SDF"
        )
        self.setattr_argument(
            "cal_samples_per_freq",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group="calibrate_motion_SDF"
        )
        self.setattr_argument(
            "cal_freq_range",
            NumberValue(default=0.0005*MHz, min=0*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="calibrate_motion_SDF"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=29.0*dB, min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group='calibrate_motion_SDF'
        )
        self.setattr_argument(
            "cal_rabi_t",
            NumberValue(default=500*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="calibrate_motion_SDF",
            tooltip="time_interogate_qubit"
        )
        self.setattr_argument(
            "cal_interval",
            NumberValue(default=400*s, min=0*s, max=1000*s, unit="s",precision=8),
            group="calibrate_motion_SDF",
            tooltip="frequency_interval"
        )
        self.cooling_option="sidebandcool_single_ion"
        self.last_time_calibrate=-5000*s
        


    def prepare(self):
        
        # Create datasets
        self.num_samples = self.cal_num_points
        self.experiment_data.set_list_dataset("cal_motion_SDF_pos", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_motion_SDF_count", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_motion_SDF_freq", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('cal_motion_SDF_fit_signal', self.num_samples, broadcast=True)

        # shuffle the frequency arrays
        self.indices = [i for i in range(self.cal_num_points)]
        np.random.shuffle(self.indices)

        self.freq_delta_m=[0.0 for i in range(self.cal_num_points)]
        
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


    @kernel
    def check_interval(self) -> bool:
        if self.core.mu_to_seconds(now_mu())-self.last_time_calibrate>self.cal_interval and self.enable_calibration:
            self.last_time_calibrate=self.core.mu_to_seconds(now_mu())
            return True
        else:
            return False

    @kernel
    def cal_seq(self, rabi_t, vib_mode, freq_729_dp, ion_status_detect):
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
        self.cal_rabi_AWG(rabi_t, vib_mode, freq_729_dp+freq_diff_dp)

    @kernel
    def cal_rabi_AWG(self, pulse_time, vib_mode , freq_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        
        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()

        delay(2*us) 
        if vib_mode=="mode1":  
            for _ in range(2):
                self.seq.sdf_mode1.run(pulse_time, att_729_dp=self.att_729_dp)
        elif vib_mode=="mode2":
            for _ in range(2):
                self.seq.sdf_mode2.run(pulse_time*1.5, att_729_dp=self.att_729_dp)
        else:
            for _ in range(2):
                self.seq.sdf_single_ion.run(pulse_time, att_729_dp=self.att_729_dp)

        #turn off
        self.ttl_awg_trigger.pulse(1*us)

    @rpc(flags={'async'})
    def send_cal_para(
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

                "if_x_Rot": 0,
                "freq_sp":  80.0*MHz,
                "amp_sp":0.0,
                "num_loop":max(self.cal_samples_per_freq+100,200)
            }])  

    @kernel
    def calibrate_freq_motion(self, 
                             cal_freq_range=-1.0*MHz,
                             vib_mode="mode_single_ion", 
                             cooling_option="optical_pumping"
                             )->np.int32:

        self.cooling_option=cooling_option
        freq_729_dp=self.exp.seq.adjust_729_freq.get_qubit_freq_tracker()

        if cal_freq_range>0.0:
            self.cal_freq_range=cal_freq_range
        
        for i in range(self.cal_num_points):
            self.freq_delta_m[i]=-self.cal_freq_range + i*(2*self.cal_freq_range)/(self.cal_num_points-1)

       
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
            i=self.cal_num_points
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last
        
        if vib_mode=="mode1":
            self.seq.sdf_mode1.prepare()
        elif vib_mode=="mode2":
            self.seq.sdf_mode2.prepare()
        elif vib_mode=="mode_single_ion":
            self.seq.sdf_single_ion.prepare()

        i=0
        while i < self.cal_num_points:

            total_thresh_count = 0
            sample_num=0
            num_try_save_ion = 0 
            freq_delta_m=self.freq_delta_m[self.indices[i]]
            self.core.break_realtime()
            self.seq.ion_store.run()
            
            

            if vib_mode=="mode1":
                
                self.send_cal_para(
                    self.seq.sdf_mode1.freq_729_sp_aux+freq_delta_m,
                    self.seq.sdf_mode1.freq_729_sp-freq_delta_m,
                    self.seq.sdf_mode1.amp_729_sp_aux,
                    self.seq.sdf_mode1.amp_729_sp
                ) 
            elif vib_mode=="mode2":
                self.send_cal_para(
                    self.seq.sdf_mode2.freq_729_sp_aux+freq_delta_m,
                    self.seq.sdf_mode2.freq_729_sp-freq_delta_m,
                    self.seq.sdf_mode2.amp_729_sp_aux,
                    self.seq.sdf_mode2.amp_729_sp
                )
            elif vib_mode=="mode_single_ion":
                self.send_cal_para(
                    self.seq.sdf_single_ion.freq_729_sp_aux+freq_delta_m,
                    self.seq.sdf_single_ion.freq_729_sp-freq_delta_m,
                    self.seq.sdf_single_ion.amp_729_sp_aux,
                    self.seq.sdf_single_ion.amp_729_sp
                )
            self.core.break_realtime()

            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue

            while sample_num<self.cal_samples_per_freq:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.cal_seq(self.cal_rabi_t, vib_mode, freq_729_dp, ion_status_detect)
                  
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
                        
                        if ion_status==0:
                            total_thresh_count += 1

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

            
            self.experiment_data.insert_nd_dataset("cal_motion_SDF_freq", self.indices[i], freq_delta_m/MHz)
            self.experiment_data.insert_nd_dataset("cal_motion_SDF_pos", self.indices[i], 1)
            self.experiment_data.insert_nd_dataset("cal_motion_SDF_count", self.indices[i], float(total_thresh_count) / self.cal_samples_per_freq)
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.update_motion_freq(vib_mode)
        self.last_time_calibrate=self.core.mu_to_seconds(now_mu())
        self.core.break_realtime()

        return ion_status_detect_last

    @rpc
    def update_motion_freq(self, vib_mode):
        freq=self.exp.get_dataset("cal_motion_SDF_freq")
        PMT_count=self.exp.get_dataset('cal_motion_SDF_count')

        # Calculate the average PMT count for each frequency
        try:
            success1, fitted_curve1, peak1, peak_error1 = find_peak_gaussian_with_error(freq, -PMT_count)

            #print(PMT_count)

            if success1:

                self.exp.set_dataset('cal_motion_SDF_fit_signal', -fitted_curve1, broadcast=True)


                peak1=peak1*MHz #BSB
                peak_error=np.sqrt(peak_error1**2)*MHz

                if peak_error>0.0005*MHz:
                    print("Peak error is too large, skipping calibration")
                    return

                freq_vib=0.0*MHz
                if vib_mode=="mode_single_ion":
                    freq_vib=self.get_vib_freq0()
                elif vib_mode=="mode1":
                    freq_vib=self.get_vib_freq1()
                elif vib_mode=="mode2":
                    freq_vib=self.get_vib_freq2()

                drop_out=0.0

                new_freq_vib=freq_vib+peak1*drop_out

                print("Finished Calibration of ", vib_mode, " from old frequency: ", freq_vib, " to new frequency: ", new_freq_vib)

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

        except:
            print("Failed to find peak")
            #return 0.0


        

       
