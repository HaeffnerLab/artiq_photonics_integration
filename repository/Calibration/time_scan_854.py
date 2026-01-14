from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class TimeScan854(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Exp_decay', 20)

        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/866")


        self.setattr_argument(
            "PI_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=2.4*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )


        self.setattr_argument(
            "samples_per_scan",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
        )

        self.setattr_argument(
            "scan_854_time",
            Scannable(
                default=RangeScan(
                    start=0.0*us,
                    stop=100*us,
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
            "freq_854",
            NumberValue(default=self.parameter_manager.get_param("frequency/854_dp"), min=20*MHz, max=300*MHz, unit="MHz", precision=5),
            tooltip="854 drive attenuation"
        )
        self.setattr_argument(
            "att_854",
            NumberValue(default=self.parameter_manager.get_param("attenuation/854_dp"), min=2*dB, max=30*dB, unit="dB", precision=5),
            tooltip="854 drive attenuation"
        )

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        



    def prepare(self):
        self.fitting_func.setup(len(self.scan_854_time.sequence))

        # Create datasets
        num_samples = len(self.scan_854_time.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_scan], broadcast=True)
        #self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("time", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="time",
            pen=False,
            fit_data_name='fit_signal'
        )


          
    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(10*us)
        
        freq_i = 0
        for drive_854_time in self.scan_854_time.sequence:
            
            # Collect PMT counts
            total_pmt_counts = 0
            total_thresh_count = 0

            for sample_i in range(self.samples_per_scan):

                #turn off all dds
                self.seq.off_dds.run()
                delay(5*us)
                #  854 repump
                self.seq.repump_854.run()
                delay(5*us)
                #  Cool
                self.seq.doppler_cool.run()
                delay(5*us)
                self.seq.sideband_cool.run()
                delay(5*us)

                self.seq.rabi.run(self.PI_drive_time,
                                  self.PI_freq_729_dp,
                                  self.PI_att_729_dp,
                                  self.PI_att_729_dp
                    )
                delay(5*us)

                #repump 854   
                self.dds_854_dp.set(self.freq_854)
                self.dds_854_dp.set_att(self.att_854)

                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_866_dp.set_att(self.attenuation_866)

                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(drive_854_time)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()
                delay(5*us)

                #qubit readout
                num_pmt_pulses=self.seq.readout_397.run()
                delay(5*us)

                # 854 repump
                self.seq.repump_854.run()
                delay(5*us)

                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                self.experiment_data.insert_nd_dataset("pmt_counts", [freq_i, sample_i], num_pmt_pulses)
                total_pmt_counts += num_pmt_pulses

                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1
                
                delay(3*ms)
                
                
        
            # Update the datasets
            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_scan)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_scan)
                
            self.experiment_data.append_list_dataset("time", drive_854_time/us)
            
            freq_i += 1
            delay(10*ms)

        self.seq.ion_store.run()

    
    def analyze(self):

            
            freq=self.get_dataset("time")
            PMT_count=self.get_dataset('pmt_counts_avg')

            self.fitting_func.fit(freq, PMT_count)

    





