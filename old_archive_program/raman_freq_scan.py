from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *


class RamanFreqScan(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'NLorentzian', -999)

        self.seq.cam_two_ions.build()

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


        
        self.setattr_argument(
            "scan_freq_Raman1",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("frequency/Raman1")-0.01*MHz,
                    stop=self.parameter_manager.get_param("frequency/Raman1")+0.01*MHz,
                    npoints=50
                ),
                global_min=0.0*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

        self.setattr_argument(
            "rabi_t",
            NumberValue(default=50*us, min=0.0*us, max=10000*us, unit="us", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "att_Raman1",
            NumberValue(default=self.parameter_manager.get_param("attenuation/Raman1"), min=8*dB, max=31*dB, unit="dB", precision=8),
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
            "amp_Raman2",
            NumberValue(default=1., min=0.0, max=1.0, precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        
        self.setattr_argument("enable_sideband_cool", BooleanValue(True))
        self.setattr_argument("enable_Raman_sideband_cool", BooleanValue(False))
        self.setattr_argument("enable_collision_detection", BooleanValue(True))  
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        

    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_Raman1.sequence)) 
         # Create datasets
        num_freq_samples = len(self.scan_freq_Raman1.sequence)
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
        self.core.break_realtime()
        delay(0.5*s)

        freq_i = 0
        while freq_i < len(self.scan_freq_Raman1.sequence):

            freq_Raman1=self.scan_freq_Raman1.sequence[freq_i]

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
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    #854 repump
                    self.seq.repump_854.run()
                    # Cool
                    self.seq.doppler_cool.run()

                    if self.enable_sideband_cool:
                        #
                        self.seq.sideband_cool.run()
                    else:
                        self.seq.op_pump.run()
                    
                    if self.enable_Raman_sideband_cool:
                        self.seq.sideband_Raman.run()

                    self.dds_Raman_1.set(freq_Raman1, amplitude=self.amp_Raman1)
                    self.dds_Raman_1.set_att(self.att_Raman1)
                    self.dds_Raman_2.set(self.freq_Raman2,  amplitude=self.amp_Raman2)
                    self.dds_Raman_2.set_att(self.att_Raman2)

                    # self.dds_397_sigma.set(206.8*MHz, amplitude=1.)
                    # self.dds_397_sigma.set_att(25*dB)
                    # self.dds_397_sigma.sw.on()
                    delay(5*us)
                    
                    if self.rabi_t>50*ns:
                        self.dds_Raman_1.sw.on()
                        self.dds_Raman_2.sw.on()
                        delay(self.rabi_t)
                        self.dds_Raman_1.sw.off()
                        self.dds_Raman_2.sw.off()
                    self.dds_397_sigma.sw.off()
                    
                  
                    self.seq.rabi.run(self.PI_drive_time,
                                    self.freq_729_dp_pi,
                                    self.freq_729_sp_pi,
                                    self.att_729_dp_pi,
                                    self.att_729_sp_pi
                    )

                    #qubit readout
                    #num_pmt_pulses=self.seq.readout_397.run()

                    ion_status=self.seq.cam_two_ions.cam_readout()

                    #if num_pmt_pulses < self.threshold_pmt_count and self.enable_collision_detection:

                    if ion_status==1 or ion_status==2:
                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        #num_pmt_pulses_detect=self.seq.readout_397.run()
                        ion_status_detect=self.seq.cam_two_ions.cam_readout()
                        self.seq.ion_store.run()
                        delay(20*us)

                        #if num_pmt_pulses_detect < self.threshold_pmt_count:
                        if ion_status_detect==0 or ion_status_detect==3:
                            is_ion_good = False
                            
                    if is_ion_good:
                        sample_num+=1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [freq_i, sample_num],
                        #                             num_pmt_pulses)
                        
                        #if num_pmt_pulses < self.threshold_pmt_count:
                        if ion_status==1 or ion_status==2:
                            total_thresh_count += 1

                        #total_pmt_counts += num_pmt_pulses

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
                    
                    if(num_try_save_ion>300):
                        print("Ion Lost!!!")
                        freq_i=100000
                        sample_num+=10000
                        break
                     
            
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_Raman1 / MHz)
            # if not self.enable_thresholding:
            # 	self.experiment_data.append_list_dataset("pmt_counts_avg",
            #                               -float(total_pmt_counts) / self.samples_per_freq)
            # else:
            self.experiment_data.append_list_dataset("pmt_counts_avg",
                                        float(total_thresh_count) / self.samples_per_freq)
            freq_i += 1
                
            
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()


    def analyze(self):

            
        freq=self.get_dataset("frequencies_MHz")
        PMT_count=self.get_dataset('pmt_counts_avg')

        peak=self.fitting_func.fit(freq, PMT_count)[1]


        with self.interactive("Ca+ line") as inter:
            inter.setattr_argument(
                "Ca_line", 
                EnumerationValue(["Sm1_2_S1_2", "Sm1_2_S1_2_RSB", "nothing"])
            )

        if inter.Ca_line=="Sm1_2_S1_2":
            self.parameter_manager.set_param(
                "frequency/Raman1",
                peak*1e6,
                "MHz"
            )
        else:
            self.parameter_manager.set_param(
                "sideband_Raman/vib_freq1",
                self.parameter_manager.get_param("frequency/Raman1")-peak*1e6,
                "MHz"
            )
