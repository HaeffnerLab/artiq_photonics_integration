from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

from acf.function.fitting import *

from artiq.experiment import *


class FreqScan854(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Voigt_Split', 218)

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling") #
        self.add_arg_from_param("frequency/397_far_detuned") #
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397") #
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866") #
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")


        self.setattr_argument(
            "freq_729_pi",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "amp_729_pi",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=10*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )


        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
        )

        self.setattr_argument(
            "scan_freq_854",
            Scannable(
                default=RangeScan(
                    start=60*MHz,
                    stop=95*MHz,
                    npoints=100
                ),
                global_min=60*MHz,
                global_max=120*MHz,
                global_step=1*MHz,
                unit="MHz"
            ),
            tooltip="Scan parameters for sweeping the 854 laser."
        )

        self.setattr_argument(
            "drive_time_854",
            NumberValue(default=20*us, min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for 854 excitation"
        )
        self.setattr_argument(
            "att_854",
            NumberValue(default=20*dB, min=2*dB, max=30*dB, unit="dB", precision=5),
            tooltip="854 drive attenuation"
        )

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )

        



    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_854.sequence))

        # Create datasets
        num_samples = len(self.scan_freq_854.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_freq])
        #self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="frequencies_MHz",
            pen=False,
            fit_data_name='fit_signal'
        )


    @kernel
    def rabi(self,pulse_time,frequency, phase:float=0.0):

        # in the register, the phase is pow_/65536
        # in turns (meaning how many 2pi, 1 turn means 2pi)

        self.dds_729_dp.set(frequency, phase=phase)
        self.dds_729_dp.set_att(self.amp_729_pi)
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        self.dds_729_sp_aux.sw.off()
    
    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        delay(10*us)

        
        freq_i = 0
        for freq_854 in self.scan_freq_854.sequence:
            
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
                self.seq.sideband_cool.run()
                delay(5*us)


                self.rabi(self.PI_drive_time, self.freq_729_pi,0.0)
                delay(5*us)

                #repump 854   
                self.dds_854_dp.set(freq_854)
                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_854_dp.set_att(self.att_854)
                self.dds_866_dp.set_att(self.attenuation_866)
                delay(5*us)
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(self.drive_time_854)
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
                                          float(total_thresh_count) / self.samples_per_freq)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_freq)
                
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_854/MHz)
            
            freq_i += 1
            delay(10*ms)

        self.seq.ion_store.run()

        


    def analyze(self):

            
            freq=self.get_dataset("frequencies_MHz")
            PMT_count=self.get_dataset('pmt_counts_avg')

            self.fitting_func.fit(freq, PMT_count)

    





