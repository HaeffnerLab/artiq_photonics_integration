from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para

class A6_att729_scan_AWG_Cam(_ACFExperiment):

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
            NumberValue(default=1000*us, min=0*us, max=5*ms, unit="us",precision=8),
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
            "att_729_dp",
            NumberValue(default=20*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=0.2, min=0, max=1,  precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        self.setattr_argument(
            "scan_att_729",
            Scannable(
                default=RangeScan(
                    start=8*dB,
                    stop=25*dB,
                    npoints=25
                ),
                global_min=8*dB,
                global_max=31.5*dB,
                unit="dB",
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool2mode", "opticalpumping", "sidebandcool_single_ion"], default="sidebandcool2mode"))
        
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
        # Create datasets
        num_samples = len(self.scan_att_729.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation_dB", num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="attenuation_dB",
            pen=False,
            pos_data_name="pos"
        )

        if self.vib_mode=="mode1":
            self.freq_729_dp+=self.parameter_manager.get_param("VdP2mode/vib_freq1")/2.0
        elif self.vib_mode=="mode2":
            self.freq_729_dp+=self.parameter_manager.get_param("VdP2mode/vib_freq2")/2.0
        else:
            self.freq_729_dp+=self.parameter_manager.get_param("qubit/vib_freq")


    @kernel
    def rabi_AWG(self,pulse_time, freq_729_dp, att_729_dp):
        
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

    @kernel
    def exp_seq(self, att_729_dp, ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()
  
        if self.cooling_option == "sidebandcool":
            if ion_status_detect==2:
                self.seq.sideband_cool.run(freq_offset=self.freq_vib2, 
                                           att_729_here=att_729_dp,
                                           freq_diff_dp=self.freq_diff_dp, 
                                           att_854_here=self.sideband_mode2_att854) 
                
                self.seq.sideband_cool.run(freq_offset=self.freq_vib1, 
                                           att_729_here=att_729_dp,
                                           freq_diff_dp=self.freq_diff_dp, 
                                           att_854_here=self.sideband_mode1_att854) 
            else:
                self.seq.sideband_cool.run(freq_offset=self.freq_vib2, 
                                           att_729_here=att_729_dp,
                                           att_854_here=self.sideband_mode2_att854) 
                self.seq.sideband_cool.run(freq_offset=self.freq_vib1, 
                                           att_729_here=att_729_dp,
                                           att_854_here=self.sideband_mode1_att854) 
            
        elif self.cooling_option == "sidebandcool2mode":
            
            if ion_status_detect==2:
                self.seq.sideband_cool_2mode.run(att_729_here=att_729_dp,  freq_diff_dp=self.freq_diff_dp) 
            else:
                self.seq.sideband_cool_2mode.run(att_729_here=att_729_dp)

        elif self.cooling_option == "sidebandcool_single_ion":
            self.seq.sideband_cool.run(att_729_here=att_729_dp) 
        
        # rabi 
        if ion_status_detect==2:
            self.rabi_AWG(self.rabi_t, self.freq_729_dp+self.freq_diff_dp, self.att_729_dp)
        else:
            self.rabi_AWG(self.rabi_t, self.freq_729_dp, self.att_729_dp)

    @rpc(flags={'async'})
    def send_exp_para(self):
        send_exp_para(["SingleTone",{"freq": self.freq_729_sp,"amp": self.amp_729_sp, "num_loop":max(self.samples_per_time+100,100)}])
  

        
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
        while i < len(self.scan_att_729.sequence):

            total_thresh_count = 0
            sample_num=0
            att_729_dp =self.scan_att_729.sequence[i]
            num_try_save_ion = 0 


            delay(20*us)
            self.seq.ion_store.run()
            self.send_exp_para()   
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq( att_729_dp, ion_status_detect)
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
                        
                        total_thresh_count += 1 if ion_status==0 else 0
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
                    delay(1*ms)


            self.experiment_data.append_list_dataset("attenuation_dB", att_729_dp/dB)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg",
                                        float(total_thresh_count) / self.samples_per_time)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)

