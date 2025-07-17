from acf.sequence import Sequence

from artiq.experiment import *
from numpy import int32, int64
from acf.function.fitting import *
from awg_utils.transmitter import send_exp_para
import time
class Check_729_Freq_Ramsey(Sequence):

    def __init__(self):
        super().__init__()

    def prepare(self):
        pass

    def build(self):

        self.setattr_argument("enable_calibration", 
                              BooleanValue(True),
            group="calibrate_qubit_Ramsey",
            tooltip="enable_calibrate"
            )

        self.setattr_argument(
            "cal_num_samples",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group="calibrate_qubit_Ramsey"  
        )

        self.setattr_argument(
            "cal_pi_time",
            NumberValue(default=self.parameter_manager.get_param("pi_time/AWG_pi_time"), min=0*us, max=5*ms, unit="us",precision=8),
            group="calibrate_qubit_Ramsey",
            tooltip="time_interogate_qubit"
        )
        self.setattr_argument(
            "cal_pi_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("pi_time/att_729_dp"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="calibrate_qubit_Ramsey"
        )
        self.setattr_argument(
            "cal_pi_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="calibrate_qubit_Ramsey"
        )
        self.setattr_argument(
            "cal_pi_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("pi_time/AWG_amp_729_sp"), min=0, max=1,  precision=8),
            tooltip="729 single pass amplitude",  
            group="calibrate_qubit_Ramsey"
        )
        self.setattr_argument(
            "cal_interval",
            NumberValue(default=100*s, min=0*s, max=500*s, unit="s",precision=8),
            group="calibrate_qubit_Ramsey",
            tooltip="frequency_interval"
        )
        self.cooling_option="sidebandcool_single_ion"
        self.line="Sm1_2_Dm5_2"
        self.last_time_calibrate=-5000*s
        self.T=[300*us, 500*us, 700*us]

    @kernel
    def check_interval(self) -> bool:
        if self.core.mu_to_seconds(now_mu())-self.last_time_calibrate>self.cal_interval and self.enable_calibration:
            self.last_time_calibrate=self.core.mu_to_seconds(now_mu())
            return True
        else:
            return False

    @kernel
    def cal_seq(self, wait_time,  freq_729_dp, ion_status_detect):
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
        self.cal_rabi_AWG(wait_time, freq_729_dp+freq_diff_dp)

    @kernel
    def cal_rabi_AWG(self, wait_time,  freq_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(self.cal_pi_att_729_dp)

        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        delay(10*us)

        #Pulse 1 
        self.ttl_awg_trigger.pulse(1*us)
        self.dds_729_dp.sw.on()
        delay(self.cal_pi_time/2.0)
        self.dds_729_dp.sw.off()

        #Ramsey wait time
        delay(wait_time)

        #Pulse 2
        self.ttl_awg_trigger.pulse(1*us)
        self.dds_729_dp.sw.on()
        delay(self.cal_pi_time/2.0)
        self.dds_729_dp.sw.off()

        #turn off the single pass
        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()

    @rpc(flags={'async'})
    def send_cal_para(self, phase1, phase2):
        send_exp_para(["Ramsey",
                       {"freq": self.cal_pi_freq_729_sp,
                        "amp": self.cal_pi_amp_729_sp, 
                        "phase1":phase1,
                        "phase2":phase2,
                        "num_loop":max(self.cal_num_samples+100,100)
                        }
                        ]
                        )

    def get_qubit_freq(self)->float:
        return self.exp.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
        
    @kernel
    def calibrate_freq_qubit(self, 
                             line="Sm1_2_Dm5_2", 
                             cooling_option="sidebandcool2mode"
                             )->np.int32:

        self.cooling_option=cooling_option
        self.line=line
        self.core.break_realtime()
        
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
            i=100000
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        i=0
        freq_729_dp_here = self.get_qubit_freq()
        self.core.break_realtime()
        while i < len(self.T):

            num_try_save_ion = 0 

            # the wait time and frequency of the qubit
            wait_time=self.T[i]
            
            ##############################################################################################################
            delay(20*us)
            self.seq.ion_store.run()
            
            res=[0.0,0.0]
           
            for iter in range(2):
                
                if iter==0:
                    self.send_cal_para(180, 0) 
                else:
                    self.send_cal_para(0, 180) 

                if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    print("BAD AWG!!!!")
                    continue

                # Reset counters for each phase
                total_thresh_count = 0
                sample_num = 0

                while sample_num<self.cal_num_samples:
                    if ion_status_detect==1 or ion_status_detect==2:
                        #line trigger
                        if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                            continue
                        
                        delay(50*us)

                        self.cal_seq(wait_time, freq_729_dp_here, ion_status_detect)
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

                        
                        if (ion_status_detect==ion_status_detect_last and ion_status_detect==1): #ion shouldn't move
                            sample_num+=1
                            # Update dataset
                            # self.experiment_data.insert_nd_dataset("pmt_counts",
                            #                             [i, sample_num],
                            #                             cam_input[0])
                            
                            if ion_status==0:
                                total_thresh_count += 1

                            self.core.break_realtime()
                        elif ion_status_detect==ion_status_detect_last and ion_status_detect==2: 
                            self.seq.rf.tickle()
                        elif (ion_status_detect==1 or ion_status_detect==2):
                            ion_status_detect_last=ion_status_detect
                            self.seq.ion_store.run()
                            delay(1*s)
                            self.seq.doppler_cool.run()
                            self.seq.ion_store.run()
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
                        delay(10*ms)

                res[iter]=float(total_thresh_count) / self.cal_num_samples

            # Calculate frequency correction
            delta_freq=(res[0]-res[1])/2.0/wait_time  # Frequency shift in MHz

            # Apply correction
            freq_729_dp_here=freq_729_dp_here+delta_freq/2.0  #double pass

            print(delta_freq*1000)
            self.core.break_realtime()
            
            # Move to next wait time
            i += 1

        self.seq.ion_store.run()

        self.update_729_freq(freq_729_dp_here)
        self.core.break_realtime()

        return ion_status_detect_last
        
    @rpc
    def get_qubit_freq_tracker(self)->float:
        a=self.exp.get_dataset('__param__tracker/qubit/a', archive=False)
        b=self.exp.get_dataset('__param__tracker/qubit/b', archive=False)
        c=self.exp.get_dataset('__param__tracker/qubit/c', archive=False)
        t=time.time()
        return a*t**2+b*t+c
    
    @rpc
    def update_729_freq(self, new_freq):
        freq_729_dp=self.get_qubit_freq()

        #update frequency of 729 
        if np.abs(new_freq-freq_729_dp)<2*kHz:
            self.exp.parameter_manager.set_param(
                "qubit/Sm1_2_Dm5_2",
                new_freq,
                "MHz"
            )
