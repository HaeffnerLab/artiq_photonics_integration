from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class FreqScanTickle(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/397") 
        self.add_arg_from_param("attenuation/866") 

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
            group="Misc"
        )

        self.setattr_argument(
            "att_tickle",
            NumberValue(default=30*dB, min=0.01*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )
        self.setattr_argument(
            "scan_freq_tickle",
            Scannable(
                default=RangeScan(
                    start=0.1*MHz,
                    stop=2.*MHz,
                    npoints=100
                ),
                global_min=0.*MHz,
                global_max=300.*MHz,
                global_step=1*MHz,
                precision=8,
                unit="MHz"
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )     
        
        self.setattr_argument("enable_diff_mode", BooleanValue(False))


    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_freq_tickle.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq])
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="frequencies_MHz"#,
            #fit_data_name='fit_signal'
        )


    @kernel
    def run(self):
        
        self.setup_run()
        self.seq.ion_store.run()
        delay(5*us)



        freq_i = 0
        for freq_tickle in self.scan_freq_tickle.sequence:

            # Set the 397 frequency
            self.seq.ion_store.run()

            self.dds_tickle.set(freq_tickle)
            self.dds_tickle.set_att(self.att_tickle)

            delay(20*us)
            
            # Collect PMT counts
            total_pmt_counts = 0
            for sample_i in range(self.samples_per_freq):

                self.seq.doppler_cool.run()
                delay(10*us)

                self.dds_tickle.sw.on()
            
                delay(20*us)

                num_pmt_pulses = self.seq.readout_397.run()

                self.dds_tickle.sw.off()
                
                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                self.experiment_data.insert_nd_dataset("pmt_counts", [freq_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses
                delay(3*ms)
                
                
            pmt_counts_avg = total_pmt_counts / self.samples_per_freq
            
            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_tickle/MHz)
            
            freq_i += 1
            delay(5*ms)
        
        self.seq.ion_store.run()


	
        


    # def analyze(self):

            
    #     freq=self.get_dataset("frequencies_MHz")
    #     PMT_count=self.get_dataset('pmt_counts_avg')


    #     with self.interactive("397 Frequency peak position estimate") as inter:
    #         inter.setattr_argument(
    #             "freq_397_resonance",
    #             NumberValue(default=freq[np.argmax(PMT_count)]*MHz, unit="MHz", min=160*MHz, max=240*MHz)
    #         )

    #     self.parameter_manager.set_param(
    #         "frequency/397_resonance",
    #         inter.freq_397_resonance,
    #         "MHz"
    #     )
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







