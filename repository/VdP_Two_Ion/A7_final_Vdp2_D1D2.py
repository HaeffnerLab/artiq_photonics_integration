from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import stark_shift_SDF_kernel
import time
import random


class A7_Sync_VdP2_D1D2(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.seq.adjust_729_freq.build()
        self.seq.calibrate_motion.build()
        self.seq.vdp2mode.build()
        self.seq.cam_two_ions.build()

        
        # Readout mode 1
        self.seq.sdf_mode1.build()
        # Readout mode 2
        self.seq.sdf_mode2.build()


        # the scan parameter for the displacement operator
        self.setattr_argument(
            "tau_1",
            NumberValue(default=30.0*us, min=0.001*us, max=300*us,  precision=8, unit='us'),
            tooltip="729 single pass amplitude",
            group='phase scan'
        )
        self.setattr_argument(
            "tau_2",
            NumberValue(default=30.0*us, min=0.001*us, max=300*us,  precision=8, unit='us'),
            tooltip="729 single pass amplitude",
            group='phase scan'
        )

        self.setattr_argument(
            "samples_phase_points",
            NumberValue(default=200, precision=0, step=1),
            tooltip="Number of phase points to scan",
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool_single_ion", "sidebandcool2mode", "opticalpumping"], default="sidebandcool2mode"))

        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("randomize", BooleanValue(True))
        self.setattr_argument(
            "freq_detune",
            NumberValue(default=0, min=-1000, max=1000, unit="Hz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument(
            "V_scale",
            NumberValue(default=1.0, min=0.0, max=5.0,  precision=8),
            tooltip="729 single pass amplitude",
        )
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

    def shuffle_one_array_with_single_indices(self, arr1):
        # Combine the two arrays into a list of tuples (index, value from arr1, value from arr2)
        indexed_pairs = [(i, arr1[i]) for i in range(len(arr1))]
        
        # Shuffle the list of tuples
        random.shuffle(indexed_pairs)
        
        # Extract the shuffled values and their original indices
        shuffled_arr1 = [pair[1] for pair in indexed_pairs]
        original_indices = [pair[0] for pair in indexed_pairs]
        
        return shuffled_arr1, original_indices
    

    def prepare(self):

        self.seq.adjust_729_freq.prepare()
        self.seq.calibrate_motion.prepare()

        # Create datasets
        self.num_samples = self.samples_phase_points
        self.experiment_data.set_nd_dataset("pmt_counts", [self.num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("phase", self.num_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        self.phase_scan=np.linspace(0, 1, self.samples_phase_points)

        if self.randomize:
            self.phase_scan, self.indices = self.shuffle_one_array_with_single_indices(self.phase_scan)
        else:
            self.indices = np.arange(self.num_samples)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="phase",
            pen=False#,
            #fit_data_name='fit_signal'#,
            #pos_data_name="pos"
        )

        
    @kernel
    def readout_AWG(self, freq_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        delay(2*us)

        
        #Vdp Evolution of the two modes
        self.seq.vdp2mode.run(self.freq_detune)

        self.ttl_rf_switch_AWG_729SP.on()

        #repump
        self.seq.repump_854.run()

        #SDF 1
        self.seq.sdf_mode1.run(self.tau_1)

        #SDF 2
        self.seq.sdf_mode2.run(self.tau_2)

        #turn off AWG
        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()
        delay(5*us)
        
    @kernel
    def exp_seq(self, freq_729_dp, ion_status_detect):
         #854 repump
        self.seq.repump_854.run()
        #  Cool
        self.seq.doppler_cool.run()
        #sideband
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
            self.seq.op_pump.run(freq_diff_dp=freq_diff_dp) 

        #apply SDF
        self.readout_AWG(freq_729_dp+freq_diff_dp)

    @rpc(flags={'async'})
    def send_exp_para(self, phase1, phase2):
        send_exp_para(["VdP2mode_2D", {
                "freq_VdP_RSB1":self.seq.vdp2mode.Sync_mode1_freq_729_RSB,
                "freq_VdP_RSB2":self.seq.vdp2mode.Sync_mode2_freq_729_RSB+self.freq_detune,
                "amp_VdP_RSB1" :self.seq.vdp2mode.Sync_mode1_amp_729_RSB*self.V_scale,
                "amp_VdP_RSB2" :self.seq.vdp2mode.Sync_mode2_amp_729_RSB*self.V_scale,

                "freq_readout_RSB1": self.seq.sdf_mode1.freq_729_sp_aux,
                "freq_readout_BSB1": self.seq.sdf_mode1.freq_729_sp,

                "freq_readout_RSB2": self.seq.sdf_mode2.freq_729_sp_aux+self.freq_detune,
                "freq_readout_BSB2": self.seq.sdf_mode2.freq_729_sp+self.freq_detune,

                "amp_readout_RSB1": self.seq.sdf_mode1.amp_729_sp_aux,
                "amp_readout_BSB1": self.seq.sdf_mode1.amp_729_sp,

                "amp_readout_RSB2": self.seq.sdf_mode2.amp_729_sp_aux,
                "amp_readout_BSB2": self.seq.sdf_mode2.amp_729_sp,

                "phase_readout_mode1":phase1,
                "phase_readout_mode2":phase2,

                "phase_offset": self.seq.vdp2mode.Vdp_sync_phase_degree,
                "num_cycle_no_sync":self.seq.vdp2mode.Vdp_Repeat_Time_no_sync,
                "num_cycle_sync":self.seq.vdp2mode.Vdp_Repeat_Time_sync,
                "num_loop":max(self.samples_per_time+400,400)
            }]) 


        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()

        self.seq.cam_two_ions.cam_setup()
        #################################################################################################################################
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
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
            i=1000000
        else:
            i=0
        ion_status_detect = ion_status_detect_last
        #################################################################################################################################

        freq_729_dp=self.get_qubit_freq()
        self.seq.vdp2mode.prepare()
        self.core.break_realtime()

        #################################################################################################################################
        while i < self.num_samples:
            total_thresh_count = 0
            sample_num=0
            num_try_save_ion = 0 

            print(i, "out of ", self.num_samples)

            phase_here=self.phase_scan[i]

            self.core.break_realtime()
            self.seq.ion_store.run()

            #calibrate qubit frequency
            if self.seq.adjust_729_freq.check_interval():
                ion_status_detect=self.seq.adjust_729_freq.calibrate_freq_qubit(
                    line="Sm1_2_Dm5_2", 
                    cooling_option=self.cooling_option,
                    wait_time=100*us
                    )
                ion_status_detect_last=ion_status_detect
            
            if self.seq.calibrate_motion.check_interval():
                ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(vib_mode='mode1')
                ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(vib_mode='mode2')
                ion_status_detect_last=ion_status_detect
            self.seq.vdp2mode.prepare()
            self.seq.sdf_mode1.prepare()
            self.seq.sdf_mode2.prepare()
            self.core.break_realtime()
            
            freq_729_dp=self.seq.adjust_729_freq.get_qubit_freq_tracker()

            self.core.break_realtime()
            self.send_exp_para(0.0*360.0, phase_here*360.0)
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(freq_729_dp, ion_status_detect)
                    ################################################################################ get readout
                    ion_status=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()
                    delay(50*us)
                    ################################################################################ get ion position
                    if ion_status==0: #if the ion is not bright then it's possible it's being kicked
                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        ion_status_detect=self.seq.cam_two_ions.cam_readout() #by the way get the position
                        self.seq.ion_store.run()
                        delay(20*us)
                    else: 
                        ion_status_detect=ion_status
                    ################################################################################
                      
                    if (ion_status_detect==ion_status_detect_last and ion_status_detect==1): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        self.experiment_data.insert_nd_dataset("pmt_counts",
                                                    [i, sample_num],
                                                    ion_status)
                        
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
                    
                    if(num_try_save_ion>6000):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break
                    delay(100*ms)
    
            self.experiment_data.insert_nd_dataset("phase", self.indices[i], phase_here )
            self.experiment_data.insert_nd_dataset("pos",self.indices[i], ion_status_detect)
            self.experiment_data.insert_nd_dataset("pmt_counts_avg_thresholded",self.indices[i],
                                        float(total_thresh_count) / self.samples_per_time)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()
