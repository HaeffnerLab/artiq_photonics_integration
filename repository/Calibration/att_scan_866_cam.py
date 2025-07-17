from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class AttScan866_Cam(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.seq.cam_two_ions.build()
        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=5, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
            group="Misc"
        )

        self.setattr_argument(
            "scan_att_866",
            Scannable(
                default=RangeScan(
                    start=12*dB,
                    stop=30*dB,
                    npoints=100
                ),
                global_min=10*dB,
                global_max=31.5*dB,
                unit="dB",
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
        )

        self.setattr_argument("enable_diff_mode", BooleanValue(True))
        

    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_att_866.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation_dB", num_samples, broadcast=True)
        # self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="attenuation_dB"#,
            #fit_data_name='fit_signal'
        )

    @kernel
    def run(self):
        
        self.setup_run()
        self.seq.ion_store.run()
        delay(5*us)
        self.seq.rf.set_voltage(mode="lower")
        self.seq.cam_two_ions.cam_setup()

        
        att_i = 0
        for att_866 in self.scan_att_866.sequence:

            self.seq.ion_store.run()

            delay(50*us)
            
            # Collect PMT counts
            total_pmt_counts = 0.0
            for sample_i in range(self.samples_per_freq):

                self.seq.doppler_cool.run()

                delay(5*us)
                
                cam_input=[0.0,0.0]
                self.seq.cam_two_ions.cam_readout_raw(cam_input, att_866_here=att_866)
                num_pmt_pulses1=cam_input[0]+cam_input[1]
               
                delay(10*us)

                if self.enable_diff_mode:
                    self.seq.cam_two_ions.cam_readout_raw(cam_input, off_866=True , att_866_here=att_866)
                    num_pmt_pulses2= cam_input[0]+cam_input[1]

                    num_pmt_pulses = num_pmt_pulses1 - num_pmt_pulses2
                else:
                    num_pmt_pulses = num_pmt_pulses1 
                
                #protect ion
                self.seq.ion_store.run()
                delay(5*us)


              #  self.experiment_data.insert_nd_dataset("pmt_counts", [att_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses
                delay(10*ms)
                
                
            pmt_counts_avg = total_pmt_counts / self.samples_per_freq
            
            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("attenuation_dB", att_866/dB)
            
            att_i += 1
            delay(5*ms)
        
        self.seq.ion_store.run()


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






