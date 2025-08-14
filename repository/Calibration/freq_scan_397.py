from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class FreqScan397(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Voigt_Split', 218)


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
                    stop=220*MHz,
                    npoints=60,
                    randomize=True
                ),
                global_min=20*MHz,
                global_max=300*MHz,
                global_step=1*MHz,
                unit="MHz"
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )     
        
        # self.setattr_argument(
        #    "far_detuned_on",
        #     BooleanValue(default=False),
        #     tooltip="Whether to prompt for a result at the end"
        # )

        self.setattr_argument("enable_diff_mode", BooleanValue(True))


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
        self.core.break_realtime()
        delay(100*us)
        self.seq.ion_store.run()
        
        delay(100*us)



        freq_i = 0
        for freq_397 in self.scan_freq_397.sequence:

            # Set the 397 frequency
            self.core.break_realtime()
            delay(50*us)
            
            # Collect PMT counts
            total_pmt_counts = 0
            for sample_i in range(self.samples_per_freq):

                self.seq.doppler_cool.run()
                delay(20*us)

                num_pmt_pulses1 = self.seq.readout_397.run(freq_397_dp=freq_397)
                delay(10*us)
                
               

                if self.enable_diff_mode:
                    num_pmt_pulses2 = self.seq.readout_397.run(freq_397_dp=freq_397, turn_off_866=True)

                    num_pmt_pulses = num_pmt_pulses1 - num_pmt_pulses2
                else:
                    num_pmt_pulses = num_pmt_pulses1 
                
                #protect ion
                self.seq.ion_store.run() 
                delay(5*us)

                self.experiment_data.insert_nd_dataset("pmt_counts", [freq_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses
                self.core.break_realtime()
                delay(100*us)
                
                
            pmt_counts_avg = total_pmt_counts / self.samples_per_freq
            
            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_397/MHz)
            
            freq_i += 1
            self.core.break_realtime()
            delay(200*us)
        
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







