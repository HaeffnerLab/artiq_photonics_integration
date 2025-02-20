from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

from awg_utils.transmitter import send_exp_para

class RabiFreqScan_AWG(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
        self.seq.op_pump_sigma.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'Lorentzian', -999)


        # self.add_arg_from_param("frequency/729_sp")
        # self.add_arg_from_param("attenuation/729_dp")
        # self.add_arg_from_param("attenuation/729_sp")

        # self.setattr_argument("enable_pi_pulse", BooleanValue(False), group='Pi pulse excitation')
        # self.setattr_argument(
        #     "PI_freq_729_dp",
        #     NumberValue(default=233.705*MHz, min=200*MHz, max=250*MHz, unit="MHz", precision=8),
        #     tooltip="729 double pass frequency for resonance",
        #     group='Pi pulse excitation'
        # )
        # self.setattr_argument(
        #     "PI_att_729_dp",
        #     NumberValue(default=20*dB, min=10*dB, max=30*dB, unit="dB", precision=8),
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
            "att_729_dp",
            NumberValue(default=30*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
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
            NumberValue(default=0.15, min=0, max=1,  precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=100*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="rabi"
        )

        
        self.setattr_argument(
            "scan_freq_729_dp",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")-0.003*MHz,
                    stop=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")+0.003*MHz,
                    npoints=40
                ),
                global_min=150*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=8
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool", "sidebandcool2mode", "opticalpumping","opticalpumping_sigma", "nothing"], default="opticalpumping"))
        self.setattr_argument("enable_collision_detection", BooleanValue(True))
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )


        #camera readout suite
        # self.setattr_device("grabber0")
        # self.setattr_argument("use_camera_readout", BooleanValue(alse))
        # self.setattr_argument(
        #     "cam_ROI_size",
        #     NumberValue(default=self.parameter_manager.get_param("readout/cam_ROI_size"), precision=0, step=1),
        #     tooltip="ROI size for camera",
        #     group="camera readout"
        # )
        # self.setattr_argument(
        #     "cam_threshold",
        #     NumberValue(default=self.parameter_manager.get_param("readout/cam_threshold"), precision=0, step=1),
        #     tooltip="threshold for camera",
        #     group="camera readout"
        # )    
        

    
    def prepare(self):
         # Create datasets
        num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_freq])
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq_samples, broadcast=True)

        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)
        self.fitting_func.setup(len(self.scan_freq_729_dp.sequence)) 
        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=True,
            fit_data_name='fit_signal'
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
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        delay(2*us)
        self.ttl_awg_trigger.pulse(1*us)

        
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @rpc(flags={'async'})
    def send_exp_para(self)->None:
        send_exp_para(["SingleTone",{"freq": self.freq_729_sp,"amp": self.amp_729_sp, "num_loop":max(self.samples_per_freq+100,100)}])
  

    @kernel
    def run(self):

        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()
        delay(50*us)

        freq_i = 0
        while freq_i < len(self.scan_freq_729_dp.sequence):

            freq_729_dp=self.scan_freq_729_dp.sequence[freq_i]

            self.dds_729_dp.set(freq_729_dp)

            #PMT
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            # Cool
            self.seq.ion_store.run()
            self.send_exp_para()

            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            
            
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue


            while sample_num<self.samples_per_freq:

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
                    elif self.cooling_option =="opticalpumping":
                        self.seq.op_pump.run()
                    elif self.cooling_option == "opticalpumping_sigma":
                        self.seq.op_pump_sigma.run()
                    delay(5*us)
                    
                    
                    # if self.enable_pi_pulse:
                    #     #self.rabi(self.PI_drive_time, self.freq_729_pi,0.0)
                    #     self.seq.rabi.run(self.PI_drive_time,
                    #                 self.PI_freq_729_dp,
                    #                 self.frequency_729_sp,
                    #                 self.PI_att_729_dp,
                    #                 self.attenuation_729_sp
                    #     )

                    # rabi 
                    self.rabi_AWG(self.rabi_t, freq_729_dp, self.att_729_dp)

                    #qubit readout
                    num_pmt_pulses=self.seq.readout_397.run()

                    if num_pmt_pulses < self.threshold_pmt_count  and self.enable_collision_detection:

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
                        freq_i=+100000
                        sample_num+=10000
                        break
                    delay(2*ms)
                     
            
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_729_dp / MHz)
            if not self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          -float(total_pmt_counts) / self.samples_per_freq)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
            
            self.core.break_realtime()

        self.seq.ion_store.run()


    def analyze(self):

            
        freq=self.get_dataset("frequencies_MHz")
        PMT_count=self.get_dataset('pmt_counts_avg')

        peak=self.fitting_func.fit(freq, PMT_count)[1]


        with self.interactive("Ca+ line") as inter:
            inter.setattr_argument(
                "Ca_line", 
                EnumerationValue(["Sm1_2_Dm1_2", "Sm1_2_Dm5_2", "nothing"]
                                 , default="Sm1_2_Dm5_2")
            )
        
        if inter.Ca_line == "Sm1_2_Dm5_2":

            if np.abs(self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")/1e6-peak)<1:
                
                self.parameter_manager.set_param(
                    "qubit/Sm1_2_Dm5_2",
                    peak*1e6,
                    "MHz"
                )
        elif inter.Ca_line == "Sm1_2_Dm1_2":
            if np.abs(self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2")/1e6-peak)<1:
                self.parameter_manager.set_param(
                    "qubit/Sm1_2_Dm1_2",
                    peak*1e6,
                    "MHz"
                )

    