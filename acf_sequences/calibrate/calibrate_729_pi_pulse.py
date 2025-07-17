from acf.sequence import Sequence

from artiq.experiment import *
from numpy import int32, int64
from acf.function.fitting import *
from awg_utils.transmitter import send_exp_para
import time

class Check_729_Pi_Pulse(Sequence):

    def __init__(self):
        super().__init__()

    def prepare(self):
        self.experiment_data.set_list_dataset('cal_pi_pulse_fit_signal', self.cal_num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_pi_pulse_count", self.cal_num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_pi_pulse_time", self.cal_num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_pi_pulse_pos", self.cal_num_samples, broadcast=True)

    def build(self):
        self.setattr_argument("enable_calibration", 
                              BooleanValue(True),
            group="qubit_calibrate_pi_time",
            tooltip="Enable pi time calibration"
            )

        self.setattr_argument(
            "cal_num_samples",
            NumberValue(default=30, precision=0, step=1),
            tooltip="Number of time points to scan",
            group="qubit_calibrate_pi_time"
        )
        self.setattr_argument(
            "cal_num_samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of measurements per time point",
            group="qubit_calibrate_pi_time"
        )
        self.setattr_argument(
            "cal_rabi_t",
            NumberValue(default=self.exp.parameter_manager.get_param("pi_time/AWG_pi_time")*4, min=0.1*us, max=100*us, unit="us",precision=8),
            group="qubit_calibrate_pi_time",
            tooltip="Maximum Rabi time to scan"
        )
        self.setattr_argument(
            "cal_att_729_dp",
            NumberValue(default=self.exp.parameter_manager.get_param("pi_time/att_729_dp"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="qubit_calibrate_pi_time"
        )
        self.setattr_argument(
            "cal_freq_729_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 single pass frequency",
            group="qubit_calibrate_pi_time"
        )
        self.setattr_argument(
            "cal_amp_729_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("pi_time/AWG_amp_729_sp"), min=0, max=1,  precision=8),
            tooltip="729 single pass amplitude",
            group="qubit_calibrate_pi_time"
        )
        self.setattr_argument(
            "cal_interval",
            NumberValue(default=1800*s, min=0*s, max=500*s, unit="s",precision=8),
            group="qubit_calibrate_pi_time",
            tooltip="Time interval between calibrations"
        )
        self.cooling_option="sidebandcool_single_ion"
        self.line="Sm1_2_Dm5_2"
        self.last_time_calibrate=-5000*s

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
        self.cal_rabi_AWG(rabi_t, wait_time, freq_729_dp+freq_diff_dp, self.cal_att_729_dp)

    @kernel
    def cal_rabi_AWG(self,pulse_time, wait_time, freq_729_dp, att_729_dp):
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)

        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        delay(wait_time)

        self.ttl_awg_trigger.pulse(1*us)
        if pulse_time>0.01*us:
            self.dds_729_dp.sw.on()
            delay(pulse_time)
            self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)

        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @rpc(flags={'async'})
    def send_cal_para(self):
        send_exp_para(["SingleTone",{"freq": self.cal_freq_729_sp,"amp": self.cal_amp_729_sp, "num_loop":max(self.cal_num_samples_per_time+100,100)}])

    def get_qubit_freq(self)->float:
        return self.exp.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)

    def get_pi_pulse_time(self)->float:
        return self.exp.get_dataset("__param__pi_time/AWG_pi_time", archive=False)

    @kernel
    def calibrate_pi_time(self, 
                         line="Sm1_2_Dm5_2", 
                         wait_time=50*us,
                         cooling_option="sidebandcool2mode"
                         )->np.int32:

        self.cooling_option=cooling_option
        self.line=line
        
        freq_729_dp=self.get_qubit_freq()
      
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
            i=100000
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        # Scan different Rabi times
        self.core.break_realtime()
        
        i=0
        while i < self.cal_num_samples:

            total_thresh_count = 0
            sample_num=0

            rabi_t=self.cal_rabi_t*i/(self.cal_num_samples-1)

            freq_729_dp_here = freq_729_dp
            num_try_save_ion = 0 
            self.core.break_realtime()
            delay(20*us)
            self.seq.ion_store.run()
            self.send_cal_para()   
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG check pi pulse!!!!")
                continue

            while sample_num<self.cal_num_samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.cal_seq(rabi_t, wait_time, freq_729_dp_here, ion_status_detect)
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

            self.experiment_data.insert_nd_dataset("cal_pi_pulse_time", i, rabi_t/us)
            self.experiment_data.insert_nd_dataset("cal_pi_pulse_count", i, 
                                        float(total_thresh_count) / self.cal_num_samples_per_time)
            self.experiment_data.insert_nd_dataset("cal_pi_pulse_pos", i, ion_status_detect)

            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.update_pi_time()
        self.core.break_realtime()

        return ion_status_detect_last

    @rpc
    def update_pi_time(self):
        times = self.exp.get_dataset("cal_pi_pulse_time")
        PMT_count = self.exp.get_dataset('cal_pi_pulse_count')

        # Check if there are too many zero values
        zero_count = np.sum(PMT_count == 0)
        if zero_count > 8:
            print("Too many zero values in data, skipping pi time update")
            return

        try:
            # Fit with a sinusoidal function
            def sin_func(x, a, b, c, d):
                return a * np.sin(2*np.pi*b*x + c) + d
            
            old_pi_time=self.exp.parameter_manager.get_param("pi_time/AWG_pi_time")

            from scipy.optimize import curve_fit
            popt, pcov = curve_fit(sin_func, times, PMT_count, 
                                 p0=[0.5, 1/(2*old_pi_time/us), 0, 0.5])

            # Calculate pi time (time for first maximum)
            a, b, c, d = popt
            pi_time = (np.pi/2 - c)/(2*np.pi*b) * us

            # Generate fitted curve
            fitted_times = np.array([self.cal_rabi_t*i/(self.cal_num_samples-1)/us for i in range(self.cal_num_samples)])
            fitted_curve = sin_func(fitted_times, *popt)

            # Update datasets
            self.exp.set_dataset('cal_pi_pulse_fit_signal', fitted_curve, broadcast=True)

            print("Finished Pi Time Calibration: ", pi_time/us, " us")

            if pi_time<0.01*us or np.abs(pi_time-old_pi_time)>5*us:
                print("Pi Time Calibration Failed: ", pi_time/us, " us")
                return
            
            # Update the pi time parameter
            self.exp.parameter_manager.set_param(
                "pi_time/AWG_pi_time",
                pi_time,
                "us"
            )

        except Exception as e:
            print("Failed to fit pi time:", str(e))
            return

        

       
