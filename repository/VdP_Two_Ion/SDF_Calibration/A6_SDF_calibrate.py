from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import stark_shift_SDF_kernel

class A6_SDF_calibrate_AWG_Cam(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        
        self.setup_fit(fitting_func ,'Lorentzian', -999)

        self.seq.cam_two_ions.build()

        #double pass part & SDF #######################################################################################################################################
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
       

        ###########################################################################################################################################################################################################
        self.setattr_argument(
            "rot_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")
                        , min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group = "pi/2 rotation"
        )
        self.setattr_argument(
            "rot_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("pi_time/att_729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
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
            NumberValue(default=self.parameter_manager.get_param("pi_time/AWG_amp_729_sp"), min=1e-4, max=0.8, precision=8),
            tooltip="729 single pass amplitude",
            group = "pi/2 rotation"
        )
        self.setattr_argument(
            "rot_time",
            NumberValue(default=self.parameter_manager.get_param("pi_time/AWG_pi_time")/2.0, min=0.*us, max=100*us, unit='us', precision=8),
            tooltip="Ramsey pulse time if don't scan this dimension",
            group = "pi/2 rotation"
        )   
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool2mode", "opticalpumping", "sidebandcool_single_ion"], default="sidebandcool2mode"))
        

        ###################################################################################################################################################################################
        self.setattr_argument("Scan_Type", EnumerationValue(['Delta_s', 'Delta_m'], default= 'Delta_s'))
        self.setattr_argument("vib_mode", EnumerationValue(["mode1","mode2","mode_single_ion"], default="mode1"))
        self.setattr_argument(
            "scan_freq",
            Scannable(
                default=RangeScan(
                    start=-0.005*MHz,
                    stop=0.005*MHz,
                    npoints=40
                ),
                global_min=-5*MHz,
                global_max=5*MHz,
                precision=6,
                unit='MHz'
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
        ###################################################################################################################################################################################
        
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
        self.fitting_func.setup(len(self.scan_freq.sequence))
        # Create datasets
        self.num_samples = len(self.scan_freq.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("del_freq", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pos", self.num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="del_freq",
            pen=False,
            fit_data_name='fit_signal',
            pos_data_name="pos"
        )


        if self.vib_mode=="mode1":

            del_m=self.parameter_manager.get_param("SDF/mode1/delta_m") if "Scan_Type"=='Delta_s' else 0
            del_s=self.parameter_manager.get_param("SDF/mode1/delta_s") if "Scan_Type"=='Delta_m' else 0
            
            self.amp_729_sp=self.parameter_manager.get_param("SDF/mode1/amp_729_sp")
            self.amp_729_sp_aux=self.parameter_manager.get_param("SDF/mode1/amp_729_sp_aux")

            self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP2mode/vib_freq1")+del_s-del_m
            self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq1")+del_s+del_m
        elif self.vib_mode=="mode2":

            del_m=self.parameter_manager.get_param("SDF/mode2/delta_m") if "Scan_Type"=='Delta_s' else 0
            del_s=self.parameter_manager.get_param("SDF/mode2/delta_s") if "Scan_Type"=='Delta_m' else 0

            self.amp_729_sp=self.parameter_manager.get_param("SDF/mode2/amp_729_sp")
            self.amp_729_sp_aux=self.parameter_manager.get_param("SDF/mode2/amp_729_sp_aux")

            self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP2mode/vib_freq2")+del_s-del_m
            self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq2")+del_s+del_m
        else:

            del_m=self.parameter_manager.get_param("SDF/mode_single_ion/delta_m") if "Scan_Type"=='Delta_s' else 0
            del_s=self.parameter_manager.get_param("SDF/mode_single_ion/delta_s") if "Scan_Type"=='Delta_m' else 0

            self.amp_729_sp=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp")
            self.amp_729_sp_aux=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp_aux")

            self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq")+del_s-del_m
            self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq")+del_s+del_m




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
            delay(3*us)
            self.dds_729_dp.sw.on()
            delay(self.rot_time)
            self.dds_729_dp.sw.off()

            
            self.dds_729_dp.set_att(att_729_dp)
            delay(2*us) 
            for _ in range(2):
                self.ttl_awg_trigger.pulse(1*us)
                delay(3*us)
                if self.SDF_time>10*ns:
                    self.dds_729_dp.sw.on()
                    delay(self.SDF_time)
                    self.dds_729_dp.sw.off()
                delay(2*us)  
            
            #pi/2
            self.dds_729_dp.set_att(self.rot_att_729_dp)
            self.ttl_awg_trigger.pulse(1*us)
            delay(3*us)
            self.dds_729_dp.sw.on()
            delay(self.rot_time)
            self.dds_729_dp.sw.off()

            #turn off
            self.ttl_awg_trigger.pulse(1*us)
        else:
            self.dds_729_dp.set_att(att_729_dp)
            delay(2*us) 
            for _ in range(2):
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
    def exp_seq(self, ion_status_detect):

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
        self.rabi_AWG(self.freq_729_dp+freq_diff_dp, self.att_729_dp)


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
            i=len(self.scan_freq.sequence)
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        freq_i=0
        while freq_i < len(self.scan_freq.sequence):

            total_thresh_count = 0
            sample_num=0
            # delta frequency
            del_freq = self.scan_freq.sequence[freq_i]
            delay(20*us)

            self.seq.ion_store.run()
            
            if self.Scan_Type == 'Delta_s':
                self.send_exp_para(self.freq_729_sp_aux + del_freq, self.freq_729_sp + del_freq, self.amp_729_sp_aux, self.amp_729_sp)  
            else:
                self.send_exp_para(self.freq_729_sp_aux + del_freq, self.freq_729_sp - del_freq, self.amp_729_sp_aux, self.amp_729_sp) 
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

                    self.exp_seq(ion_status_detect)
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

                      
                    if (ion_status_detect==ion_status_detect_last):# and (ion_status_detect==1 or ion_status_detect==2) and (ion_status!=3)): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [i, sample_num],
                        #                             cam_input[0])
                        
                        if ion_status==0:
                            total_thresh_count += 1

                        #total_pmt_counts += cam_input[0]

                        delay(20*us)
                    elif (ion_status_detect==1 or ion_status_detect==2):
                        ion_status_detect_last=ion_status_detect
                        self.seq.ion_store.run()
                        delay(1*s)
                    

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
                    self.core.break_realtime()


            self.experiment_data.append_list_dataset("del_freq", del_freq/MHz)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                        float(total_thresh_count) / self.samples_per_time)
            
            freq_i=freq_i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)
    
    def analyze(self):        
        freq=self.get_dataset("del_freq")
        PMT_count=self.get_dataset('pmt_counts_avg_thresholded')

        if self.Scan_Type == 'Delta_s':
            peak=self.fitting_func.fit(freq, PMT_count)[1]
        else:
            peak=self.fitting_func.fit(freq, -PMT_count)[1]
        

        del_fit=peak*MHz
        # if self.Scan_Type == 'Delta_s':
        #     del_fit=freq[np.argmax(PMT_count)]*MHz
        # else:
        #     del_fit=freq[np.argmin(PMT_count)]*MHz
        
        
        param_name=""
        if self.Scan_Type == 'Delta_s':
            match self.vib_mode:
                case "mode2":
                    param_name="SDF/mode2/delta_s"
                case "mode1":
                    param_name="SDF/mode1/delta_s"       
                case "mode_single_ion":
                    param_name="SDF/mode_single_ion/delta_s"

        elif self.Scan_Type == 'Delta_m':
            match self.vib_mode:
                case "mode2":
                    param_name="SDF/mode2/delta_m"
                case "mode1":
                    param_name="SDF/mode1/delta_m"       
                case "mode_single_ion":
                    param_name="SDF/mode_single_ion/delta_m"
        
        with self.interactive(param_name) as inter:
            inter.setattr_argument(
                "del_freq",
                NumberValue(default=del_fit*1.0, unit="MHz", min=0.*MHz, max=240.*MHz, precision=8)
            )
        
        self.parameter_manager.set_param(
            param_name,
            inter.del_freq,
            "MHz"
        )

        # if "vib_mode"=="mode_single_ion":#, EnumerationValue(["mode1","mode2","mode_single_ion"], default="mode1"))
            

        # with self.interactive("397 Frequency peak position estimate") as inter:
        #     inter.setattr_argument(
        #         "freq_397_resonance",
        #         NumberValue(default=freq[np.argmax(PMT_count)]*MHz-0.5*MHz, unit="MHz", min=160*MHz, max=240*MHz)
        #     )

        #     inter.setattr_argument(
        #         "freq_397_cooling",
        #         NumberValue(default=freq[np.argmax(PMT_count)]*MHz-5.2*MHz, unit="MHz", min=160*MHz, max=240*MHz)
        #     )

        # self.parameter_manager.set_param(
        #     "frequency/397_resonance",
        #     inter.freq_397_resonance,
        #     "MHz"
        # )

        # self.parameter_manager.set_param(
        #     "frequency/397_cooling",
        #     inter.freq_397_cooling,
        #     "MHz"
        # )
