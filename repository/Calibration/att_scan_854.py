from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class AttScan854(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling") #
        self.add_arg_from_param("frequency/397_far_detuned") #
        self.add_arg_from_param("frequency/866_cooling")
        #self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397") #
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866") #
        #self.add_arg_from_param("attenuation/729_dp")
        #self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("readout/pmt_sampling_time")

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
            group="Misc"
        )

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
        )

        self.setattr_argument(
            "scan_att_854",
            Scannable(
                default=RangeScan(
                    start=12*dB,
                    stop=30*dB,
                    npoints=20
                ),
                global_min=10*dB,
                global_max=31.5*dB,
                unit="dB",
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        

    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_att_854.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation_dB", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="attenuation_dB",
            fit_data_name='fit_signal'
        )


    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        delay(10*us)
        
        att_i = 0
        for att_854 in self.scan_att_854.sequence:

            self.dds_854_dp.set_att(att_854)
            self.dds_854_dp.set(self.frequency_854_dp)

            # Collect PMT counts
            total_pmt_counts = 0
            total_thresh_count = 0

            for sample_i in range(self.samples_per_freq):

                
                #turn off all dds
                self.seq.off_dds.run()
                delay(5*us)
                
                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                #854 repump
                self.seq.repump_854.run()
                delay(5*us)
                
                #  Cool
                self.seq.doppler_cool.run()
                delay(5*us)

                self.seq.sideband_cool.run()

                #see how good the pump is, for good sideband cooling, the population should be half
                self.dds_729_dp.set_att(self.att_729_dp)
                self.dds_729_dp.set(self.freq_729_dp)
                self.dds_729_dp.sw.on()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(100*us)

                self.dds_729_dp.sw.off()

                delay(200*us)
                self.dds_866_dp.sw.off()
                self.dds_854_dp.sw.off()
                delay(5*us)


                num_pmt_pulses=self.seq.readout_397.run()

                delay(5*us)

                self.seq.repump_854.run()

                #protect ion
                self.seq.ion_store.run()

                delay(5*ms)
                self.experiment_data.insert_nd_dataset("pmt_counts", [att_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses

                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1
                
                
                delay(1*ms)
                
            # Update the datasets
            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_freq)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_freq)
            

            self.experiment_data.append_list_dataset("attenuation_dB", att_854/dB)
            
            att_i += 1
        
        self.seq.ion_store.run()
	
        # if self.collect_result:
        #     self.get_results()
        


    # def analyze(self):

            
    #         freq=self.get_dataset("frequencies_MHz")
    #         PMT_count=self.get_dataset('pmt_counts_avg')

    #         self.fitting_func.fit(freq, PMT_count)

    
    # def get_results(self):
    #     """Prompt user for the results and set the appropriate parameters."""
    #     with self.interactive("397 Frequency Scan Results") as inter:
    #         inter.setattr_argument(
    #             "freq_397_resonance",
    #             NumberValue(default=200*MHz, unit="MHz", min=160*MHz, max=240*MHz),
    #             tooltip="The new 397 resonance frequency."
    #         )

    #         inter.setattr_argument(
    #             "freq_397_cooling",
    #             NumberValue(default=200*MHz, unit="MHz", min=160*MHz, max=240*MHz),
    #             tooltip="The new 397 cooling frequency."
    #         )

    #     self.parameter_manager.set_param(
    #         "frequency/397_resonance",
    #         inter.freq_397_resonance,
    #         "MHz"
    #     )
    #     self.parameter_manager.set_param(
    #         "frequency/397_cooling",
    #         inter.freq_397_cooling,
    #         "MHz"
    #     )

    # Define the Lorentzian function






