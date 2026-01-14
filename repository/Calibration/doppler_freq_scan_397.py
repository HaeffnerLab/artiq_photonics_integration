from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class Doppler_FreqScan397(_ACFExperiment):

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
            group='Side_Band'
        )
        self.setattr_argument(
            "BSB_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2")-self.parameter_manager.get_param("qubit/vib_freq"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Side_Band'
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=30*dB, min=10*dB, max=30*dB, unit="dB", precision=8),
            group='Side_Band'
        )

        self.setattr_argument(
            "drive_time",
            NumberValue(default=500*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB excitation",
            group='Side_Band'
        )
    

        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
            
        )

        self.setattr_argument(
            "scan_freq_397",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("frequency/397_cooling")-2*MHz,
                    stop=self.parameter_manager.get_param("frequency/397_cooling")+2*MHz,
                    npoints=100
                ),
                global_min=60*MHz,
                global_max=5000*MHz,
                global_step=1*MHz,
                unit="MHz"
            ),
            tooltip="Scan parameters for sweeping the 854 laser."
        )

        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        

    def prepare(self):

        # Create datasets
        num_samples = len(self.scan_freq_397.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequency_MHz", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="frequency_MHz",
            fit_data_name='fit_signal',
            pen=True
        )

    @kernel
    def run(self):
        
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        
        freq_i = 0
        for freq_397 in self.scan_freq_397.sequence:

            delay(5*us)
            
            # Collect PMT counts
            total_thresh_count_RSB = 0
            total_thresh_count_BSB = 0

            
            for sample_i in range(self.samples_per_freq):
                #collect RSB excitation
                self.seq.repump_854.run()
                self.seq.doppler_cool.run(freq_397=freq_397)
                self.seq.rabi.run(self.drive_time,
                                  self.RSB_freq_729_dp,
                                  self.att_729_dp,
                                  0.0
                )

                delay(5*us)

                num_pmt_pulses=self.seq.readout_397.run()
                delay(5*us)
                #repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()

                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count_RSB += 1
                delay(1*ms)

                #collect BSB excitation
                self.seq.repump_854.run()
                self.seq.doppler_cool.run(freq_397=freq_397)
                self.seq.rabi.run(self.drive_time,
                                  self.BSB_freq_729_dp,
                                  self.att_729_dp,
                                  0.0
                )

                delay(5*us)

                num_pmt_pulses=self.seq.readout_397.run()
                delay(5*us)
                #repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()

                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count_BSB += 1
                delay(1*ms)
                
                
            pmt_counts_avg_RSB = total_thresh_count_RSB / self.samples_per_freq
            pmt_counts_avg_BSB = total_thresh_count_BSB / self.samples_per_freq
            
            res=pmt_counts_avg_RSB*1.0/(pmt_counts_avg_BSB*1.0-pmt_counts_avg_RSB*1.0+1e-5)

            if res>20:
                res=0.0

            # Update the datasets
            self.experiment_data.append_list_dataset("pmt_counts_avg", res)
            self.experiment_data.append_list_dataset("frequency_MHz", freq_397/MHz)
            
            freq_i += 1
            delay(5*ms)
        
        self.seq.ion_store.run()
	