from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class RamanTimeScan_Cam(_ACFExperiment):

    def build(self):
        self.setup(sequences)


        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
        self.seq.sideband_Raman.add_arguments_to_gui()


        self.setup_fit(fitting_func, 'Sin' ,-1)
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
            "freq_Raman1",
            NumberValue(default=self.parameter_manager.get_param("frequency/Raman1"), min=40*MHz, max=500*MHz, unit="MHz", precision=8),
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
        self.setattr_argument("enable_Raman_sideband_cool", BooleanValue(True))

        
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

    @kernel
    def exp_seq(self, rabi_t, ion_status_detect):
         #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()

        #SBC
        if self.enable_sideband_cool:
            self.seq.sideband_cool.run()
        if self.enable_Raman_sideband_cool:
            self.seq.sideband_Raman.run()

        self.dds_Raman_1.set(self.freq_Raman1, amplitude=self.amp_Raman1)
        self.dds_Raman_1.set_att(self.att_Raman1)
        self.dds_Raman_2.set(self.freq_Raman2,  amplitude=self.amp_Raman2)
        self.dds_Raman_2.set_att(self.att_Raman2)
        delay(5*us)


        if rabi_t>0.05*us:
            self.dds_Raman_1.sw.on()
            self.dds_Raman_2.sw.on()
            
            delay(rabi_t)
            self.dds_Raman_1.sw.off()
            self.dds_Raman_2.sw.off()
        
        
        self.seq.rabi.run(self.PI_drive_time,
                        self.freq_729_dp_pi,
                        self.freq_729_sp_pi,
                        self.att_729_dp_pi,
                        self.att_729_sp_pi
        )

        
    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()
        delay(0.5*s)

        self.seq.cam_two_ions.cam_setup()
        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1

        # #detecting the initial position of the ion 
        while ion_status_detect_last!=1 and ion_status_detect_last!=2:
            delay(2*ms)
            self.seq.repump_854.run()
            self.seq.doppler_cool.run()
            delay(5*us)
            ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
            self.seq.ion_store.run()
            delay(1*ms)
        
        if(ion_status_detect_last==3): 
            i=len(self.scan_rabi_t.sequence)
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        time_i=0

        
        while time_i < len(self.scan_rabi_t.sequence):

            rabi_t=self.scan_rabi_t.sequence[time_i]
           
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            # Cool
            self.seq.ion_store.run()

            # Collision Detection
            num_try_save_ion = 0 
            self.core.break_realtime()

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    delay(50*us)

                    self.exp_seq(rabi_t, ion_status_detect)
                    ################################################################################
                    ion_status=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()
                    delay(50*us)
                    ################################################################################
                    if ion_status==0: #if the ion is not bright then it's possible it's being kicked
                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        ion_status_detect=self.seq.cam_two_ions.cam_readout() #by the way get the position
                        self.seq.ion_store.run()
                        delay(20*us)
                    else: 
                        ion_status_detect=ion_status

                      
                    if (ion_status_detect==ion_status_detect_last ): #ion shouldn't move
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
                        self.seq.ion_store.run()
                        delay(1*s)
                        self.seq.doppler_cool.run()
                        self.seq.ion_store.run()
                    

                else:
                    self.seq.ion_store.run()
                    delay(1*s)
                    self.seq.doppler_cool.run()
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
                    delay(1*ms)



            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)

            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            time_i+=1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()
    
    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        self.fitting_func.fit(rabi_time, rabi_PMT)


    