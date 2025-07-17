from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

import random

from artiq.coredevice.ad9910 import PHASE_MODE_ABSOLUTE, PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para

class A4_Displace_Vdp_Wigner_2D_AWG(_ACFExperiment):

    def generate_random_float(self)->float:
        return random.random()

    def build(self): 
        
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()


        #VdP Hamiltonian (2nd red sideband + 1st blue sideband) ######################################################################
        self.setattr_argument(
            "Vdp_freq_729_BSB_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")-self.parameter_manager.get_param("qubit/vib_freq"), min=180*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_freq_729_2RSB_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=180*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_2RSB",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_BSB",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_drive_freq_854",
            NumberValue(default=self.parameter_manager.get_param("frequency/854_dp"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_freq_866",
            NumberValue(default=self.parameter_manager.get_param("frequency/866_cooling"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_drive_att_854",
            NumberValue(default=16*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_866",
            NumberValue(default=self.parameter_manager.get_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_drive_time_2RSB",
            NumberValue(default=self.parameter_manager.get_param("VdP1mode/Vdp_drive_time_2RSB"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB VdP Hamiltonian",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_time_BSB",
            NumberValue(default=self.parameter_manager.get_param("VdP1mode/Vdp_drive_time_BSB"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for BSB VdP Hamiltonian",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Repeat_Time",
            NumberValue(default=200, min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group='VdP Hamiltonian'
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
            NumberValue(default=80*MHz-2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=80*MHz+2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
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

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        self.setattr_argument("enable_collision_detection", BooleanValue(True))

    @kernel
    def repump(self):
        delay(2*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(5*us)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(2*us)

    @kernel
    def Vdp_Evolve(self):

        #loss in the upper spin state
        self.dds_854_dp.set(self.Vdp_drive_freq_854)
        self.dds_866_dp.set(self.Vdp_drive_freq_866)
        self.dds_854_dp.set_att(self.Vdp_drive_att_854)
        self.dds_866_dp.set_att(self.Vdp_drive_att_866)


        self.dds_729_sp.set(self.Vdp_freq_729_sp)
        self.dds_729_sp.set_att(self.Vdp_att_729_sp)
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()

        delay(10*us)

        for i in range(self.Repeat_Time):
            #generate random phase
            # 2 order red sideband

            self.dds_729_dp.set(self.Vdp_freq_729_2RSB_dp, phase=0.)
            self.dds_729_dp.set_att(self.Vdp_drive_att_2RSB)
            self.dds_729_dp.sw.on()
            delay(self.Vdp_drive_time_2RSB)
            self.dds_729_dp.sw.off()
            # self.seq.rabi.run(
            #     self.Vdp_drive_time_2RSB,
            #     self.Vdp_freq_729_2RSB_dp,
            #     self.Vdp_freq_729_sp,
            #     self.Vdp_drive_att_2RSB,
            #     self.Vdp_att_729_sp,
            #     self.rand_phase1[i]
            # )
            self.repump()
            #self.seq.op_pump_sigma.run()

            self.dds_729_dp.set(self.Vdp_freq_729_BSB_dp, phase=0.)
            self.dds_729_dp.set_att(self.Vdp_drive_att_BSB)
            self.dds_729_dp.sw.on()
            delay(self.Vdp_drive_time_BSB)
            self.dds_729_dp.sw.off()
            
            # 1 order blue sideband
            # self.seq.rabi.run(
            #     self.Vdp_drive_time_BSB,
            #     self.Vdp_freq_729_BSB_dp,
            #     self.Vdp_freq_729_sp,
            #     self.Vdp_drive_att_2RSB,
            #     self.Vdp_att_729_sp,
            #     self.rand_phase2[i]
            # )
            
            delay(2*us)
            #self.seq.op_pump_sigma.run()
        
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        delay(5*us)


    def prepare(self):
        #set up fitting dataset
        # self.fitting_func.setup(len(self.scan_rabi_t.sequence))

        # Create datasets
        self.num_samples = int(self.num_beta*self.num_beta)
        self.experiment_data.set_nd_dataset("pmt_counts", [self.num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("beta_index", self.num_samples, broadcast=True)

        #Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="beta_index",
            pen=False
        )

        self.rand_phase1= [ self.generate_random_float() for i in range(self.Repeat_Time)]
        self.rand_phase2= [ self.generate_random_float() for i in range(self.Repeat_Time)]

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
                self.beta_phase[idx]-=np.floor(self.beta_phase[idx])
                idx+=1
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


    @rpc(flags={'async'})
    def send_exp_para(
        self,
        freq_RSB,
        freq_BSB,
        amp_RSB,
        amp_BSB,
        phase
    ):
        send_exp_para(["Displacement_SDF", {
                    "freq_sp_RSB":   freq_RSB,
                    "freq_sp_BSB":   freq_BSB,
                    "amp_sp_RSB":  amp_RSB,
                    "amp_sp_BSB":   amp_BSB,
                    "phase": phase,
                    "num_loop":max(self.samples_per_time+100,100)
                }])  
        
    @kernel
    def rabi_AWG(self, pulse_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)

        
        self.ttl_rf_switch_AWG_729SP.on()
        self.ttl_rf_switch_DDS_729SP.off()
        self.ttl_awg_trigger.pulse(1*us)
            
        self.dds_729_sp.sw.off()
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        delay(2*us)

        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        i=0
        while i < self.num_samples:
            total_thresh_count = 0
            total_pmt_counts = 0

            # counter for repeating 
            sample_num=0

            delay(200*us)
            self.seq.ion_store.run()
            self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp, self.amp_729_sp_aux, self.amp_729_sp,self.beta_phase[i]*360)     
            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(50*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue

            while sample_num<self.samples_per_time:
                if is_ion_good:

                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                   
                    delay(50*us)

                    #854 repump
                    self.seq.repump_854.run()
                    #  Cool
                    self.seq.doppler_cool.run()
                    #sideband cooling
                    self.seq.sideband_cool.run()

                    #apply SDF
                    self.rabi_AWG(10*us,self.freq_729_dp,self.att_729_dp)

                    #Vdp Evolution
                    self.Vdp_Evolve()
                    delay(5*us)

                    # Prepare the Spin State to |down>
                    self.seq.repump_854.run()

                    #apply SDF
                    self.rabi_AWG(self.beta_time[i],self.freq_729_dp,self.att_729_dp)

                    # Readout
                    num_pmt_pulses=self.seq.readout_397.run()

                    if num_pmt_pulses < self.threshold_pmt_count and self.enable_collision_detection:

                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        num_pmt_pulses_detect=self.seq.readout_397.run()
                        self.seq.ion_store.run()
                        delay(20*us)

                        if num_pmt_pulses_detect < self.threshold_pmt_count:
                            is_ion_good = False
                            
                    if is_ion_good:
                        sample_num+=1
                        # Update dataset
                        self.experiment_data.insert_nd_dataset("pmt_counts",
                                                    [i, sample_num],
                                                    num_pmt_pulses)
                        
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        total_pmt_counts += num_pmt_pulses

                        delay(3*ms)

                else:
                    self.seq.ion_store.run()
                    delay(1*s)
                    num_pmt_pulses_detect=self.seq.readout_397.run()
                    if num_pmt_pulses_detect >= self.threshold_pmt_count:
                        is_ion_good = True
                        num_try_save_ion = 0
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>50):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break



            self.experiment_data.append_list_dataset("beta_index", i)

            
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            i=i+1
            delay(5*ms)

        self.seq.ion_store.run()
    

