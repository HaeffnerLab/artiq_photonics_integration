from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class RabiTimeScan_EIT(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.eit_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.rabi.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
      
        self.setup_fit(fitting_func, 'Sin' ,-1)
        
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")


        self.setattr_argument("enable_pi_pulse", BooleanValue(False), group='Pi pulse excitation')
        self.setattr_argument(
            "freq_729_pi",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "amp_729_pi",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )

        


        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=100*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("enable_awg_trigger", BooleanValue(False))

        self.setattr_argument("enable_sideband_cool", BooleanValue(True))
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )



    @kernel
    def rabi(self,pulse_time,frequency, phase:float=0.0):

        # in the register, the phase is pow_/65536
        # in turns (meaning how many 2pi, 1 turn means 2pi)

        self.dds_729_dp.set(frequency, phase=phase)
        self.dds_729_dp.set_att(self.amp_729_pi)
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        
    
    @kernel
    def side_band_cooling_ion_chain(self):
        # # Optical pumping

        axialmodes = np.array([0.089,0.153,0.214,0.272,0.326,0.380,0.432,0.482,0.532])*(1.01685)
        # carrier_freq = (233.707)
        sbc_freq = (239.7763)
        # sbc_freq = (239.785)
        # freq_offset = (0.26)
        op_freq = (241.80)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        self.dds_729_dp.set(op_freq*MHz)
        self.dds_729_dp.set_att(18*dB)
        #     self.dds_854_dp.sw.on()
        #     self.dds_866_dp.sw.on()
        #     delay(4*us)
        #     self.dds_854_dp.sw.off()
        #     self.dds_866_dp.sw.off()

        for GSC in range(20):
            for i in range(3):
                self.dds_729_dp.set((sbc_freq+2*axialmodes[i])*MHz)
                self.dds_729_dp.set_att(15*dB)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(12*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(5*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()

            for OP_num in range(5):
                self.dds_729_dp.set((op_freq)*MHz)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(7*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(5*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()

            for i in range(8):
                self.dds_729_dp.set((sbc_freq+axialmodes[i])*MHz)
                self.dds_729_dp.set_att(18*dB)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                #delay(20*np.sqrt(axialmodes[i]/axialmodes[0])*us)
                delay(20*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw. on()
                self.dds_866_dp.sw.on()
                delay(5*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()

            for OP_num in range(5):
                self.dds_729_dp.set((op_freq)*MHz)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(7*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(5*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()

            for i in range(10):
                self.dds_729_dp.set((sbc_freq +axialmodes[0])*MHz)
                self.dds_729_dp.set_att(20*dB)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(20*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(4*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()
            # 239.64

            for OP_num in range(5):
                self.dds_729_dp.set((op_freq)*MHz)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(4*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()
        
        

        # self.dds_729_dp.set((sbc_freq +axialmodes[0])*MHz)
        # self.dds_729_dp.set_att(20*dB)
        # self.dds_854_dp.set_att(30*dB)

        # self.dds_729_dp.sw.on()
        # self.dds_729_sp.sw.on()
        # self.dds_854_dp.sw.on()
        # self.dds_866_dp.sw.on()
        # delay(1.5*ms)
        # self.dds_729_dp.sw.off()
        # self.dds_854_dp.sw.off()
        # self.dds_866_dp.sw.off()
        # self.dds_854_dp.set_att(self.attenuation_854_dp)

        # for OP_num in range(10):
        #     self.dds_729_dp.set((op_freq)*MHz)
        #     self.dds_729_dp.sw.on()
        #     self.dds_729_sp.sw.on()
        #     delay(10*us)
        #     self.dds_729_dp.sw.off()
        #     self.dds_854_dp.sw.on()
        #     self.dds_866_dp.sw.on()
        #     delay(5*us)
        #     self.dds_854_dp.sw.off()
        #     self.dds_866_dp.sw.off()


    
    def prepare(self):
        self.fitting_func.setup(len(self.scan_rabi_t.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_freq_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

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

        time_i = 0
        delay(50*us)
        
        for rabi_t in self.scan_rabi_t.sequence: 
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            #  Cool
            self.seq.ion_store.run()
            delay(200*us)

            while sample_num<self.samples_per_time:
                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1

                delay(50*us)

                #turn off all dds
                self.seq.off_dds.run()

                #854 repump
                self.seq.repump_854.run()
                
                #  Cool
                self.seq.doppler_cool.run()

                self.seq.eit_cool.run()
                self.seq.op_pump.run()

                self.seq.eit_cool.run()
                self.seq.op_pump.run()               
                delay(5*us)


                #self.side_band_cooling_ion_chain()
                #self.seq.sideband_cool_ion_chain.run()

                # Send a TTL trigger signal to AWG
                if self.enable_awg_trigger:
                    self.ttl_awg_trigger.pulse(1*us)

                # Apply pi pulse after sideband cooling to get the initial state |1>
                if self.enable_pi_pulse:
                    self.rabi(self.PI_drive_time, self.freq_729_pi,0.0)
                
                self.seq.rabi.run(rabi_t,
                                  self.freq_729_dp,
                                  self.frequency_729_sp,
                                  self.attenuation_729_dp,
                                  self.attenuation_729_sp
                )

                #qubit readout
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()

                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [time_i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses

                delay(2*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            time_i += 1
            delay(5*ms)

        self.seq.ion_store.run()
    
    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        self.fitting_func.fit(rabi_time, rabi_PMT)


    
    
