from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *


class RamanAtt397SigmaScan_SBC(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
        self.seq.sideband_Raman.add_arguments_to_gui()


        self.setup_fit(fitting_func, 'Sin' ,-1)

        self.setattr_argument("enable_pi_pulse", BooleanValue(True), group='Pi pulse excitation')
        self.setattr_argument(
            "freq_729_dp_pi",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "att_729_dp_pi",
            NumberValue(default=self.parameter_manager.get_param("pi_time/att_729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "freq_729_sp_pi",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "att_729_sp_pi",
            NumberValue(default=self.parameter_manager.get_param("pi_time/att_729_sp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=self.parameter_manager.get_param("pi_time/pi_time"), min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )


        #red sideband
        self.setattr_argument(
            "RSB_freq_Raman1",
            NumberValue(default=self.parameter_manager.get_param("frequency/Raman1")-self.parameter_manager.get_param("sideband_Raman/vib_freq1"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Red_Side_Band'
        )
        self.setattr_argument(
            "RSB_drive_time",
            NumberValue(default=200*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB excitation",
            group='Red_Side_Band'
        )
        
        
        self.setattr_argument(
            "scan_att_397_sigma",
            Scannable(
                default=RangeScan(
                    start=15*dB,
                    stop=30*dB,
                    npoints=30
                ),
                global_min=10*dB,
                global_max=31.5*dB,
                global_step=0.1*dB,
                unit="dB"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )

        self.setattr_argument(
            "freq_Raman1",
            NumberValue(default=self.parameter_manager.get_param("frequency/Raman1"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_Raman1",
            NumberValue(default=self.parameter_manager.get_param("attenuation/Raman1"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_Raman2",
            NumberValue(default=self.parameter_manager.get_param("frequency/Raman2"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_Raman2",
            NumberValue(default=self.parameter_manager.get_param("attenuation/Raman2"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        self.setattr_argument(
            "amp_Raman1",
            NumberValue(default=1., min=0.0, max=1.0, precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        self.setattr_argument(
            "amp_Raman2",
            NumberValue(default=1., min=0.0, max=1.0, precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        self.setattr_argument("enable_sideband_cool", BooleanValue(True))
        #self.setattr_argument("enable_Raman_sideband_cool", BooleanValue(False))
        self.setattr_argument("enable_collision_detection", BooleanValue(True))  
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        
    def prepare(self):
        self.fitting_func.setup(len(self.scan_att_397_sigma.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_att_397_sigma.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation", num_freq_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="attenuation",
            pen=False,
            fit_data_name='fit_signal'
        )



    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        time_i = 0
        self.core.break_realtime()
        
        while time_i < len(self.scan_att_397_sigma.sequence):
            
            att_397_sigma=self.scan_att_397_sigma.sequence[time_i]
           
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            # Cool
            self.seq.ion_store.run()

            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            delay(200*us)
            self.core.break_realtime()

            while sample_num<self.samples_per_time:
                if is_ion_good:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue

                    #854 repump
                    self.seq.repump_854.run()
                    
                    #  Cool
                    self.seq.doppler_cool.run()

                    #SBC
                    if self.enable_sideband_cool:
                        self.seq.sideband_cool.run()
                   
                    self.seq.sideband_Raman.run(att_397_sigma_here=att_397_sigma)

                    self.dds_Raman_1.set(self.RSB_freq_Raman1, amplitude=self.amp_Raman1)
                    self.dds_Raman_1.set_att(self.att_Raman1)
                    self.dds_Raman_2.set(self.freq_Raman2,  amplitude=self.amp_Raman2)
                    self.dds_Raman_2.set_att(self.att_Raman2)
                    delay(5*us)


                    if self.RSB_drive_time>0.1*us:
                        self.dds_Raman_1.sw.on()
                        self.dds_Raman_2.sw.on()
                        
                        delay(self.RSB_drive_time)
                        self.dds_Raman_1.sw.off()
                        self.dds_Raman_2.sw.off()
                    
                  
                    self.seq.rabi.run(self.PI_drive_time,
                                    self.freq_729_dp_pi,
                                    self.freq_729_sp_pi,
                                    self.att_729_dp_pi,
                                    self.att_729_sp_pi
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
                                                    [time_i, sample_num],
                                                    num_pmt_pulses)
                        
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        total_pmt_counts += num_pmt_pulses

                        self.core.break_realtime()
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
                        time_i=10000
                        sample_num+=10000
                        break
                     
            
            self.experiment_data.append_list_dataset("attenuation", att_397_sigma)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            time_i+=1
            self.core.break_realtime()

        self.seq.ion_store.run()
    # def analyze(self):
    #     rabi_time=self.get_dataset("rabi_t")
    #     rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
    #     self.fitting_func.fit(rabi_time, rabi_PMT)


    