from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class FreqScan397ACF(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Voigt_Split', 218)

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling") #
        self.add_arg_from_param("frequency/397_far_detuned") #
        self.add_arg_from_param("frequency/866_cooling") #
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397") #
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")#
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")

        # Frequencies

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
                    npoints=50
                ),
                global_min=150*MHz,
                global_max=300*MHz,
                global_step=1*MHz,
                unit="MHz"
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )
        
        self.setattr_argument(
            "collect_result",
            BooleanValue(default=False),
            tooltip="Whether to prompt for a result at the end",
            group="Misc"
        )


    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_397.sequence))
       

    @kernel
    def run(self):
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

        self.setup_run()

        self.dds_729_dp.sw.off()

        # Get current values of rf signals to reset to after this script finishes
        delay(1*ms)
        freq_397_original = self.dds_397_dp.get_frequency()
        delay(1*ms)
        freq_866_original = self.dds_866_dp.get_frequency()
        delay(1*ms)
        attenuation_397_original = self.dds_397_dp.get_att()
        delay(1*ms)
        attenuation_866_original = self.dds_866_dp.get_att()
        delay(1*ms)

        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_866_dp.set_att(self.attenuation_866)
        
        # Set the 866 frequency
        delay(1*ms)
        self.dds_866_dp.set(self.freq_866)
        #print(self.dds_866_dp.get_frequency())
        
        freq_i = 0
        for freq_397 in self.scan_freq_397.sequence:

            # Set the 397 frequency
            self.dds_397_dp.set(freq_397)
            
            self.dds_397_far_detuned.cfg_sw(False)
            
            # Collect PMT counts
            total_pmt_counts = 0
            for sample_i in range(self.samples_per_freq):
                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(10*ms)
                )
                self.experiment_data.insert_nd_dataset("pmt_counts", [freq_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses
                
                delay(1.5*ms)
                
                self.seq.doppler_cool.run()
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                
                delay(1*ms)
                
                self.dds_397_dp.set(freq_397)
                
                delay(1*ms)
                
            pmt_counts_avg = total_pmt_counts / self.samples_per_freq
            
            # Set regular frequencies and delay before taking next measurement
            delay(1*ms)
            self.dds_397_dp.set_att(attenuation_397_original)
            delay(1*ms)
            self.dds_866_dp.set_att(attenuation_866_original)
            delay(1*ms)
            self.dds_397_dp.set(freq_397_original)
            delay(1*ms)
            #self.dds_866_dp.set(freq_866_original)
            self.dds_866_dp.set(self.freq_866)
            delay(100*ms)

            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_397/MHz)
            
            freq_i += 1
	
        if self.collect_result:
            self.get_results()
        
        
        # with self.interactive("397 Frequency peak position estimate") as inter:
        #     inter.setattr_argument(
        #         "freq_397_resonance",
        #         NumberValue(default=215*MHz, unit="MHz", min=160*MHz, max=240*MHz)
        #     )

    def analyze(self):
        # with self.interactive("397 Frequency peak position estimate") as inter:
        #     inter.setattr_argument(
        #         "freq_397_resonance",
        #         NumberValue(default=215*MHz, unit="MHz", min=160*MHz, max=240*MHz)
        #     )
            
            freq_397=self.get_dataset("frequencies_MHz")
            PMT_count=self.get_dataset('pmt_counts_avg')

            self.fitting_func.fit(freq_397, PMT_count)

    
    def get_results(self):
        """Prompt user for the results and set the appropriate parameters."""
        with self.interactive("397 Frequency Scan Results") as inter:
            inter.setattr_argument(
                "freq_397_resonance",
                NumberValue(default=200*MHz, unit="MHz", min=160*MHz, max=240*MHz),
                tooltip="The new 397 resonance frequency."
            )

            inter.setattr_argument(
                "freq_397_cooling",
                NumberValue(default=200*MHz, unit="MHz", min=160*MHz, max=240*MHz),
                tooltip="The new 397 cooling frequency."
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

    # Define the Lorentzian function






