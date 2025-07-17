from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *
from artiq.language.core import now_mu

from acf.function.fitting import *

class ScanLineTriggeredOffset(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()

        #self.setup_fit(fitting_func, 'Sin' ,-1)
        
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")

        self.setattr_argument(
            "scan_offset_t",
            Scannable(
                default=RangeScan(
                    start=50*us,
                    stop=10000*us,
                    npoints=100
                ),
                global_min=20*us,
                global_max=16.67*1000*us,
                global_step=1*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )


        self.setattr_argument(
            "rabi_t",
            NumberValue(default=10*us, min=0.1*us, max=100*us, unit="us", precision=6),
            tooltip="729 double pass frequency",
        )

	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=233.7*MHz, min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument("enable_thresholding", BooleanValue(False))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=40, precision=0, step=1),
            tooltip="Threshold PMT counts",
        )

        self.setattr_device("ttl1")             #input the line trigger signal
        #self.setattr_device("ttl12")            #sets drivers of TTL12 as attributes to see the ha[[e]]

        self.trigger=self.ttl1
        #self.ttl_out=self.ttl12


    # def prepare(self):
    #     self.fitting_func.setup(len(self.scan_offset_t.sequence))

    @kernel(flags={"fast-math"})
    def wait_trigger(self, time_gating_mu, time_holdoff_mu):
        """
        Trigger off a rising edge of the AC line.
        Times out if no edges are detected.
        Arguments:
            time_gating_mu  (int)   : the maximum waiting time (in machine units) for the trigger signal.
            time_holdoff_mu (int64) : the holdoff time (in machine units)
        Returns:
                            (int64) : the input time of the trigger signal.
        """ 

        gate_open_mu = now_mu() #current time on the timeline (int kernel)
                                #self.core.get_rtio_counter_mu (hardware time cursor)
        self.trigger._set_sensitivity(1)
    
        t_trig_mu = 0
        while True:
            t_trig_mu = self.trigger.timestamp_mu(gate_open_mu + time_gating_mu)
            if t_trig_mu < 0 or t_trig_mu >= gate_open_mu:
                break
        
        #self.trigger.count(self.core.get_rtio_counter_mu() + time_holdoff_mu) #drain the FIFO to avoid input overflow

        at_mu(self.core.get_rtio_counter_mu()+2000)

        self.trigger._set_sensitivity(0)

        at_mu(self.core.get_rtio_counter_mu() + time_holdoff_mu) #set the current time (software) to be the same as the current hardware timeline + a shift in time

        # if t_trig_mu < 0:
        #     raise Exception("MissingTrigger")

        return t_trig_mu

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        # Create datasets
        num_freq_samples = len(self.scan_offset_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("offset_t", num_freq_samples, broadcast=True)
       

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="offset_t",
            pen=False
        )

        # Init devices
        self.core.break_realtime()
        self.dds_397_dp.init()
        self.dds_397_far_detuned.init()
        self.dds_866_dp.init()
        self.dds_729_dp.init()
        self.dds_729_sp.init()
        self.dds_854_dp.init()

        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(1*ms)

        # Set frequencies
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_dp.set(self.freq_729_dp)
        self.dds_854_dp.set(self.frequency_854_dp)
        delay(1*ms)

        time_i = 0

        for offset_time in self.scan_offset_t.sequence: 
            total_thresh_count = 0
            total_pmt_counts = 0

            sample_num=0
            while sample_num<self.samples_per_time:# repeat N times
                #print(self.core.seconds_to_mu(offset_time))
                
                flag = self.wait_trigger(self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(offset_time) )
                # if flag is zero, then just abandon the loop
                if flag <0 : continue
                sample_num+=1

                delay(50*us)
            
                #  Cool
                
                self.seq.doppler_cool.run()
                self.dds_397_dp.set(self.frequency_397_resonance)
                self.dds_397_dp.set_att(self.attenuation_397) 
                delay(10*us)

                self.seq.sideband_cool.run()

                delay(10*us)

                # Attempt Rabi flop
                self.dds_729_dp.set(self.freq_729_dp)
                self.dds_729_dp.set_att(self.attenuation_729_dp)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(self.rabi_t)
                self.dds_729_dp.sw.off()
                #self.dds_729_sp.sw.off()

                delay(10*us)

                num_pmt_pulses=self.seq.readout_397.run()

                delay(10*us)

                # 854 repump
               
                self.seq.repump_854.run()

                delay(10*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [time_i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses
                
                delay(1*ms)

               

            
            self.experiment_data.append_list_dataset("offset_t", offset_time / us)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            time_i += 1
            delay(30*ms)

        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.set_att(10*dB)
        self.dds_854_dp.sw.on()

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.cfg_sw(True)
        self.dds_866_dp.sw.on()
    
    def analyze(self):
        pass
        #rabi_time=self.get_dataset("rabi_t")
       # rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        #self.fitting_func.fit(rabi_time, rabi_PMT)


    
    
