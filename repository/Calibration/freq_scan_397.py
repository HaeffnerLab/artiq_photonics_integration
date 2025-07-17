from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class FreqScan397(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Voigt_Split', 218)

        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/397") 
        self.add_arg_from_param("attenuation/866") 
        self.add_arg_from_param("readout/pmt_sampling_time")

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=5, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
            group="Misc"
        )

        self.setattr_argument(
            "scan_freq_397",
            Scannable(
                default=RangeScan(
                    start=190*MHz,
                    stop=235*MHz,
                    npoints=100
                ),
                global_min=150*MHz,
                global_max=300*MHz,
                global_step=1*MHz,
                unit="MHz"
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )     
        
        self.setattr_argument(
           "far_detuned_on",
            BooleanValue(default=False),
            tooltip="Whether to prompt for a result at the end"
        )

        self.setattr_argument("enable_diff_mode", BooleanValue(False))


    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_397.sequence))

        # Create datasets
        num_samples = len(self.scan_freq_397.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="frequencies_MHz",
            fit_data_name='fit_signal'
        )


    @kernel
    def run(self):
        
        self.setup_run()
        self.seq.ion_store.run()
        delay(5*us)



        freq_i = 0
        for freq_397 in self.scan_freq_397.sequence:

            # Set the 397 frequency
            self.dds_397_dp.set(freq_397)
            self.dds_397_far_detuned.cfg_sw(False)
            self.dds_397_dp.sw.on()
            self.dds_866_dp.sw.on()

            delay(20*us)
            
            # Collect PMT counts
            total_pmt_counts = 0
            for sample_i in range(self.samples_per_freq):

                self.seq.doppler_cool.run()
                
                self.dds_397_dp.set(freq_397)
                self.dds_397_dp.set_att(self.attenuation_397)
                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_866_dp.set_att(self.attenuation_866)

                delay(10*us)

                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                if self.far_detuned_on:
                    self.dds_397_far_detuned.cfg_sw(True)
                else:
                    self.dds_397_far_detuned.cfg_sw(False)

                num_pmt_pulses1 = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                )
                delay(10*us)
                self.dds_866_dp.sw.off()
                
               
                delay(10*us)

                if self.enable_diff_mode:
                    num_pmt_pulses2 = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                    )
                    delay(30*us)

                    num_pmt_pulses = num_pmt_pulses1 - num_pmt_pulses2
                else:
                    num_pmt_pulses = num_pmt_pulses1 
                
                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                self.experiment_data.insert_nd_dataset("pmt_counts", [freq_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses
                delay(5*ms)
                
                
            pmt_counts_avg = total_pmt_counts / self.samples_per_freq
            
            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_397/MHz)
            
            freq_i += 1
            delay(5*ms)
        
        self.seq.ion_store.run()


	
        


    def analyze(self):

            
        freq=self.get_dataset("frequencies_MHz")
        PMT_count=self.get_dataset('pmt_counts_avg')

        if self.far_detuned_on:

            with self.interactive("397 Frequency peak position estimate") as inter:
                inter.setattr_argument(
                    "freq_397_cooling_stark",
                    NumberValue(default=freq[np.argmax(PMT_count)]*MHz-6.5*MHz, unit="MHz", min=160*MHz, max=240*MHz)
                )
            self.parameter_manager.set_param(
                "frequency/397_cooling_stark",
                inter.freq_397_cooling_stark,
                "MHz"
            )
        else:


            with self.interactive("397 Frequency peak position estimate") as inter:
                inter.setattr_argument(
                    "freq_397_resonance",
                    NumberValue(default=freq[np.argmax(PMT_count)]*MHz-0.5*MHz, unit="MHz", min=160*MHz, max=240*MHz)
                )

                inter.setattr_argument(
                    "freq_397_cooling",
                    NumberValue(default=freq[np.argmax(PMT_count)]*MHz-5.2*MHz, unit="MHz", min=160*MHz, max=240*MHz)
                )

            self.parameter_manager.set_param(
                "frequency/397_resonance",
                inter.freq_397_resonance,
                "MHz"
            )

            self.parameter_manager.set_param(
                "frequency/397_cooling",
                inter.freq_397_cooling,
                "MHz"
            )
        #self.fitting_func.fit(freq, PMT_count)

    
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







