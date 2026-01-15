from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *
from acf.function.fitting import *


from artiq.coredevice.ad9910 import PHASE_MODE_ABSOLUTE, PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING

class Sigma_Calibrate(_ACFExperiment):

    def build(self):
    
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)

        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("attenuation/729_dp")

        self.add_arg_from_param("EIT_cooling/freq_397_sigma")
        self.add_arg_from_param("EIT_cooling/att_397_sigma")

        self.setattr_argument(
            "samples_per_scan",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each scan configuration",
        )
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
        
        self.setattr_argument(
            "Ramsey_pulse_time",
            NumberValue(default=0.1*us, min=0.*us, max=100*us, unit='us'),
            tooltip="Ramsey pulse time if don't scan this dimension"
        )   
        self.setattr_argument(
            "Ramsey_phase",
            NumberValue(default=0.25, min=0, max=1, precision=8),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns) if don't scan this dimension"
        )

        self.setattr_argument(
            "Ramsey_wait_time",
            Scannable(
                default=RangeScan(
                    start=3.*us,
                    stop=10000*us,
                    npoints=100
                ),
                global_min=3*us,
                global_max=100000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for Ramsey wait time.",
            group='Ramsey scan setting'
        )   

       

    def prepare(self):
        self.fitting_func.setup(len(self.Ramsey_wait_time.sequence))
        # Create datasets
        num_freq_samples = len(self.Ramsey_wait_time.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
            fit_data_name='fit_signal'
        )


    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        #set dds to tracking mode
        self.dds_729_dp.set_phase_mode(PHASE_MODE_TRACKING)

        delay(50*us)
        for time_i in range(len(self.Ramsey_wait_time.sequence)): 
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0
            wait_t = self.Ramsey_wait_time.sequence[time_i]
            delay(200*us)
            self.seq.ion_store.run()


            self.dds_397_sigma.set(self.EIT_cooling_freq_397_sigma)
            self.dds_397_sigma.set_att(self.EIT_cooling_att_397_sigma)

            delay(200*us)

            while sample_num<self.samples_per_scan:
                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(20*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)
                
                self.seq.off_dds.run()
                self.seq.repump_854.run()
                #  Cool
                self.seq.doppler_cool.run()
                self.seq.sideband_cool.run()
                ########################################################################################################################

                #record current time for time tracking purpose
                at_mu(now_mu() & ~7)
                start_time_mu = now_mu()
                delay(5*us)
             
                self.dds_729_dp.set(self.frequency_729_dp)
                self.dds_729_dp.set_att(self.attenuation_729_dp)

                delay(5*us)
                
                # Attempt Rabi flop
                self.dds_729_dp.sw.on()
                delay(self.Ramsey_pulse_time)
                self.dds_729_dp.sw.off()


                
                self.dds_397_sigma.sw.on()

                delay(wait_t-2.0*us)
                #tmp_now = now_mu()
                #at_mu(now_mu() & ~7)
                #set pi/2 & Attempt Rabi flop
                #at_mu(tmp_now)
                delay(2.0*us)
                self.dds_397_sigma.sw.off()


                self.dds_729_dp.sw.on()
                delay(self.Ramsey_pulse_time)
                self.dds_729_dp.sw.off()
                ########################################################################################################################

                #read out
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                # Update dataset
                # self.experiment_data.insert_nd_dataset("pmt_counts",
                #                             [time_i, sample_num],
                #                             num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses

                delay(1*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", wait_t / us)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_scan)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_scan)
            delay(5*ms)

        self.seq.ion_store.run()
