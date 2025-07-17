from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

'''

drive a SDF and readout spin as a function of read time

'''

class SDFTimeScan(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.rabi.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        #the system parameters
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/854_dp")
        #Attenuation
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/854_dp")


        # Motional State Readout (displacement operator) https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.125.043602 

        # get the wigner function after trace out spin degrees of freedom  
        # displacement operation (may need to be a bit offseted due to stark shift)
        self.setattr_argument(
            "displace_freq_729_dp_resonance",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=50*MHz, max=120*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq"), min=50*MHz, max=120*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency 2",
            group='Displacement Operation'
        )
        # 
        self.setattr_argument(
            "displace_amp_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 douuble pass amplitude 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 single pass amplitude 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 single pass amplitude 2",
            group='Displacement Operation'
        )

        # the scan parameter for the displacement operator
        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=100*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )

        # general sampling parameters
        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )


    def prepare(self):
        

        # Create datasets
        num_freq_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("time", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="time",
            pen=False
        )
  
    @kernel
    def displacement(self,drive_time:float, drive_phase:float):
        
        #set attenuation
        self.dds_729_dp.set_att(self.displace_amp_729_dp)
        self.dds_729_sp.set_att(self.displace_amp_729_sp)
        self.dds_729_sp_aux.set_att(self.displace_amp_729_sp_aux)

        #set frequency
        self.dds_729_dp.set(self.displace_freq_729_dp_resonance)
        self.dds_729_sp.set(self.displace_freq_729_sp, phase=0.0)
        self.dds_729_sp_aux.set(self.displace_freq_729_sp_aux, phase=drive_phase)

        #turn on the 729
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.on()
        delay(drive_time)
        self.dds_729_dp.sw.off()

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        time_i = 0
        delay(10*us)

        for rabi_t in self.scan_rabi_t.sequence: 

            total_thresh_count = 0
            total_pmt_counts = 0

            # counter for repeating 
            sample_num=0

            while sample_num<self.samples_per_time:

                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)
                
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

                # Drive to a displacement state     --> |up>x|alpha>
                self.displacement(rabi_t,0.0)

                # self.seq.rabi.run(rabi_t,
                #                   self.displace_freq_729_dp_resonance,
                #                   self.displace_freq_729_sp,
                #                   self.displace_amp_729_dp,
                #                   self.displace_amp_729_sp
                # )

              

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
                                            [time_i, sample_num],
                                            num_pmt_pulses)
                # Record avergae spin
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1
                total_pmt_counts += num_pmt_pulses
                delay(3*ms)
            
            self.experiment_data.append_list_dataset("time", rabi_t/us)

            # if self.enable_thresholding:
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            # else:
            #     self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
            #                               float(total_pmt_counts) / self.samples_per_time)
            time_i += 1
            delay(10*ms)

        self.seq.ion_store.run()

    def analyze(self):
        pass
        # rabi_time=self.get_dataset("rabi_t")
        # rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        # self.fitting_func.fit(rabi_time, rabi_PMT)


    
    