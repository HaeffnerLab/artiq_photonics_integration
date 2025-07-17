from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import stark_shift_SDF_kernel

class A6_Displacement_Time(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        #self.seq.vdp2mode.build()

        self.setup_fit(fitting_func, 'Sin' ,-1)
        self.seq.cam_two_ions.build()

        self.seq.sdf_mode1.build()
        self.seq.sdf_mode2.build()
        self.seq.sdf_single_ion.build()

        
        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=500*us,
                    npoints=30
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("vib_mode", EnumerationValue(["mode1","mode2","mode_single_ion"], default="mode1"))
        self.setattr_argument(
            "freq_delta_m",
            NumberValue(default=0.005*MHz, min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )


        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool2mode", "opticalpumping", "sidebandcool_single_ion"], default="sidebandcool2mode"))
        
        self.setattr_argument("power_calibration", 
                              EnumerationValue(["SDF/mode1/Rabi_Freq", 
                                                "SDF/mode2/Rabi_Freq",
                                                "SDF/mode_single_ion/Rabi_Freq"
                                                ], default="SDF/mode2/Rabi_Freq"))

        
        self.freq_vib1=self.get_vib_freq1()
        self.freq_vib2=self.get_vib_freq2()
        self.sideband_mode1_att729=self.parameter_manager.get_float_param('sideband2mode/mode1_att_729')
        self.sideband_mode1_att854=self.parameter_manager.get_float_param('sideband2mode/mode1_att_854')
        self.sideband_mode2_att729=self.parameter_manager.get_float_param('sideband2mode/mode2_att_729')
        self.sideband_mode2_att854=self.parameter_manager.get_float_param('sideband2mode/mode2_att_854')

    def get_qubit_freq(self)->float:
        return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_vib_freq1(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq1', archive=False)
    def get_vib_freq2(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq2', archive=False)
    def prepare(self):
        self.fitting_func.setup(len(self.scan_rabi_t.sequence))
        # Create datasets
        num_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
            fit_data_name='fit_signal',
            pos_data_name="pos"
        )



    @kernel
    def rabi_AWG(self,pulse_time, freq_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()

        if self.vib_mode=="mode1":
            self.seq.sdf_mode1.run(pulse_time)
        elif self.vib_mode=="mode2":
            self.seq.sdf_mode2.run(pulse_time)
        else:
            self.seq.sdf_single_ion.run(pulse_time)

        self.ttl_awg_trigger.pulse(1*us)

        
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @kernel
    def exp_seq(self, rabi_t, ion_status_detect):
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
        self.rabi_AWG(rabi_t, self.freq_729_dp+freq_diff_dp)


    @rpc(flags={'async'})
    def send_exp_para(
        self,
        phase=0.0 
    ):
        if self.vib_mode=="mode1":
            send_exp_para(["Displacement_SDF", {
                "freq_sp_RSB":   self.seq.sdf_mode1.freq_729_sp+self.freq_delta_m,
                "freq_sp_BSB":   self.seq.sdf_mode1.freq_729_sp_aux-self.freq_delta_m,
                "amp_sp_RSB":  self.seq.sdf_mode1.amp_729_sp,
                "amp_sp_BSB":   self.seq.sdf_mode1.amp_729_sp_aux,
                "phase": phase,
                "num_loop":max(self.samples_per_time+100,400)
            }])  
        elif self.vib_mode=="mode2":
            send_exp_para(["Displacement_SDF", {
                "freq_sp_RSB":   self.seq.sdf_mode2.freq_729_sp+self.freq_delta_m,
                "freq_sp_BSB":   self.seq.sdf_mode2.freq_729_sp_aux-self.freq_delta_m,
                "amp_sp_RSB":  self.seq.sdf_mode2.amp_729_sp,
                "amp_sp_BSB":   self.seq.sdf_mode2.amp_729_sp_aux,
                "phase": phase,
                "num_loop":max(self.samples_per_time+100,400)
            }])   
        else:
            send_exp_para(["Displacement_SDF", {
                "freq_sp_RSB":   self.seq.sdf_single_ion.freq_729_sp+self.freq_delta_m,
                "freq_sp_BSB":   self.seq.sdf_single_ion.freq_729_sp_aux-self.freq_delta_m,
                "amp_sp_RSB":  self.seq.sdf_single_ion.amp_729_sp,
                "amp_sp_BSB":   self.seq.sdf_single_ion.amp_729_sp_aux,    
                "phase": phase,
                "num_loop":max(self.samples_per_time+100,400)
            }])   
        
        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        self.seq.cam_two_ions.cam_setup()

        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1
        num_try_save_ion = 0 

        # #detecting the initial position of the ion 
        # while ion_status_detect_last!=1 and ion_status_detect_last!=2:
        #     delay(2*ms)
        #     self.seq.repump_854.run()
        #     self.seq.doppler_cool.run()
        #     delay(5*us)
        #     ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
        #     self.seq.ion_store.run()
        #     delay(1*ms)
        
        if(ion_status_detect_last==3): 
            i=len(self.scan_rabi_t.sequence)
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        i=0
        while i < len(self.scan_rabi_t.sequence):

            total_thresh_count = 0
            sample_num=0
            rabi_t=self.scan_rabi_t.sequence[i]


            delay(20*us)
            self.seq.ion_store.run()
            

            self.send_exp_para(0.0)
            num_try_save_ion = 0 

            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(55*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue
            
            

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(rabi_t, ion_status_detect)
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

                      
                    if (ion_status_detect==ion_status_detect_last and ion_status_detect==1):# and (ion_status_detect==1 or ion_status_detect==2) and (ion_status!=3)): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [i, sample_num],
                        #                             cam_input[0])
                        
                        total_thresh_count += 1 if ion_status==0 else 0

                        #total_pmt_counts += cam_input[0]

                        self.core.break_realtime()
                    elif ion_status_detect==ion_status_detect_last and ion_status_detect==2: 
                        self.seq.rf.tickle()
                    elif (ion_status_detect==1 or ion_status_detect==2):
                        ion_status_detect_last=ion_status_detect
                        self.seq.ion_store.run()
                        delay(0.5*s)

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
                    
                    if(num_try_save_ion>60):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break
                    delay(100*ms)


            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                        float(total_thresh_count) / self.samples_per_time)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)

    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        try:
            params=self.fitting_func.fit(rabi_time, rabi_PMT)

            fitted_amplitude, fitted_omega, fitted_phase, fitted_tau, fitted_offset = params

            fitted_frequency = fitted_omega / (2 * np.pi)

            with self.interactive("Rabi Frequency estimate for " + self.power_calibration) as inter:
                inter.setattr_argument(
                    "rabi_freq",
                    NumberValue(default=fitted_frequency*MHz, unit="MHz", min=-5*MHz, max=240*MHz, precision=8)
                )
            
            self.parameter_manager.set_param(
                self.power_calibration,
                inter.rabi_freq,
                "MHz"
            )
            
        except Exception:
            pass