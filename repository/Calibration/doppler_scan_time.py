from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class Doppler_ScanTime(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.readout_397_diff.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling") #
        self.add_arg_from_param("frequency/397_far_detuned") #
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866") #
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("readout/pmt_sampling_time")

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=5, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
            group="Misc"
        )

        self.setattr_argument(
            "scan_doppler_time",
            Scannable(
                default=RangeScan(
                    start=0.5*ms,
                    stop=5*ms,
                    npoints=20
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )

        self.setattr_argument(
            "RSB_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2")+self.parameter_manager.get_param("qubit/vib_freq"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Red_Side_Band'
        )
        self.setattr_argument(
            "RSB_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            group='Red_Side_Band'
        )

        self.setattr_argument(
            "RSB_drive_time",
            NumberValue(default=100*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB excitation",
            group='Red_Side_Band'
        )


        self.setattr_argument("enable_diff_mode", BooleanValue(False))

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        

    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_doppler_time.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("time", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="time",
            fit_data_name='fit_signal'
        )

    @kernel
    def run(self):
        
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        
        att_i = 0
        for doppler_time in self.scan_doppler_time.sequence:

            delay(5*us)
            
            # Collect PMT counts
            total_pmt_counts = 0
            total_thresh_count =0
            for sample_i in range(self.samples_per_freq):

                self.seq.doppler_cool.run(doppler_time=doppler_time)

                delay(5*us)

                self.seq.rabi.run(self.RSB_drive_time,
                                  self.RSB_freq_729_dp,
                                  self.frequency_729_sp,
                                  self.RSB_att_729_dp,
                                  self.attenuation_729_sp,
                                  0.0
                )
                
                if self.enable_diff_mode:
                    num_pmt_pulses = self.seq.readout_397_diff.run()
                else:
                    num_pmt_pulses = self.seq.readout_397.run()


                delay(5*us)

                self.seq.repump_854.run()

                #protect ion
                self.seq.ion_store.run()

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
            

            self.experiment_data.append_list_dataset("time", doppler_time/ms)

            delay(2*ms)
            