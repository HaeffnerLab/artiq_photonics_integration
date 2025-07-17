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

class A6_VdP1mode_Wigner_AWG_Cam(_ACFExperiment):

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
        self.seq.vdp2mode_one.build()
        self.seq.cam_two_ions.build()


        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("vib_mode", EnumerationValue(["mode1","mode2","mode_single_ion"], default="mode1"))

        # the scan parameter for the displacement operator
        self.setattr_argument("enable_start_from_cat_state", BooleanValue(False),
            group='beta grid')
        self.setattr_argument(
            "drive_time_us",
            NumberValue(default=120*us, min=0.001*us, max=300*us,  precision=8, unit='us'),
            tooltip="729 single pass amplitude",
            group='beta grid'
        )
        self.setattr_argument("enable_polar_coordinates", BooleanValue(False),
            group='beta grid')
        self.setattr_argument(
            "num_beta_r",
            NumberValue(default=21, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group='beta grid'
        )   
        self.setattr_argument(
            "num_beta_theta",
            NumberValue(default=16, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group='beta grid'
        )   

        self.setattr_argument(
            "beta_range_us",
            NumberValue(default=30*us, min=0.001*us, max=300*us,  precision=8, unit='us'),
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

        self.setattr_argument("readout_option", EnumerationValue(["2D", "1D_1", "1D_2"], default="2D"))
        self.setattr_argument("randomize", BooleanValue(True))
        self.setattr_argument("symmetric_randomize", BooleanValue(False))

        self.att_729_dp=self.parameter_manager.get_float_param('attenuation/729_dp')
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
        self.seq.adjust_729_freq.prepare()
        self.seq.calibrate_motion.prepare()

        if self.readout_option=="1D_1":
            # Create datasets
            num_samples = self.num_beta
            self.num_samples = self.num_beta
            #beta sampling
            self.beta=np.linspace(-self.beta_range_us,self.beta_range_us,self.num_beta).reshape((self.num_beta,1))
        elif self.readout_option=="1D_2":
            # Create datasets
            num_samples = self.num_beta
            self.num_samples = self.num_beta
            #beta sampling
            self.beta=1.0j*np.linspace(-self.beta_range_us,self.beta_range_us, self.num_beta).reshape((1,self.num_beta))
        else:
            # Create datasets
            if self.enable_polar_coordinates:
                num_samples = self.num_beta_theta*self.num_beta_r
                self.num_samples = self.num_beta_theta*self.num_beta_r
                self.beta=np.zeros((self.num_beta_theta,self.num_beta_r),dtype=np.complex128)
            else:
                num_samples = self.num_beta*self.num_beta
                self.num_samples = self.num_beta*self.num_beta
                self.beta=np.linspace(-self.beta_range_us,self.beta_range_us,self.num_beta).reshape((self.num_beta,1))+1.0j*np.linspace(-self.beta_range_us,self.beta_range_us, self.num_beta).reshape((1,self.num_beta))
            
        # Create datasets
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("beta_index", num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="beta_index",
            pen=False,
            pos_data_name="pos"
        )

    
        #np.savetxt(get_config_dir()/'../repository/Vdp/beta.txt', self.beta)

        #from beta to corresponding time & phase
        self.beta_time=np.zeros(self.beta.shape[0]*self.beta.shape[1],dtype=float)
        self.beta_phase=np.zeros(self.beta.shape[0]*self.beta.shape[1],dtype=float)
        
        #compute the time & phase based on the parameters

        if self.enable_polar_coordinates:
            idx=0
            for i in range(self.num_beta_r):
                for j in range(self.num_beta_theta):
                    self.beta_time[idx]=float(self.beta_range_us*(i+1.0)/self.num_beta_r)
                    self.beta_phase[idx]=j/self.num_beta_theta #in unit of turns (2pi)
                    idx+=1
        else:
            idx=0
            for i in range(self.beta.shape[0]):
                for j in range(self.beta.shape[1]):
                    self.beta_time[idx]=float(np.abs(self.beta[i][j]))
                    self.beta_phase[idx]=(np.angle(self.beta[i][j])-np.pi/2)/(2*np.pi) #in unit of turns (2pi)
                    idx+=1
        np.savetxt(get_config_dir()/'../repository/Vdp/beta_time.txt', self.beta_time)
        np.savetxt(get_config_dir()/'../repository/Vdp/beta_phase.txt', self.beta_phase)  

        if self.randomize:
            self.beta_time, self.beta_phase, self.indices= self.shuffle_two_arrays_with_single_indices(self.beta_time, self.beta_phase)
        elif self.symmetric_randomize and self.readout_option=="2D":

            if self.num_beta%2==0:
                # Group symmetric points together before shuffling
                n = self.num_beta // 2
                grouped_indices = []
                
                # Create groups of 4 symmetric points
                for i in range(n):
                    for j in range(n):
                        group = [
                            i*2*n + j,                   # (i,j)
                            (2*n-1-i)*2*n + j,           # (n-i,j) 
                            i*2*n + (2*n-1-j),           # (i,n-j)
                            (2*n-1-i)*2*n + (2*n-1-j)    # (n-i,n-j)
                        ]
                        grouped_indices.append(group)
                
                # Shuffle the groups
                random.shuffle(grouped_indices)
                
                # Flatten the groups into final sequence
                final_indices = [idx for group in grouped_indices for idx in group]
                
                # Reorder the time and phase arrays according to grouped indices
                self.beta_time = np.array([self.beta_time[i] for i in final_indices])
                self.beta_phase = np.array([self.beta_phase[i] for i in final_indices])
                self.indices = final_indices
            else:
                # Handle odd case
                n = self.num_beta // 2  # Integer division gives middle point
                grouped_indices = []
                
                # Create groups of 4 symmetric points for the rest
                for i in range(n):
                    for j in range(n):
                        group = [
                            i*(2*n+1) + j,                    # (i,j)
                            (2*n-i)*(2*n+1) + j,             # (2n-i,j)
                            i*(2*n+1) + (2*n-j),             # (i,2n-j)
                            (2*n-i)*(2*n+1) + (2*n-j)        # (2n-i,2n-j)
                        ]
                        grouped_indices.append(group)
                
                for i in range(n):
                    grouped_indices.append(
                        [
                            i*(2*n+1) + n,                  # (i,n)
                            (2*n-i)*(2*n+1) + n,            # (2n-i,n)
                            n*(2*n+1) + i,                  # (n,i)
                            n*(2*n+1) + (2*n-i)             # (n,2n-i)
                        ]
                        )
                grouped_indices.append([n*(2*n+1) + n])     # (n,n)
                
                # Shuffle the groups
                random.shuffle(grouped_indices)
                
                # Combine all indices
                final_indices = [idx for group in grouped_indices for idx in group]
                
                # Reorder the time and phase arrays according to grouped indices
                self.beta_time = np.array([self.beta_time[i] for i in final_indices])
                self.beta_phase = np.array([self.beta_phase[i] for i in final_indices])
                self.indices = final_indices
        else:
            self.indices=[i for i in range(len(self.beta_time))]


        if self.vib_mode=="mode1":

            del_m=self.parameter_manager.get_param("SDF/mode1/delta_m")
            del_s=self.parameter_manager.get_param("SDF/mode1/delta_s")
            
            self.att_729_dp=self.parameter_manager.get_param("SDF/mode1/att_729_dp")

            self.amp_729_sp=self.parameter_manager.get_param("SDF/mode1/amp_729_sp")
            self.amp_729_sp_aux=self.parameter_manager.get_param("SDF/mode1/amp_729_sp_aux")

            self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP2mode/vib_freq1")+del_s-del_m
            self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq1")+del_s+del_m
        elif self.vib_mode=="mode2":

            del_m=self.parameter_manager.get_param("SDF/mode2/delta_m")
            del_s=self.parameter_manager.get_param("SDF/mode2/delta_s") 

            self.att_729_dp=self.parameter_manager.get_param("SDF/mode2/att_729_dp")

            self.amp_729_sp=self.parameter_manager.get_param("SDF/mode2/amp_729_sp")
            self.amp_729_sp_aux=self.parameter_manager.get_param("SDF/mode2/amp_729_sp_aux")

            self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP2mode/vib_freq2")+del_s-del_m
            self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq2")+del_s+del_m
        else:

            del_m=self.parameter_manager.get_param("SDF/mode_single_ion/delta_m")
            del_s=self.parameter_manager.get_param("SDF/mode_single_ion/delta_s")
            
            self.att_729_dp=self.parameter_manager.get_param("SDF/mode_single_ion/att_729_dp")

            self.amp_729_sp=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp")
            self.amp_729_sp_aux=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp_aux")

            self.freq_729_sp=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq")+del_s-del_m
            self.freq_729_sp_aux=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq")+del_s+del_m

    def shuffle_two_arrays_with_single_indices(self, arr1, arr2):
        # Combine the two arrays into a list of tuples (index, value from arr1, value from arr2)
        indexed_pairs = [(i, arr1[i], arr2[i]) for i in range(len(arr1))]
        
        # Shuffle the list of tuples
        random.shuffle(indexed_pairs)
        
        # Extract the shuffled values and their original indices
        shuffled_arr1 = [pair[1] for pair in indexed_pairs]
        shuffled_arr2 = [pair[2] for pair in indexed_pairs]
        original_indices = [pair[0] for pair in indexed_pairs]
        
        return shuffled_arr1, shuffled_arr2, original_indices
    @kernel
    def readout_AWG(self, beta_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set_att(att_729_dp)
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()

        #turn on sync red sideband in AWG
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.off()
        
        #drive vdp
        self.ttl_rf_switch_AWG_729SP.on()
        self.ttl_rf_switch_DDS_729SP.off()

        if self.enable_start_from_cat_state:
            #readout the motional state
            self.dds_729_dp.set_att(att_729_dp)
            self.ttl_awg_trigger.pulse(1*us)
            delay(3*us)
            if beta_time>0.01*us:
                self.dds_729_dp.sw.on()
                delay(self.drive_time_us)
                self.dds_729_dp.sw.off()
            delay(3*us)
            self.ttl_awg_trigger.pulse(1*us)


        self.seq.vdp2mode_one.run()
        
        # Prepare the Spin State to |down>
        self.seq.repump_854.run()

        #readout the motional state
        self.dds_729_dp.set_att(att_729_dp)
        self.ttl_awg_trigger.pulse(1*us)
        delay(3*us)
        if beta_time>0.01*us:
            self.dds_729_dp.sw.on()
            delay(beta_time)
            self.dds_729_dp.sw.off()
        delay(3*us)
        self.ttl_awg_trigger.pulse(1*us)

        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.off()

    @kernel
    def exp_seq(self, freq_729_dp, beta_time, ion_status_detect):
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
        delay(5*us)
        
        # rabi 
        self.readout_AWG(beta_time, freq_729_dp+freq_diff_dp, self.att_729_dp)



    @rpc(flags={'async'})
    def send_exp_para(
        self,
        freq_RSB,
        freq_BSB,
        amp_RSB,
        amp_BSB, 
        phase
    ):
        
        if self.enable_start_from_cat_state:
                send_exp_para(["Displacement_SDF", {
                "freq_sp_RSB":   freq_RSB,
                "freq_sp_BSB":   freq_BSB,
                "amp_sp_RSB":  amp_RSB,
                "amp_sp_BSB":   amp_BSB,
                "phase": phase,
                "num_loop":max(self.samples_per_time+100,400)
            }])  
        else:
            send_exp_para(["SDF", {
                    "freq_sp_RSB":   freq_RSB,
                    "freq_sp_BSB":   freq_BSB,
                    "amp_sp_RSB":  amp_RSB,
                    "amp_sp_BSB":   amp_BSB,
                    "phase": phase,
                    "num_loop":max(self.samples_per_time+300,400)
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
        self.seq.vdp2mode_one.prepare(self.vib_mode)
        self.core.break_realtime()

        #################################################################################################################################
        while i < self.num_samples:
            total_thresh_count = 0
            sample_num=0
            num_try_save_ion = 0         

            delay(20*us)
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
                ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(vib_mode=self.vib_mode)
                ion_status_detect_last=ion_status_detect

            self.seq.vdp2mode_one.prepare(self.vib_mode)
            freq_729_dp=self.seq.adjust_729_freq.get_qubit_freq_tracker()
            self.core.break_realtime() 

            self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp, self.amp_729_sp_aux, self.amp_729_sp,self.beta_phase[i]*360)

            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue
            
            is_zero_time=False
            if self.beta_time[i]<0.05*us:
                is_zero_time=True

            if is_zero_time:
                total_thresh_count=0
            else:

                while sample_num<self.samples_per_time:
                    if ion_status_detect==1 or ion_status_detect==2:
                        #line trigger
                        if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                            continue
                        
                        delay(50*us)

                        self.exp_seq(freq_729_dp, self.beta_time[i], ion_status_detect)
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
        
            self.experiment_data.insert_nd_dataset("beta_index", self.indices[i], self.indices[i] )
            self.experiment_data.insert_nd_dataset("pos",self.indices[i], ion_status_detect)
            self.experiment_data.insert_nd_dataset("pmt_counts_avg_thresholded",self.indices[i],
                                        float(total_thresh_count) / self.samples_per_time)
            
            if (not is_zero_time) and total_thresh_count==0:
                print("qubit laser if unlocked; waiting")
            else:
                i=i+1
            print(i, "out of ", self.num_samples)
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)
        self.core.break_realtime()
