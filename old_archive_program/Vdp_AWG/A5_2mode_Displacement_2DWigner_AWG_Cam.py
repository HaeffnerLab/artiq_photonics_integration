from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d

from artiq.coredevice.ad9910 import PHASE_MODE_ABSOLUTE, PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING

from awg_utils.transmitter import send_exp_para

class A5_Displace_Wigner_2D_AWG_Cam(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/866_cooling")

        self.setattr_argument("enable_rot_pulse", BooleanValue(False), group='rotation pulse excitation')
        self.setattr_argument("enable_img_readout", BooleanValue(False), group='rotation pulse excitation')
        self.setattr_argument(
            "freq_729_dp_rot",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "att_729_dp_rot",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "freq_729_sp_rot",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=0*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "amp_729_sp_rot",
            NumberValue(default=self.parameter_manager.get_param("AWG_amplitude/729_sp"), min=0, max=1,  precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "rot_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='rotation pulse excitation'
        )  
      

        # Motional State Readout (displacement operator) https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.125.043602 
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument("enable_dp_freq_compensation", BooleanValue(True))
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("SDF/amp_729_sp"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation"
        )
        
        self.setattr_argument(
            "amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("SDF/amp_729_sp_aux"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation"
        )

        # the scan parameter for the displacement operator
        self.setattr_argument(
            "beta_range_us",
            NumberValue(default=self.parameter_manager.get_param("SDF/beta_range_us"), min=0.001*us, max=300*us,  precision=8, unit='us'),
            tooltip="729 single pass amplitude",
            group='beta grid'
        )
        self.setattr_argument(
            "num_beta",
            NumberValue(default=self.parameter_manager.get_param("SDF/num_beta"), precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group='beta grid'
        )

        # general sampling parameters
        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        #self.setattr_argument("enable_collision_detection", BooleanValue(True))
        #self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold0"), precision=8),
            tooltip="Threshold PMT counts",
        )
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )

        #camera readout suite
        self.setattr_device("grabber0")
        self.setattr_argument(
            "cam_ROI_size",
            NumberValue(default=self.parameter_manager.get_param("readout/cam_ROI_size"), precision=0, step=1),
            tooltip="ROI size for camera",
            group="camera readout"
        )
        self.setattr_argument(
            "cam_threshold0",
            NumberValue(default=self.parameter_manager.get_param("readout/cam_threshold0"), precision=8),
            tooltip="threshold for camera",
            group="camera readout"
        )
        self.setattr_argument(
            "cam_threshold1",
            NumberValue(default=self.parameter_manager.get_param("readout/cam_threshold1"), precision=8),
            tooltip="threshold for camera",
            group="camera readout"
        )

    def prepare(self):
        # Create datasets
        num_freq_samples = self.num_beta*self.num_beta
        #self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("beta_index", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="beta_index",
            pen=False
        )

        #beta sampling
        self.beta=np.linspace(-self.beta_range_us,self.beta_range_us,self.num_beta).reshape((self.num_beta,1))+1.0j*np.linspace(-self.beta_range_us,self.beta_range_us, self.num_beta).reshape((1,self.num_beta))

        np.savetxt(get_config_dir()/'../repository/Vdp/beta.txt', self.beta)
        print(self.beta)
        #from beta to corresponding time & phase
        self.beta_time=np.zeros(self.beta.shape[0]*self.beta.shape[1],dtype=float)
        self.beta_phase=np.zeros(self.beta.shape[0]*self.beta.shape[1],dtype=float)
        
        #compute the time & phase based on the parameters
        idx=0
        for i in range(self.beta.shape[0]):
            for j in range(self.beta.shape[1]):
                self.beta_time[idx]=float(np.abs(self.beta[i][j]))
                self.beta_phase[idx]=(np.angle(self.beta[i][j])-np.pi/2)/(2*np.pi) #in unit of turns (2pi)
                
                idx+=1
        np.savetxt(get_config_dir()/'../repository/Vdp/beta_time.txt', self.beta_time)
        np.savetxt(get_config_dir()/'../repository/Vdp/beta_phase.txt', self.beta_phase)  

        if self.enable_dp_freq_compensation:
            self.setup_dp_att()


    def setup_dp_att(self):

        # Initialize empty lists to store x and y values
        freq_data =[]
        att_data = []
        # Read the file and parse each line
        with open(get_config_dir()/'../repository/Vdp/freq_att.txt', 'r') as f:
            for line in f:
               
                # Split the line by the comma and strip any extra whitespace
                x_val, y_val = line.strip().split(', ')
                freq_data.append(float(x_val))  # Convert x value to int
                att_data.append(float(y_val))  # Convert y value to float

        # Create the interpolation function
        interpolation_function = interp1d(freq_data, att_data, fill_value="extrapolate", kind='linear')

        self.att_729_dp =  float(interpolation_function(self.freq_729_dp/MHz))*dB

        print(self.att_729_dp)


    @rpc
    def send_exp_para(
        self,
        freq_RSB,
        freq_BSB,
        amp_RSB,
        amp_BSB,
        phase=0.0 
    ):
        
        if self.enable_rot_pulse:
            send_exp_para(["Rotation_Displacement_SDF", {
                    "rot_freq_sp": self.freq_729_sp_rot,
                    "rot_amp_sp": self.amp_729_sp_rot,
                    "rot_phase_sp": 90.0,
                    "freq_sp_RSB":   freq_RSB,
                    "freq_sp_BSB":   freq_BSB,
                    "amp_sp_RSB":  amp_RSB,
                    "amp_sp_BSB":   amp_BSB,
                    "phase": phase,
                    "if_imagine": self.enable_img_readout,
                    "num_loop":max(self.samples_per_time+100,100)
                }])
        else:
            send_exp_para(["Displacement_SDF", {
                    "freq_sp_RSB":   freq_RSB,
                    "freq_sp_BSB":   freq_BSB,
                    "amp_sp_RSB":  amp_RSB,
                    "amp_sp_BSB":   amp_BSB,
                    "phase": phase,
                    "num_loop":max(self.samples_per_time+100,100)
                }])  

    @kernel
    def run_729(self,time_729):
        self.ttl_awg_trigger.pulse(1*us)
        self.dds_729_dp.sw.on()
        delay(time_729)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)

    @kernel
    def exp_seq(self, beta_time, ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        # Cool
        self.seq.doppler_cool.run()
        #sideband cooling
        self.seq.sideband_cool.run()

        ################################################################################

        self.ttl_rf_switch_AWG_729SP.on()
        self.ttl_rf_switch_DDS_729SP.off()
        self.dds_729_sp.sw.off()
        #set 729 frequency only once (rotation frequency should be in principle the same)
        if ion_status_detect==2:
            self.dds_729_dp.set(self.freq_729_dp+self.freq_diff_dp) 
        else:
            self.dds_729_dp.set(self.freq_729_dp) 

        if self.enable_rot_pulse:
            self.dds_729_dp.set_att(self.att_729_dp_rot)
            self.run_729(self.rot_drive_time)

        delay(1*us)

        #displacement operation
        self.dds_729_dp.set_att(self.att_729_dp)
        #self.run_729(50*us)

        self.ttl_awg_trigger.pulse(1*us)
        self.dds_729_dp.sw.on()
        delay(150*us)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)


        # Prepare the Spin State to |down>
        self.seq.repump_854.run()
        
        #imaginary part (do a pi/2 before reading)
        if self.enable_img_readout:
            self.dds_729_dp.set_att(self.att_729_dp_rot)
            self.run_729(self.rot_drive_time)

        self.dds_729_dp.set_att(self.att_729_dp)
        #turn on AWG & double pass
        self.ttl_awg_trigger.pulse(1*us)
        self.dds_729_dp.sw.on()
        delay(beta_time)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    
    @kernel
    def cam_readout(self):
        # Readout
        cam_input=[0,0]
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_dp.set(self.frequency_397_resonance)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(5*us)
        
        self.ttl_camera_trigger.pulse(10*us)
        self.grabber0.input_mu(cam_input)
        delay(5*ms)

        ion_status=0
        ion_status = ion_status | 2 if cam_input[1]>self.cam_threshold1*self.cam_ROI_size**2  else ion_status
        ion_status = ion_status | 1 if cam_input[0]>self.cam_threshold0*self.cam_ROI_size**2  else ion_status
        
        return ion_status
    
    @kernel
    def cam_setup(self):
        #setup camera readout parameters
        self.grabber0.setup_roi(0, 0, 0, self.cam_ROI_size, self.cam_ROI_size)
        self.grabber0.setup_roi(1, 10, 10, 10+self.cam_ROI_size, 10+self.cam_ROI_size)
        self.grabber0.gate_roi(3)


    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        self.cam_setup()

        i=0
        while i < len(self.beta_time):
            total_thresh_count = 0

            # counter for repeating 
            sample_num=0


            delay(20*us)
            self.seq.ion_store.run()
            self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp,self.amp_729_sp_aux,self.amp_729_sp,self.beta_phase[i]*360)   
            delay(30*ms)
            # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
            ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
            ion_status=1
            ion_status_detect=1
            num_try_save_ion = 0 

            #detecting the initial position of the ion 
            while ion_status_detect_last!=1 and ion_status_detect_last!=2:
                delay(2*ms)
                self.seq.repump_854.run()
                delay(5*us)
                self.seq.doppler_cool.run()
                delay(5*us)
                ion_status_detect_last=self.cam_readout()
                self.seq.ion_store.run()
                delay(1*ms)
            
            if(ion_status_detect_last==3): 
                i=len(self.beta_time) 
                print("Maybe two bright ions????????????????????????????????????????????????????????????????")
            ion_status_detect== ion_status_detect_last
            delay(1*ms)

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(self.beta_time[i], ion_status_detect)
                    ################################################################################
                    ion_status=self.cam_readout()
                    self.seq.ion_store.run()
                    delay(50*us)
                    ################################################################################
                    if ion_status==0: #if the ion is not bright then it's possible it's being kicked
                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        ion_status_detect=self.cam_readout() #by the way get the position
                        self.seq.ion_store.run()
                        delay(20*us)
                    else: 
                        ion_status_detect=ion_status

                      
                    if (ion_status_detect==ion_status_detect_last): #ion shouldn't move
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
                        

                else:
                    self.seq.ion_store.run()
                    delay(0.2*s)
                    self.seq.doppler_cool.run()
                    ion_status_detect=self.cam_readout()
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


            self.experiment_data.append_list_dataset("beta_index", i)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                        float(total_thresh_count) / self.samples_per_time)
            
            i=i+1
            delay(6*ms)

        self.seq.ion_store.run()
        delay(5*us)