from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *
from acf.function.fitting import *

class Ramsey_Scan_Half(_ACFExperiment):

    def build(self):
    
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()


        # self.setup_fit(fitting_func ,'Exp_decay', 10)

        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("attenuation/729_dp")


       

        self.setattr_argument("Motional_Ramsey", BooleanValue(False),group = "Motional Ramsey")
        self.setattr_argument(
            "frequency_729_dp_SB",
            NumberValue(default=239.74*MHz, unit="MHz", min=200*MHz, max=250*MHz, precision=8),
            tooltip="Frequency for the red side band",
            group = "Motional Ramsey"
        )
        self.setattr_argument(
            "SB_drive_attenuation",
            NumberValue(default=20*dB, min=0.*dB, max=30*dB, unit='dB'),
            tooltip="Drive attenuation for the red side band",
            group = "Motional Ramsey"
        )
        self.setattr_argument(
            "SB_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=10000*us, unit='us'),
            tooltip="Drive time for the red side band",
            group = "Motional Ramsey"
        )

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
        self.setattr_argument("Scan_Type", EnumerationValue(["Ramsey_wait_time", "Ramsey_pulse_time", "Ramsey_phase"], default="Ramsey_wait_time"))

        self.setattr_argument(
            "Ramsey_wait_time_single",
            NumberValue(default=0.1*us, min=0.*us, max=10000*us, unit='us'),
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
                global_max=10000*us,
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
                    npoints=100
                )
            ),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns)",
            group='Ramsey scan setting'
        )

        

        self.scan_name='Ramsey_wait_time_(us)'

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
    def rabi(self,pulse_time,phase:float=0.0)-> None:

        # in the register, the phase is pow_/65536
        # in turns (meaning how many 2pi, 1 turn means 2pi)

        self.dds_729_dp.set(self.frequency_729_dp, phase=phase)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()

    @kernel
    def Ramsey(self, pulse_time:float, wait_time:float, phase:float)-> None:

        # 729 rabi flopping 
        self.rabi(pulse_time,0.0)
       
        # # delay(self.wait_time)
        # delay(wait_time)

        # self.rabi(pulse_time,phase)
    
    @kernel
    def SB(self):
        self.dds_729_dp.set(self.frequency_729_dp_SB)
        self.dds_729_dp.set_att(self.SB_drive_attenuation)
        self.dds_729_dp.sw.on()
        
        delay(self.SB_drive_time)

        self.dds_729_dp.sw.off()
        
    
    @kernel
    def Ramsey_Motion(self, pulse_time:float, wait_time:float, phase:float)-> None:

        # 729 rabi flopping 
        self.rabi(pulse_time,0.0)
        
        self.SB()
       
        # # # delay(self.wait_time)
        # delay(wait_time)

        # self.SB()

        # self.rabi(pulse_time,phase)

    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
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
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
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
            
            delay(5*ms)

        self.seq.ion_store.run()
        

    # def analyze(self):
        
    #     fit_length=0
    #     if self.Scan_Type == "Ramsey_wait_time":
    #         fit_length=len(self.Ramsey_wait_time.sequence)

    #     elif self.Scan_Type == "Ramsey_pulse_time":
    #         fit_length=len(self.Ramsey_pulse_time.sequence)
        
    #     else: #"Ramsey_phase"
    #         fit_length=len(self.Ramsey_phase.sequence)

    #     rabi_time=self.get_dataset(self.scan_name)
    #     rabi_PMT=self.get_dataset('pmt_counts_avg')
    #     # print(rabi_time.shape)
    #     # print(rabi_PMT.shape)
    #     # print(rabi_time[:fit_length])
    #     # print(rabi_PMT[:fit_length])
    #     self.fitting_func.fit(rabi_time[:fit_length], rabi_PMT[:fit_length])


''' potential code for 3D scan
        # ramsey_wait_time=scan_seq[0][0]
        # ramsey_pulse_time=scan_seq[1][0]
        # ramsey_phase=scan_seq[2][0]

        # for index0 in range(len(scan_seq[0])):
        #     for index1 in range(len(scan_seq[1])):
        #         for index2 in range(len(scan_seq[2])):

        #             ramsey_wait_time=scan_seq[0][index0]
        #             ramsey_pulse_time=scan_seq[1][index1]
        #             ramsey_phase=scan_seq[2][index2]
        #             for sample_num in range(self.samples_per_time):

        #                 self.dds_854_dp.set_att(30*dB)

        #                 self.Ramsey(wait_time=ramsey_wait_time, pulse_time=ramsey_pulse_time,phase=ramsey_phase)

        #                 num_pmt_pulses = self.ttl_pmt_input.count(
        #                     self.ttl_pmt_input.gate_rising(self.misc_pmt_sampling_time)
        #                 )
        #                 delay(10*us)

        #                 # 854 repump
        #                 self.dds_854_dp.set_att(self.attenuation_854_dp)
        #                 self.dds_854_dp.sw.on()
        #                 delay(self.repump_854_time)
        #                 self.dds_854_dp.sw.off()
        #                 self.dds_854_dp.set_att(30*dB)
        #                 delay(10*us)

        #                 # Update dataset
        #                 self.experiment_data.insert_nd_dataset("pmt_counts",
        #                                     [index0, index1],#, sample_num
        #                                     num_pmt_pulses)
        #                 delay(2*ms)

                    # self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)
                    # self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                    #                       float(total_thresh_count) / self.samples_per_time)
'''