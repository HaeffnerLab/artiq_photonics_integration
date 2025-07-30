from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class RFRabiFreqScan(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("readout/pmt_sampling_time")


        #electron shelving to detect the final state
        self.setattr_argument(
            "freq_729_pi",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse shelving'
        )
        self.setattr_argument(
            "amp_729_pi",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse shelving'
        )
        self.setattr_argument(
            "pi_drive_time",
            NumberValue(default=2.6*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for pi excitation",
            group='Pi pulse shelving'
        )

        self.setattr_argument(
            "repump_854_time",
            NumberValue(default=100*us, min=5*us, max=1*ms, unit="us",precision=6),
        )


        self.setattr_argument(
            "rabi_t",
            NumberValue(default=500*us, min=0*us, max=5*ms, unit="us",precision=6)
        )


        self.setattr_argument(
            "amp_RF",
            NumberValue(default=15*dB, min=10*dB, max=30*dB, unit="dB", precision=6),
            tooltip="RF amplitude for resonance"
        )


        self.setattr_argument(
            "scan_freq_RF",
            Scannable(
                default=RangeScan(
                    start=8.955*MHz,
                    stop=8.965*MHz,
                    npoints=50
                ),
                global_min=1*MHz,
                global_max=20*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        self.setattr_argument("enable_sideband_cool", BooleanValue(False))
        self.setattr_argument("enable_thresholding", BooleanValue(False))
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
        self.dds_854_dp.init()
        delay(40*us)
        
        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(40*us)

        # Set frequencies
        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_sp_aux.set(self.frequency_729_sp)
        self.dds_854_dp.set(self.frequency_854_dp)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        delay(40*us)

        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_397_dp.sw.off()
        self.dds_397_far_detuned.sw.off()
        self.dds_rf_g_qubit.sw.off()

    @kernel
    def rabi(self,pulse_time,frequency, phase:float=0.0):

        self.dds_729_dp.set(frequency, phase=phase)
        self.dds_729_dp.set_att(self.amp_729_pi)
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        # self.dds_729_sp.sw.off()

    @kernel
    def rabi_RF(self, pulse_time, frequency, phase:float=0.0):


        self.dds_rf_g_qubit.set(frequency, phase=phase)
        self.dds_rf_g_qubit.set_att(self.amp_RF)

        self.dds_rf_g_qubit.sw.on()
        delay(pulse_time)
        self.dds_rf_g_qubit.sw.off()
        

    @kernel
    def run(self):

        self.setup_run()

        self.init_device()
    
        # Create datasets
        num_freq_samples = len(self.scan_freq_RF.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_freq], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=True
        )

        self.core.break_realtime()

        freq_i = 0
        for freq_RF in self.scan_freq_RF.sequence: # scan the frequency

            self.dds_rf_g_qubit.set(freq_RF)
            self.dds_rf_g_qubit.set_att(self.amp_RF)

            total_thresh_count = 0
            total_pmt_counts = 0

            sample_num=0

            while sample_num<self.samples_per_freq:
            
                flag = self.wait_trigger(self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) )
                if flag <0 : continue
                sample_num+=1

                delay(50*us)
                
                self.dds_854_dp.sw.off()
                self.dds_729_dp.sw.off()
                self.dds_729_sp.sw.off()
                self.dds_397_dp.sw.off()
                self.dds_854_dp.sw.off()
                delay(1*ms)

                #854 repump
                self.seq.repump_854.run()
                delay(10*us)
                #  Cool
                self.seq.doppler_cool.run()
                delay(5*us)
                self.seq.sideband_cool.run()
                delay(5*us)


                self.rabi_RF(self.rabi_t, freq_RF,0.0)

                delay(10*us)
                
                self.rabi(self.pi_drive_time, self.freq_729_pi,0.0)        

                delay(10*us)

                # Collect counts
                # leave 866 at cooling frequency
                self.dds_397_dp.set(self.frequency_397_resonance)
                self.dds_397_dp.set_att(self.attenuation_397)
                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_866_dp.set_att(self.attenuation_866)

                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()

                delay(5*us)

                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                )

                delay(30*us)

                self.dds_397_dp.set(self.frequency_397_cooling)
                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                self.dds_397_far_detuned.sw.on()
                
                delay(20*us)

                # 854 repump
                self.seq.repump_854.run()
                delay(10*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [freq_i, sample_num],
                                            num_pmt_pulses)
                                            
                #update the total count & thresholded events
                total_pmt_counts += num_pmt_pulses
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(2*ms)
                     
            
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_RF / MHz)
            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          -float(total_pmt_counts) / self.samples_per_freq)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
            delay(40*ms)



    