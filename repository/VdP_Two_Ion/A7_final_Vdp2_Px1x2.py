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

class A7_Sync_VdP2_Px1x2(_ACFExperiment):

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
            "beta_range_us1",
            NumberValue(default=60.0*us, min=0.001*us, max=300*us,  precision=8, unit='us'),
            tooltip="729 single pass amplitude",
            group='beta grid'
        )
        self.setattr_argument(
            "beta_range_us2",
            NumberValue(default=75.0*us, min=0.001*us, max=300*us,  precision=8, unit='us'),
            tooltip="729 single pass amplitude",
            group='beta grid'
        )
        self.setattr_argument(
            "num_beta",
            NumberValue(default=21, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group='beta grid'
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool_single_ion", "sidebandcool2mode", "opticalpumping"], default="sidebandcool2mode"))
        
        self.setattr_argument("readout_option", EnumerationValue(["2D", "1D_1", "1D_2", "1D_circle"], default="2D"))
        self.setattr_argument("randomize_option", EnumerationValue(["randomize", "sort_by_magnitude","sorted"], default="sort_by_magnitude"))
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument(
            "freq_detune",
            NumberValue(default=0, min=-10000, max=10000, unit="Hz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument(
            "V_scale",
            NumberValue(default=1.0, min=0.0, max=5.0,  precision=8),
            tooltip="729 single pass amplitude",
        )
        self.setattr_argument(
            "Px1p2",
            BooleanValue(default=False),
            tooltip="if True, then Px1p2 else Px1x2"
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
    def shuffle_four_arrays_with_single_indices(self, arr1, arr2, arr3, arr4):
        # Combine the two arrays into a list of tuples (index, value from arr1, value from arr2)
        indexed_pairs = [(i, arr1[i], arr2[i], arr3[i], arr4[i]) for i in range(len(arr1))]
        
        # Shuffle the list of tuples
        random.shuffle(indexed_pairs)
        
        # Extract the shuffled values and their original indices
        shuffled_arr1 = [pair[1] for pair in indexed_pairs]
        shuffled_arr2 = [pair[2] for pair in indexed_pairs]
        shuffled_arr3 = [pair[3] for pair in indexed_pairs]
        shuffled_arr4 = [pair[4] for pair in indexed_pairs]
        original_indices = [pair[0] for pair in indexed_pairs]
        
        return shuffled_arr1, shuffled_arr2, shuffled_arr3, shuffled_arr4, original_indices

    def sort_four_arrays_by_magnitude(self, arr1, arr2, arr3, arr4):
        # Combine the arrays into a list of tuples with their magnitude
        indexed_pairs = [(i, arr1[i], arr2[i], arr3[i], arr4[i], np.sqrt(arr1[i]**2 + arr2[i]**2)) for i in range(len(arr1))]
        
        # Sort the list of tuples by magnitude (last element)
        indexed_pairs.sort(key=lambda x: x[5])
        
        # Extract the sorted values and their original indices
        sorted_arr1 = [pair[1] for pair in indexed_pairs]
        sorted_arr2 = [pair[2] for pair in indexed_pairs]
        sorted_arr3 = [pair[3] for pair in indexed_pairs]
        sorted_arr4 = [pair[4] for pair in indexed_pairs]
        original_indices = [pair[0] for pair in indexed_pairs]
        
        return sorted_arr1, sorted_arr2, sorted_arr3, sorted_arr4, original_indices
    def prepare(self):
        self.seq.adjust_729_freq.prepare()
        self.seq.calibrate_motion.prepare()
        if self.readout_option=="2D":
            # Create datasets
            self.num_samples = int(self.num_beta*self.num_beta)
            #from beta to corresponding time & phase
            self.beta_time1, self.beta_time2=np.meshgrid(
                    np.linspace(-self.beta_range_us1, self.beta_range_us1, self.num_beta),
                    np.linspace(-self.beta_range_us2, self.beta_range_us2, self.num_beta),
                )
        elif self.readout_option=="1D_1":
            # Create datasets
            self.num_samples = int(self.num_beta)
            #from beta to corresponding time & phase
            self.beta_time1, self.beta_time2=np.meshgrid(
                    np.linspace(-self.beta_range_us1, self.beta_range_us1, self.num_beta),
                    np.linspace(-0.0, 0.0, 1),
                )
        elif self.readout_option=="1D_2":
            # Create datasets
            self.num_samples = int(self.num_beta*self.num_beta)
            #from beta to corresponding time & phase
            self.beta_time1, self.beta_time2=np.meshgrid(
                    np.linspace(-0.0, 0.0, 1),
                    np.linspace(-self.beta_range_us2, self.beta_range_us2, self.num_beta),
                )
        elif self.readout_option=="1D_circle":
            # Create datasets
            self.num_samples = int(self.num_beta)
            #from beta to corresponding time & phase
            self.beta_time1=np.zeros(self.num_samples)
            self.beta_time2=np.zeros(self.num_samples)

            for i in range(self.num_samples):
                self.beta_time1[i]=self.beta_range_us1*np.cos(np.pi*i/(self.num_samples-1))
                self.beta_time2[i]=self.beta_range_us2*np.sin(np.pi*i/(self.num_samples-1))

        self.beta_time1=self.beta_time1.flatten()
        self.beta_time2=self.beta_time2.flatten()
        
        self.beta_phase1=self.beta_time1.flatten()
        self.beta_phase2=self.beta_time2.flatten()
        for i in range(len(self.beta_phase1)):
            self.beta_phase1[i]=(np.angle(self.beta_time1[i])-np.pi/2)/(2*np.pi)
            self.beta_phase2[i]=(np.angle(self.beta_time2[i])-np.pi/2)/(2*np.pi)
            self.beta_time1[i]=np.abs(self.beta_time1[i])
            self.beta_time2[i]=np.abs(self.beta_time2[i])
        

        self.experiment_data.set_nd_dataset("pmt_counts", [self.num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", self.num_samples, broadcast=True)

        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded2", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("beta_index", self.num_samples, broadcast=True)

        #Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="beta_index",
            pen=False,
            pos_data_name="pos"
        )

        if self.randomize_option == "randomize":
            self.beta_time1, self.beta_time2, self.beta_phase1, self.beta_phase2, self.indices = self.shuffle_four_arrays_with_single_indices(self.beta_time1, self.beta_time2, self.beta_phase1, self.beta_phase2)
        elif self.randomize_option == "sort_by_magnitude":
            self.beta_time1, self.beta_time2, self.beta_phase1, self.beta_phase2, self.indices = self.sort_four_arrays_by_magnitude(self.beta_time1, self.beta_time2, self.beta_phase1, self.beta_phase2)
        else:
            self.indices = np.arange(self.num_samples)

    @kernel
    def readout_AWG(self, pulse_time1, pulse_time2, freq_729_dp):
        
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
        self.seq.sdf_mode1.run(pulse_time1)

        #SDF 2
        self.seq.sdf_mode2.run(pulse_time2)

        #turn off AWG
        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()
        delay(5*us)
        
    @kernel
    def exp_seq(self, freq_729_dp,  beta_time1, beta_time2, ion_status_detect):
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
        self.readout_AWG(beta_time1, beta_time2, freq_729_dp+freq_diff_dp)

    @rpc(flags={'async'})
    def send_exp_para(self, phase1, phase2):
        send_exp_para(["VdP2mode_2D", {
            "freq_VdP_RSB1":self.seq.vdp2mode.Sync_mode1_freq_729_RSB,
            "freq_VdP_RSB2":self.seq.vdp2mode.Sync_mode2_freq_729_RSB+self.freq_detune,
            "amp_VdP_RSB1" :self.seq.vdp2mode.Sync_mode1_amp_729_RSB*self.V_scale,
            "amp_VdP_RSB2" :self.seq.vdp2mode.Sync_mode2_amp_729_RSB*self.V_scale,

            "freq_readout_RSB1": self.seq.sdf_mode1.freq_729_sp_aux,
            "freq_readout_BSB1": self.seq.sdf_mode1.freq_729_sp,

            "freq_readout_RSB2": self.seq.sdf_mode2.freq_729_sp_aux,#+self.freq_detune,
            "freq_readout_BSB2": self.seq.sdf_mode2.freq_729_sp,#+self.freq_detune,

            "amp_readout_RSB1": self.seq.sdf_mode1.amp_729_sp_aux,
            "amp_readout_BSB1": self.seq.sdf_mode1.amp_729_sp,

            "amp_readout_RSB2": self.seq.sdf_mode2.amp_729_sp_aux,
            "amp_readout_BSB2": self.seq.sdf_mode2.amp_729_sp,

            "phase_readout_mode1":phase1,
            "phase_readout_mode2":phase2,

            "phase_offset": self.seq.vdp2mode.Vdp_sync_phase_degree,

            "num_cycle_no_sync":self.seq.vdp2mode.Vdp_Repeat_Time_no_sync,
            "num_cycle_sync":self.seq.vdp2mode.Vdp_Repeat_Time_sync,

            "num_loop":self.samples_per_time+100,
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
        # while ion_status_detect_last!=1 and ion_status_detect_last!=2:
        #     delay(2*ms)
        #     self.seq.repump_854.run()
        #     self.seq.doppler_cool.run()
        #     delay(5*us)
        #     ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
        #     self.seq.ion_store.run()
        #     delay(1*ms)
        
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

        if self.Px1p2:
            num_iter=2
        else:
            num_iter=1

        #################################################################################################################################
        while i < self.num_samples:

            for iter in range(num_iter):
            

                print("Data point ", i, "of ", self.num_samples)

                self.core.break_realtime()
                self.seq.ion_store.run()

                #calibrate qubit frequency
                if self.seq.adjust_729_freq.check_interval():
                    ion_status_detect=self.seq.adjust_729_freq.calibrate_freq_qubit(
                            line="Sm1_2_Dm5_2", 
                            cooling_option=self.cooling_option,
                            wait_time=10*us
                            )
                   
                
                if self.seq.calibrate_motion.check_interval():
                    
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(vib_mode='mode1')
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(vib_mode='mode2')#cal_freq_range=0.002*MHz)
                ion_status_detect_last=ion_status_detect
                    
                self.seq.vdp2mode.prepare()
                self.seq.sdf_mode1.prepare()
                self.seq.sdf_mode2.prepare()
                self.core.break_realtime()
                
                freq_729_dp=self.seq.adjust_729_freq.get_qubit_freq_tracker()

                self.core.break_realtime()

            
                if iter==0:
                    self.send_exp_para(self.beta_phase1[i]*360.0, self.beta_phase2[i]*360.0)
                else:
                    self.send_exp_para(self.beta_phase1[i]*360.0, self.beta_phase2[i]*360.0+90.0)
                if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    print("BAD AWG!!!!")
                    continue


                total_thresh_count = 0
                sample_num=0
                num_try_save_ion = 0 

                while sample_num<self.samples_per_time:
                    if ion_status_detect==1 or ion_status_detect==2:
                        #line trigger
                        if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                            continue
                        
                        delay(50*us)

                        self.exp_seq(freq_729_dp,  self.beta_time1[i], self.beta_time2[i], ion_status_detect)
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

                self.experiment_data.insert_nd_dataset("beta_index", self.indices[i], self.indices[i] )
                self.experiment_data.insert_nd_dataset("pos",self.indices[i], ion_status_detect)
                if iter==0:
                    self.experiment_data.insert_nd_dataset("pmt_counts_avg_thresholded",self.indices[i],
                                            float(total_thresh_count) / self.samples_per_time)
                else:
                    self.experiment_data.insert_nd_dataset("pmt_counts_avg_thresholded2",self.indices[i],
                                            float(total_thresh_count) / self.samples_per_time)
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()
