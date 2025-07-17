from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

from awg_utils.transmitter import send_exp_para

from utils_func.stark_D import stark_shift


class RabiTimeScan_AWG(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.rabi.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)
        
        # self.setattr_argument("enable_pi_pulse", BooleanValue(False), group='Pi pulse excitation')
        # self.setattr_argument(
        #     "PI_freq_729",
        #     NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=350*MHz, unit="MHz", precision=8),
        #     tooltip="729 double pass frequency for resonance",
        #     group='Pi pulse excitation'
        # )
        # self.setattr_argument(
        #     "PI_amp_729_pi",
        #     NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
        #     tooltip="729 double pass amplitude for resonance",
        #     group='Pi pulse excitation'
        # )
        # self.setattr_argument(
        #     "PI_drive_time",
        #     NumberValue(default=0.1*us, min=0.*us, max=1000*us, unit='us', precision=8),
        #     tooltip="Drive time for pi excitation",
        #     group='Pi pulse excitation'
        # )

        
        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=60*us,
                    npoints=30
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "Rabi_freq",
            NumberValue(default=0.0, min=0.0*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=8*dB, max=31*dB, unit="dB", precision=8),
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
            NumberValue(default=self.parameter_manager.get_param("AWG_amplitude/729_sp"), min=0, max=1,  precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )



        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool2mode", "opticalpumping"], default="sidebandcool"))
        
        self.setattr_argument("enable_collision_detection", BooleanValue(True))
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )



    @kernel
    def rabi_AWG(self,pulse_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)

        
        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()

        self.ttl_awg_trigger.pulse(1*us)
        if pulse_time>10*ns:
            self.dds_729_dp.sw.on()
            delay(pulse_time)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)

        
        # self.ttl_rf_switch_AWG_729SP.off()
        # self.ttl_rf_switch_DDS_729SP.on()

        
    @rpc(flags={'async'})
    def send_exp_para(self):
        send_exp_para(["SingleTone",{"freq": self.freq_729_sp,"amp": self.amp_729_sp, "num_loop":max(self.samples_per_time+100,100)}])
  
    
    def prepare(self):
        self.fitting_func.setup(len(self.scan_rabi_t.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_freq_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
            fit_data_name='fit_signal'
        )

        # self.freq_729_dp=self.freq_729_dp-stark_shift(self.parameter_manager, self.freq_729_dp, self.freq_729_sp, self.Rabi_freq)/2.0
        # print(self.freq_729_dp)


    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()

        time_i=0
        while time_i < len(self.scan_rabi_t.sequence):
        
            #time 
            rabi_t=self.scan_rabi_t.sequence[time_i]
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            # Cool
            self.seq.ion_store.run()
            self.send_exp_para()

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
                

                    #854 repump
                    self.seq.repump_854.run()
                    
                    #  Cool
                    self.seq.doppler_cool.run()
                    if self.cooling_option == "sidebandcool":
                        self.seq.sideband_cool.run()
                    elif self.cooling_option == "sidebandcool2mode":
                        self.seq.sideband_cool_2mode.run()
                    else:
                        self.seq.op_pump.run()
                    delay(5*us)
                    
                    # rabi 
                    self.rabi_AWG(rabi_t, self.freq_729_dp, self.att_729_dp)

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
                        
                        self.core.break_realtime()
                            
                    if is_ion_good:
                        sample_num+=1
                        # Update dataset
                        self.experiment_data.insert_nd_dataset("pmt_counts",
                                                    [time_i, sample_num],
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
                        time_i=len(self.scan_rabi_t.sequence)+100
                        sample_num+=10000
                        break
                    delay(2*ms)

            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            time_i+=1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()
    
    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        try:
            params=self.fitting_func.fit(rabi_time, rabi_PMT)

            fitted_amplitude, fitted_omega, fitted_phase, fitted_tau, fitted_offset = params

            fitted_frequency = fitted_omega / (2 * np.pi)

            # with self.interactive(f"Pi: time {fitted_frequency:.4f}") as inter:
            #        pass
        except Exception:
            pass