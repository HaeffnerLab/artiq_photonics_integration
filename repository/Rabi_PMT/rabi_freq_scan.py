from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *


class RabiFreqScan(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        # self.seq.op_pump.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'Lorentzian', -999)

        self.setattr_argument("enable_pi_pulse", BooleanValue(False), group='Pi pulse excitation')
        self.setattr_argument(
            "freq_729_dp_pi",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "att_729_dp_pi",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=10.06*us, min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )


        
        self.setattr_argument(
            "scan_freq_729_dp",
            Scannable(
                default=RangeScan(
                   start=self.parameter_manager.get_param("qubit/S1_2_D3_2")-0.24*MHz,
                    stop=self.parameter_manager.get_param("qubit/S1_2_D3_2")+0.24*MHz,
                    npoints=50
                ),
                global_min=150*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "rabi_t",
            NumberValue(default=8.1*us, min=0.0*us, max=10000*us, unit="us", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=12.5*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        self.setattr_argument("enable_sideband_cool", BooleanValue(False))
        self.setattr_argument("enable_collision_detection", BooleanValue(True))  
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        

    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_729_dp.sequence)) 

    
    # @kernel(flags={"fast-math"})
    # def wait_trigger(self, time_gating_mu, time_holdoff_mu):
    #     """
    #     Trigger off a rising edge of the AC line.
    #     Times out if no edges are detected.
    #     Arguments:
    #         time_gating_mu  (int)   : the maximum waiting time (in machine units) for the trigger signal.
    #         time_holdoff_mu (int64) : the holdoff time (in machine units)
    #     Returns:
    #                         (int64) : the input time of the trigger signal.
    #     """ 

    #     gate_open_mu = now_mu() #current time on the timeline (int kernel)
    #                             #self.core.get_rtio_counter_mu (hardware time cursor)
    #     self.ttl_linetrigger_input._set_sensitivity(1)
    
    #     t_trig_mu = 0
    #     while True:
    #         t_trig_mu = self.ttl_linetrigger_input.timestamp_mu(gate_open_mu + time_gating_mu)
    #         if t_trig_mu < 0 or t_trig_mu >= gate_open_mu:
    #             break
        
    #     #self.trigger.count(self.core.get_rtio_counter_mu() + time_holdoff_mu) #drain the FIFO to avoid input overflow

    #     at_mu(self.core.get_rtio_counter_mu()+2000)

    #     self.ttl_linetrigger_input._set_sensitivity(0)

    #     at_mu(self.core.get_rtio_counter_mu() + time_holdoff_mu) #set the current time (software) to be the same as the current hardware timeline + a shift in time

    #     # if t_trig_mu < 0:
    #     #     raise Exception("MissingTrigger")

    #     return t_trig_mu


    # @kernel
    # def rabi(self,pulse_time,frequency, phase:float=0.0):

    #     # in the register, the phase is pow_/65536
    #     # in turns (meaning how many 2pi, 1 turn means 2pi)

    #     self.dds_729_dp.set(frequency, phase=phase)
    #     self.dds_729_dp.set_att(self.amp_729_pi)
    #     self.dds_729_dp.sw.on()
    #     delay(pulse_time)
    #     self.dds_729_dp.sw.off()
        
    
  
    def prepare(self):
         # Create datasets
        num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_freq], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq_samples, broadcast=True)

        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=True,
            fit_data_name='fit_signal'
        )



    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        freq_i = 0
        while freq_i < len(self.scan_freq_729_dp.sequence):

            freq_729_dp=self.scan_freq_729_dp.sequence[freq_i]
            self.core.break_realtime()
            delay(100*us)
            self.dds_729_dp.set(freq_729_dp)

            #PMT
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            self.seq.ion_store.run()
            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            delay(200*us)

            while sample_num<self.samples_per_freq:
                if is_ion_good:
                    # #line trigger
                    # if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(2*ms) ) <0 : 
                    #     continue
                    
                    # Ensure timeline is safely ahead before SPI-heavy repump sequence
                    self.core.break_realtime()
                    delay(1*ms)
                    #854 repump
                    self.seq.repump_854.run()
                    # Cool
                    self.seq.doppler_cool.run()

                    # if self.enable_sideband_cool:
                    #     self.seq.sideband_cool.run()
                    # else:
                    #     self.seq.op_pump.run()
                    # delay(5*us)
                    
                    # if self.enable_pi_pulse:
                    #     #self.rabi(self.PI_drive_time, self.freq_729_pi,0.0)
                    #     self.seq.rabi.run(self.PI_drive_time,
                    #                     self.freq_729_dp_pi,
                    #                     self.att_729_dp_pi,
                    #         )

                    # Attempt Rabi flop
                    self.seq.rabi.run(self.rabi_t,
                                    freq_729_dp,
                                    self.att_729_dp,
                                    self.att_729_dp
                    )

                    #qubit readout
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
                                                    [freq_i, sample_num],
                                                    num_pmt_pulses)
                        
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        total_pmt_counts += num_pmt_pulses

                        delay(2*ms)
                else:
                    self.seq.ion_store.run()
                    delay(0.2*s)
                    self.seq.doppler_cool.run()
                    num_pmt_pulses_detect=self.seq.readout_397.run()
                    if num_pmt_pulses_detect >= self.threshold_pmt_count:
                        is_ion_good = True
                        num_try_save_ion = 0
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>60):
                        print("Ion Lost!!!")
                        time_i=len(self.scan_freq_729_dp.sequence)+100
                        sample_num+=10000
                        break
                     
            
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_729_dp / MHz)
            if not self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          -float(total_pmt_counts) / self.samples_per_freq)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
            
            delay(5*ms)

        self.seq.ion_store.run()

    def analyze(self):

            
        freq=self.get_dataset("frequencies_MHz")
        PMT_count=self.get_dataset('pmt_counts_avg')

        peak=self.fitting_func.fit(freq, PMT_count)[1]


        with self.interactive("Ca+ line") as inter:
            inter.setattr_argument(
                "Ca_line", 
                EnumerationValue(["Sm1_2_Dm1_2", "Sm1_2_Dm5_2", "nothing"]
                                 , default="Sm1_2_Dm1_2")
            )
        
        if inter.Ca_line == "Sm1_2_Dm5_2":
            self.parameter_manager.set_param(
                "qubit/Sm1_2_Dm5_2",
                peak*1e6,
                "MHz"
            )
        elif inter.Ca_line == "Sm1_2_Dm1_2":
            self.parameter_manager.set_param(
                "qubit/Sm1_2_Dm1_2",
                peak*1e6,
                "MHz"
            )
