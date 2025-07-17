from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class Doppler_AttScan397(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()


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
            "RSB_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Red_Side_Band'
        )
        self.setattr_argument(
            "RSB_att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            group='Red_Side_Band'
        )

        self.setattr_argument(
            "RSB_drive_time",
            NumberValue(default=300*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB excitation",
            group='Red_Side_Band'
        )
    

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=5, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
            
        )

        self.setattr_argument(
            "scan_att_397",
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

        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        

    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_att_397.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation_dB", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="attenuation_dB",
            fit_data_name='fit_signal'
        )

    @kernel
    def run(self):
        
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        
        att_i = 0
        for att_397 in self.scan_att_397.sequence:

            delay(5*us)
            
            # Collect PMT counts
            total_thresh_count = 0
            for sample_i in range(self.samples_per_freq):

                self.seq.doppler_cool.run(att_397=att_397)

                self.seq.rabi.run(self.RSB_drive_time,
                                  self.RSB_freq_729_dp,
                                  self.RSB_freq_729_sp,
                                  self.RSB_att_729_dp,
                                  self.RSB_att_729_sp,
                                  0.0
                )

                delay(15*us)

                num_pmt_pulses=self.seq.readout_397.run()

                delay(5*us)

                self.seq.repump_854.run()

                #protect ion
                self.seq.ion_store.run()

                self.experiment_data.insert_nd_dataset("pmt_counts", [att_i, sample_i], num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1
                
                delay(10*ms)
                
                
            pmt_counts_avg = total_thresh_count / self.samples_per_freq
            
            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("attenuation_dB", att_397/dB)
            
            att_i += 1
            delay(5*ms)
        
        self.seq.ion_store.run()
	