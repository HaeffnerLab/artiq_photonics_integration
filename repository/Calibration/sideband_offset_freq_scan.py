from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class Sideband_FreqScanOffset(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.rabi.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling") #
        self.add_arg_from_param("frequency/397_far_detuned") #
        self.add_arg_from_param("frequency/866_cooling")
        #self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397") #
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866") #
        #self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
            group="Misc"
        )

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2")+self.parameter_manager.get_param("qubit/vib_freq"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
        )

        self.setattr_argument(
            "RSB_drive_time",
            NumberValue(default=100*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB excitation",
        )

        self.setattr_argument(
            "scan_freq_offset", #motional frequency on -1/2 -> --5/2
            Scannable(
                default=RangeScan(
                    start=0.2*MHz,
                    stop=0.3*MHz,
                    npoints=50
                ),
                global_min=0.01*MHz,
                global_max=2*MHz,
                global_step=1*MHz,
                unit="MHz"
            )
        )

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        

    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_freq_offset.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="frequencies_MHz",
            fit_data_name='fit_signal',
            pen=False
        )

    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(10*us)

        
        att_i = 0
        for freq_offset in self.scan_freq_offset.sequence:
            
            # Collect PMT counts
            total_pmt_counts = 0
            total_thresh_count = 0

            for sample_i in range(self.samples_per_freq):

                #turn off all dds
                self.seq.off_dds.run()
                delay(5*us)
                #  854 repump
                self.seq.repump_854.run()
                delay(5*us)
                #  Cool
                self.seq.doppler_cool.run()
                delay(5*us)
                self.seq.sideband_cool.run(freq_offset=freq_offset)
                delay(5*us)


                self.seq.rabi.run(self.RSB_drive_time,
                                  self.freq_729_dp,
                                  self.frequency_729_sp,
                                  self.att_729_dp,
                                  self.attenuation_729_sp,
                                  0.0
                )

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
            

            self.experiment_data.append_list_dataset("frequencies_MHz", freq_offset/MHz)
            
            att_i += 1
	