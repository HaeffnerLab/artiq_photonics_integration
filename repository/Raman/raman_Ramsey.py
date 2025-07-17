from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *
from acf.function.fitting import *

class Raman_Ramsey_Scan(_ACFExperiment):

    def build(self):
    
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        


        #################################################################################################################################################################
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

        #################################################################################################################################################################
        self.setattr_argument("Motional_Ramsey", BooleanValue(False),group = "Motional Ramsey")
        self.setattr_argument(
            "freq_Raman1_SB",
            NumberValue(default=self.parameter_manager.get_param("frequency/Raman1"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "SB_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=10000*us, unit='us'),
            tooltip="Drive time for the red side band",
            group = "Motional Ramsey"
        )

        #################################################################################################################################################################
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

        #################################################################################################################################################################
        self.setattr_argument(
            "samples_per_scan",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each scan configuration",
        )
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        self.setattr_argument("Scan_Type", EnumerationValue(["Ramsey_wait_time", "Ramsey_pulse_time", "Ramsey_phase"], default="Ramsey_phase"))

        self.setattr_argument(
            "Ramsey_wait_time_single",
            NumberValue(default=0.1*us, min=0.*us, max=100000*us, unit='us'),
            tooltip="Ramsey wait time if don't scan this dimension",
            group='Ramsey non-scan setting'
        )
        self.setattr_argument(
            "Ramsey_pulse_time_single",
            NumberValue(default=0.1*us, min=0.*us, max=100*us, unit='us'),
            tooltip="Ramsey pulse time if don't scan this dimension",
            group='Ramsey non-scan setting'
        )   
        self.setattr_argument(
            "Ramsey_phase_single",
            NumberValue(default=0, min=0, max=1),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns) if don't scan this dimension",
            group='Ramsey non-scan setting'
        )

        self.setattr_argument(
            "Ramsey_wait_time",
            Scannable(
                default=RangeScan(
                    start=0.*us,
                    stop=10000*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=100000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for Ramsey wait time.",
            group='Ramsey scan setting'
        )   
        self.setattr_argument(
            "Ramsey_pulse_time",
            Scannable(
                default=RangeScan(
                    start=0.*us,
                    stop=10*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=100*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for Ramsey pulse time.",
            group='Ramsey scan setting'
        )
        self.setattr_argument(
            "Ramsey_phase",
            Scannable(
                default=RangeScan(
                    start=0,
                    stop=1,
                    npoints=15
                )
            ),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns)",
            group='Ramsey scan setting'
        )
        self.scan_name='Ramsey_wait_time_(us)'
        #################################################################################################################################################################

    def prepare(self):
        scan_length=max(len(self.Ramsey_wait_time.sequence), max(len(self.Ramsey_pulse_time.sequence),len(self.Ramsey_phase.sequence)))
       
        self.scan_param0 =[0.0 *us for i in range(scan_length)] 
        self.scan_param1 =[0.0 *us for i in range(scan_length)]
        self.scan_param2 =[0.0 for i in range(scan_length)]        
        self.scan_axis=[0.0 for i in range(scan_length)]   
        self.num_scan_samples = 0

        if self.Scan_Type == "Ramsey_wait_time":
            for i in range(len(self.Ramsey_wait_time.sequence)):
                self.scan_param0[i]=self.Ramsey_wait_time.sequence[i]
                self.scan_param1[i]=self.Ramsey_pulse_time_single
                self.scan_param2[i]=self.Ramsey_phase_single

                self.scan_axis[i]=self.Ramsey_wait_time.sequence[i]/us
            self.num_scan_samples=len(self.Ramsey_wait_time.sequence)
            self.scan_name='Ramsey_wait_time_(us)'


        elif self.Scan_Type == "Ramsey_pulse_time":
            for i in range(len(self.Ramsey_pulse_time.sequence)):
                self.scan_param0[i]=self.Ramsey_wait_time_single
                self.scan_param1[i]=self.Ramsey_pulse_time.sequence[i]
                self.scan_param2[i]=self.Ramsey_phase_single

                self.scan_axis[i]=self.Ramsey_pulse_time.sequence[i]/us
            self.num_scan_samples=len(self.Ramsey_pulse_time.sequence)
            self.scan_name='Ramsey_pulse_time_(us)'


        
        else: #"Ramsey_phase"
            for i in range(len(self.Ramsey_phase.sequence)):
                self.scan_param0[i]=self.Ramsey_wait_time_single
                self.scan_param1[i]=self.Ramsey_pulse_time_single
                self.scan_param2[i]=self.Ramsey_phase.sequence[i]

                self.scan_axis[i]=self.Ramsey_phase.sequence[i]
            self.num_scan_samples=len(self.Ramsey_phase.sequence)
            self.scan_name='Ramsey_phase_(turns)'




        # create datasets
        self.experiment_data.set_nd_dataset("pmt_counts", [scan_length, self.samples_per_scan], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", scan_length, broadcast=True)
        self.experiment_data.set_list_dataset(self.scan_name, scan_length, broadcast=True)

        # # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name=self.scan_name,
            pen=True#,
            #fit_data_name='fit_signal'
        )


    @kernel
    def Ramsey(self, pulse_time:float, wait_time:float, phase:float)-> None:

        #set frequency
        self.dds_Raman_1.set(self.freq_Raman1)
        self.dds_Raman_1.set_att(self.att_Raman1)
        self.dds_Raman_2.set(self.freq_Raman2)
        self.dds_Raman_2.set_att(self.att_Raman2)

        #carrier pulse
        self.dds_Raman_1.sw.on()
        self.dds_Raman_2.sw.on()
        delay(pulse_time)
        self.dds_Raman_1.sw.off()
        self.dds_Raman_2.sw.off()
       
        delay(wait_time)

        #carrier pulse
        self.dds_Raman_1.set(self.freq_Raman1, phase=phase)
        self.dds_Raman_1.sw.on()
        self.dds_Raman_2.sw.on()
        delay(pulse_time)
        self.dds_Raman_1.sw.off()
        self.dds_Raman_2.sw.off()
    
    @kernel
    def Ramsey_Motion(self, pulse_time:float, wait_time:float, phase:float)-> None:

        #set frequency
        self.dds_Raman_1.set(self.freq_Raman1)
        self.dds_Raman_1.set_att(self.att_Raman1)
        self.dds_Raman_2.set(self.freq_Raman2)
        self.dds_Raman_2.set_att(self.att_Raman2)
        
        # # 729 rabi flopping 
        # self.rabi(pulse_time,0.0)
        
        # self.SB()
       
        # # # delay(self.wait_time)
        # delay(wait_time)

        # self.SB()

        # self.rabi(pulse_time,phase)

    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()
        delay(1*ms)

        for iter in range(self.num_scan_samples): # scan the frequency
            
            #the parameter for scanning in this iteration
            phase_here=self.scan_param2[iter]
            wait_time_here=self.scan_param0[iter]
            pulse_time_here=self.scan_param1[iter]

            total_thresh_count = 0
            total_pmt_counts = 0

            sample_num=0

            

            self.seq.ion_store.run()
            delay(500*us)

            while sample_num<self.samples_per_scan:

                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(100*us)

                #854 repump
                self.seq.repump_854.run()
                # Cool
                self.seq.doppler_cool.run()
                self.seq.sideband_cool.run()

                if self.Motional_Ramsey:
                    self.Ramsey_Motion(pulse_time=pulse_time_here, wait_time=wait_time_here, phase=phase_here)
                else:
                    self.Ramsey(pulse_time=pulse_time_here, wait_time=wait_time_here, phase=phase_here)
                
                self.seq.rabi.run(self.PI_drive_time,
                                    self.freq_729_dp_pi,
                                    self.freq_729_sp_pi,
                                    self.att_729_dp_pi,
                                    self.att_729_sp_pi
                    )
                
                 #qubit readout
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()
                
                #protect ion
                self.seq.ion_store.run()

                #Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [iter, sample_num],
                                            num_pmt_pulses)
                                            
                #update the total count & thresholded events
                total_pmt_counts += num_pmt_pulses
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(1*ms)
                
            self.experiment_data.append_list_dataset(self.scan_name, self.scan_axis[iter])

            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg", float(total_pmt_counts) / self.samples_per_scan)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg", float(total_thresh_count) / self.samples_per_scan)
            
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()