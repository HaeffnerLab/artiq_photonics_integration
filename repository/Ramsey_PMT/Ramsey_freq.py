from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

class RamseyFreq(_ACFExperiment):

    def build(self):
    
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.rabi.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("readout/pmt_sampling_time")
        self.add_arg_from_param("doppler_cooling/cooling_time")

        #self.dds_729_dp=self.get_device("urukul2_ch3") for debug


        self.setattr_argument(
            "samples_per_scan",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each scan configuration",
        )
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        

        self.setattr_argument(
            "Ramsey_wait_time",
            NumberValue(default=0.1*us, min=0.*us, max=10000*us, unit='us'),
            tooltip="Ramsey wait time if don't scan this dimension",
            group='Ramsey non-scan setting'
        )
        self.setattr_argument(
            "Ramsey_pulse_time",
            NumberValue(default=0.1*us, min=0.*us, max=100*us, unit='us'),
            tooltip="Ramsey pulse time if don't scan this dimension",
            group='Ramsey non-scan setting'
        )   
        self.setattr_argument(
            "Ramsey_phase",
            NumberValue(default=0, min=0, max=1),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns) if don't scan this dimension",
            group='Ramsey non-scan setting'
        )


        self.setattr_argument(
            "Scan_Ramsey_Frequency", 
            Scannable(
                default=RangeScan(
                    start=233*MHz,
                    stop=234*MHz,
                    npoints=100
                ),
                global_min=220*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for Ramsey pulse frequency"
        )
        

        

    @kernel
    def rabi(self,pulse_time,phase:float=0.0):
        self.dds_729_dp.set(self.frequency_729_dp, phase=phase, amplitude=1.)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()

        

    @kernel
    def Ramsey(self, pulse_time:float, wait_time:float, phase:float):
        self.rabi(pulse_time,0.0)
        delay(wait_time)
        self.rabi(pulse_time,phase)
    
    def prepare(self):
        self.scan_length=len(self.Scan_Ramsey_Frequency.sequence)
        self.scan_name="frequency_MHz"

        # create datasets
        # num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [self.scan_length, self.samples_per_scan], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", self.scan_length, broadcast=True)
        self.experiment_data.set_list_dataset(self.scan_name, self.scan_length, broadcast=True)

        # # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name=self.scan_name,
            pen=True,
        )


    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.init_device.run()
        delay(5*us)
        self.seq.ion_store.run()
        delay(20*us)

        for iter in range(self.scan_length): # scan the frequency
            
            #the parameter for scanning in this iteration
            phase_here=self.Ramsey_phase
            wait_time_here=self.Ramsey_wait_time
            pulse_time_here=self.Ramsey_pulse_time

            self.frequency_729_dp=self.Scan_Ramsey_Frequency.sequence[iter]

            total_thresh_count = 0
            total_pmt_counts = 0

            # counter for repeating 
            sample_num=0

            while sample_num<self.samples_per_scan:

                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                
                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                #854 repump
                self.seq.repump_854.run()
                delay(5*us)
                
                #Cool
                self.seq.doppler_cool.run()
                delay(5*us)

                #sideband cooling
                self.seq.sideband_cool.run()
                delay(5*us)

                self.Ramsey(pulse_time=pulse_time_here, wait_time=wait_time_here, phase=phase_here)
                delay(5*us)

                #qubit readout
                num_pmt_pulses=self.seq.readout_397.run()
                delay(5*us)

                # 854 repump
                self.seq.repump_854.run()
                delay(5*us)

                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [iter, sample_num],
                                            num_pmt_pulses)
                                            
                #update the total count & thresholded events
                total_pmt_counts += num_pmt_pulses
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(5*ms)
                
            self.experiment_data.append_list_dataset(self.scan_name, self.Scan_Ramsey_Frequency.sequence[iter]/MHz)

            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg", float(total_pmt_counts) / self.samples_per_scan)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg", float(total_thresh_count) / self.samples_per_scan)
            
            delay(30*ms)
            
        self.seq.ion_store.run()

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
        #                     self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
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