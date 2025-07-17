from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

import random

class A4_Vdp_SDF_2D(_ACFExperiment):

    def generate_random_float(self)->float:
        return random.random()

    def build(self): 
        
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        #the system parameters
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/854_dp") 
        self.add_arg_from_param("frequency/729_sp")

        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/854_dp")

        #VdP Hamiltonian (2nd red sideband + 1st blue sideband) ######################################################################
        self.setattr_argument(
            "Vdp_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_freq_729_dp_vib",
            NumberValue(default=self.parameter_manager.get_param("qubit/vib_freq"), min=0*MHz, max=10*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency for vib quanta",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_RSB",
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
            "Vdp_drive_att_854",
            NumberValue(default=16*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_drive_time_RSB",
            NumberValue(default=5*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB VdP Hamiltonian",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_time_BSB",
            NumberValue(default=5*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for BSB VdP Hamiltonian",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Repeat_Time",
            NumberValue(default=200, min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group='VdP Hamiltonian'
        )


        #readout parameters  ######################################################################
        self.setattr_argument(
            "num_beta",
            NumberValue(default=self.parameter_manager.get_param("SDF/num_beta"), min=0, max=1000, precision=0,step=1),
            tooltip="numbers of beta points",
            group='readout'
        )
        self.setattr_argument(
            "beta_range",
            NumberValue(default=10.0, min=0, max=1000, precision=6),
            tooltip="range of beta points",
            group='readout'
        )
        self.setattr_argument(
            "eta",
            NumberValue(default=0.134, min=0, max=10, precision=6),
            tooltip="lamb dicke parameter",
            group='readout'
        )
        self.setattr_argument( # the rabi frequency of both frequency components
            "rabi_freq",
            NumberValue(default=0.5, min=0, max=10, precision=6),
            tooltip="rabi frequency in MHz",
            group='readout'
        )

        # get the wigner function after trace out spin degrees of freedom  
        # displacement operation (may need to be a bit offseted due to stark shift)
        self.setattr_argument(
            "displace_freq_729_dp_resonance",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=50*MHz, max=120*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq"), min=50*MHz, max=120*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency 2",
            group='Displacement Operation'
        )
        # 
        self.setattr_argument(
            "displace_amp_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 douuble pass amplitude 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 single pass amplitude 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 single pass amplitude 2",
            group='Displacement Operation'
        )

        # self.setattr_argument(
        #     "carrier_readout",
        #     NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
        #     tooltip="729 double pass frequency for resonance",
        #     group='readout'
        # )
        # self.setattr_argument(
        #     "vib_readout", #this is value in double pass AOM, so if use for single pass AOM, we need to multiplied by 2
        #     NumberValue(default=self.parameter_manager.get_param("qubit/vib_freq"), min=0*MHz, max=10*MHz, unit="MHz", precision=6),
        #     tooltip="729 single pass frequency for vib quanta",
        #     group='readout'
        # )

        # self.setattr_argument(
        #     "att_729_dp_readout",
        #     NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
        #     tooltip="729 single pass amplitude",
        #     group='readout'
        # )

        # self.setattr_argument(
        #     "att_729_sp_readout",
        #     NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=6),
        #     tooltip="729 single pass amplitude",
        #     group='readout'
        # )



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
    

    @kernel(flags={"fast-math"})
    def wait_trigger(self, time_gating_mu, time_holdoff_mu):
        """
        Trigger off a rising edge of the AC line.
        Times out if no edges are detected.
        Arguments:
            time_gating_mu  (int)   : the maximum waiting time (in machine units) for the trigger signal.
            time_holdoff_mu (int64) : the holdoff time (in machine units)
        Returns:
                            (int64) : the input time of the trigger signal.
        """ 

        gate_open_mu = now_mu() #current time on the timeline (int kernel)
                                #self.core.get_rtio_counter_mu (hardware time cursor)
        self.ttl_linetrigger_input._set_sensitivity(1)
    
        t_trig_mu = 0
        while True:
            t_trig_mu = self.ttl_linetrigger_input.timestamp_mu(gate_open_mu + time_gating_mu)
            if t_trig_mu < 0 or t_trig_mu >= gate_open_mu:
                break
        
        #self.trigger.count(self.core.get_rtio_counter_mu() + time_holdoff_mu) #drain the FIFO to avoid input overflow

        at_mu(self.core.get_rtio_counter_mu()+2000)

        self.ttl_linetrigger_input._set_sensitivity(0)

        at_mu(self.core.get_rtio_counter_mu() + time_holdoff_mu) #set the current time (software) to be the same as the current hardware timeline + a shift in time

        # if t_trig_mu < 0:
        #     raise Exception("MissingTrigger")

        return t_trig_mu

    @kernel  
    def init_device(self):
        # Init devices
        self.core.break_realtime()
        self.dds_397_dp.init()
        self.dds_397_far_detuned.init()
        self.dds_866_dp.init()
        self.dds_729_dp.init()
        self.dds_729_sp.init()
        self.dds_729_sp_aux.init()
        self.dds_854_dp.init()
        
        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(1*ms)

        # Set frequencies
        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_729_sp.set(self.frequency_729_sp)
        delay(1*ms)

        # Turn off the dds
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_397_dp.sw.off()
        self.dds_397_far_detuned.cfg_sw(False)
        self.dds_rf_g_qubit.sw.off()
    
    
    @kernel
    def pulse_single_tone(self, freq_729_dp, amp_729_dp, relative_phase, drive_time):
        
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_729_dp.set(freq_729_dp, phase=relative_phase)
        self.dds_729_dp.set_att(amp_729_dp)
        delay(1*us)

        #turn on 729
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()

        delay(drive_time)

        self.dds_729_dp.sw.off()
    
    @kernel
    def pulse_displacement(self, relative_phase, drive_time):

        #set frequency 
        self.dds_729_sp.set(self.frequency_729_sp+self.vib_readout*2, phase=relative_phase)
        self.dds_729_sp_aux.set(self.frequency_729_sp-self.vib_readout*2, phase=0.0)

        #set attenuation
        self.dds_729_sp.set_att(self.att_729_sp_readout)
        self.dds_729_sp_aux.set_att(self.att_729_sp_readout)

        self.dds_729_dp.set_att(self.att_729_dp_readout)
        self.dds_729_dp.set(self.carrier_readout)

        delay(5*us)

        #turn on 729
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.on()

        delay(drive_time)

        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
    
    @kernel
    def Vdp_Evolve(self):
        
        #loss in the upper spin state
        self.dds_854_dp.set(self.frequency_854_dp)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set_att(self.Vdp_drive_att_854)
        self.dds_866_dp.set_att(self.attenuation_866)
        delay(5*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(5*us)
        

        for j in range(self.Repeat_Time):
            
            # 2 order red sideband
            self.pulse_single_tone(self.Vdp_freq_729_dp+2*self.Vdp_freq_729_dp_vib, self.Vdp_drive_att_RSB, self.Vdp_drive_time_RSB, self.rand_phase1[j])
            delay(1*us)

            # 1 order blue sideband
            self.pulse_single_tone(self.Vdp_freq_729_dp- self.Vdp_freq_729_dp_vib, self.Vdp_drive_att_BSB, self.Vdp_drive_time_BSB, self.rand_phase2[j])
            delay(1*us)

        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()


    def prepare(self):
        #set up fitting dataset
        # self.fitting_func.setup(len(self.scan_rabi_t.sequence))

        # Create datasets
        self.num_samples = int(self.num_beta*self.num_beta)
        self.experiment_data.set_nd_dataset("pmt_counts", [self.num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("index", self.num_samples, broadcast=True)

        #Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="index",
            pen=False
        )

        self.rand_phase1= [ self.generate_random_float() for i in range(self.Repeat_Time)]
        self.rand_phase2= [ self.generate_random_float() for i in range(self.Repeat_Time)]

        self.beta_phase = [float(0.0)] * self.num_samples
        self.beta_time  = [float(0.0)] * self.num_samples


        beta=np.linspace(-self.beta_range, self.beta_range, self.num_beta)

        for i in range(self.num_beta):
            for j in range(self.num_beta):
                beta_complex_abs=float(np.abs(beta[i]+1.0j*beta[j]))
                beta_complex_angle=float(np.angle(beta[i]+1.0j*beta[j]))
                self.beta_time[i*self.num_beta+j]=beta_complex_abs/4.0/self.rabi_freq
                self.beta_phase[i*self.num_beta+j]=beta_complex_angle-np.pi/2
       

    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()

        self.init_device()

        delay(1*ms)

        for i in range(self.num_samples): 
            total_thresh_count = 0
            total_pmt_counts = 0

            sample_num=0

            while sample_num<self.samples_per_time:

                #line trigger 
                flag = self.wait_trigger(self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) )
                if flag <0 : continue
                delay(50*us)
                
                # doppler cooling and state preparation
                self.seq.doppler_cool.run()
                delay(5*us)
                self.dds_397_dp.set(self.frequency_397_cooling)
                self.dds_397_dp.set_att(self.attenuation_397) 
                delay(10*us)
                self.seq.sideband_cool.run()
                delay(10*us)

                #Vdp Evolution
                self.Vdp_Evolve()
                delay(10*us)

                #post selection
                num_pmt_pulses1=self.seq.readout_397.run()
                if num_pmt_pulses1<self.threshold_pmt_count: # in the upper state, then skip this datapoint
                   continue
                
                #apply SDF
                self.pulse_displacement(self.beta_phase[i], self.beta_time[i]*us)

                #readout
                delay(10*us)
                num_pmt_pulses=self.seq.readout_397.run()

                delay(10*us)

                self.dds_397_dp.set(self.frequency_397_cooling)
                self.dds_397_dp.set_att(self.attenuation_397) 
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()

                delay(10*us)
                self.seq.repump_854.run()
                delay(10*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses

                sample_num+=1

                delay(3*ms)

            

            self.experiment_data.append_list_dataset("index", i)

            
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)

            delay(30*ms)

        self.seq.ion_store.run()
    

