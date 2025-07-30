.0.........................from artiq.experiment import *
from trapped_ions_control.experiment_data import ExperimentData
from tic_setup.hardware_definition import hardware_setup
from tic_setup.arguments_definition import argument_manager
import numpy as np

class RabiTimeScannThresholded_withMSparity(EnvExperiment):

    def build(self):
        
        # Initialize devices
        self.hardware_setup = hardware_setup
        self.hardware_setup.initialize(self)

        # Set experiment arguments
        self.argument_manager = argument_manager
        self.argument_manager.initialize(self)
        self.argument_manager.set_arguments([
            "freq_397_resonance",
            "freq_397_cooling",
            "freq_397_far_detuned",
            "freq_866_cooling",
            "freq_729_sp",
            "freq_729_sp_aux",
            "freq_854_dp",
            "attenuation_397",
            "attenuation_397_far_detuned",
            "attenuation_866",
            "attenuation_729_dp",
            "attenuation_729_sp",
            "attenuation_729_sp_aux",
            "phase_729_sp",
            "phase_729_sp_aux",
            "attenuation_854_dp",
            "doppler_cooling_time",
            "pmt_sampling_time",
        ])

        self.setattr_argument(
            "scan_phase",
            Scannable(
                default=RangeScan(
                    start=0.0,
                    stop=1.0,
                    npoints=50
                ),
                global_min=0.0,
                global_max=1.0,
                global_step=0.1,
            ),
            tooltip="Scan parameter for single qubit gate phase"
        )


        self.setattr_argument(
            "repump_854_time",
            NumberValue(default=100*us, min=5*us, max=1*ms, unit="us"),
            tooltip="Time to run 854 repump",
        )

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=233.48*MHz, min=200*MHz, max=250*MHz, unit="MHz", ndecimals=4),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "MS_detuning",
            NumberValue(default=0.1*MHz, min=-0.5*MHz, max=0.5*MHz, unit="MHz", ndecimals=4),
            tooltip="detuning from the strectch mode",
        )


        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=25, ndecimals=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument(
            "OP_cycle",
            NumberValue(default=20, ndecimals=0, step=1),
            tooltip="Threshold PMT counts",
        )


        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=45, ndecimals=0, step=1),
            tooltip="Threshold PMT counts",
        )

        self.setattr_argument(
            "MS_time",
            NumberValue(default=50*us, min=1*us, max = 500*us, unit="us", ndecimals=3),
            tooltip="MS_gate_time",
        )

        self.setattr_argument(
            "sq_pi_2_time",
            NumberValue(default= 2.5*us, min=1*us, max = 500*us, unit="us", ndecimals=3),
            tooltip="sq_gate_time",
        )

        self.setattr_argument(
            "sq_pi_2_phase",
            NumberValue(default = 0.0, min=0.0, max = 1.0),
            tooltip="sq_pi_2_phase",
        )



        


        # Initialize experiment data
        self.data = ExperimentData("parity_scan", self)
    
    @kernel
    def run(self):
        print("Running the script")
        # Create datasets
        num_freq_samples = len(self.scan_phase.sequence)
        self.data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.data.set_list_dataset("phase", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="phase",
            pen=False,
        )

        # Init devices
        self.core.reset()
        self.dds_397_dp.init()
        self.dds_397_far_detuned.init()
        self.dds_866_dp.init()
        self.dds_729_dp.init()
        self.dds_729_sp.init()
        self.dds_729_sp_aux.init()
        self.dds_854_dp.init()

        axialmodes = np.array([0.089,0.153,0.214,0.272,0.326,0.380,0.432,0.482,0.532])

        sbc_freq = (239.71)
        freq_offset = (0.26)
        op_freq = (241.73)
        # print(self.phase_729_sp)
        # print(self.phase_729_sp_aux)

        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_729_sp_aux.set_att(self.attenuation_729_sp_aux)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(1*ms)

        # Set frequencies
        self.dds_729_sp.set(self.freq_729_sp)
        self.dds_729_sp_aux.set(self.freq_729_sp_aux)
        self.dds_729_dp.set(self.freq_729_dp)
        self.dds_854_dp.set(self.freq_854_dp)
        delay(1*ms)

        time_i = 0

        for sq_phase in self.scan_phase.sequence: # scan the frequency
            total_thresh_count = 0
            total_pmt_counts = 0
            for sample_num in range(self.samples_per_time): # repeat N times
                
                # Cool
                self.run_doppler_cooling()

                # Set 397 freq here for count collection, so less delay between
                # end of cooling and beginning of detection
                
                

                self.dds_397_dp.set(self.freq_397_resonance)
                delay(10*us)

                #OP
                self.dds_729_dp.set(241.9*MHz)
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(15*dB)
                self.dds_854_dp.set_att(3*dB)
                for OP_num in range(self.OP_cycle):
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(5*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()


                for GSC in range(30):
                    self.dds_729_dp.set((sbc_freq+freq_offset*2)*MHz)
                    self.dds_729_dp.set_att(15*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(20):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()

                # two sb at the same time


                for GSC in range(50):
                    self.dds_729_dp.set((sbc_freq)*MHz)
                    self.dds_729_sp.set((80+0.515)*MHz)
                    self.dds_729_sp_aux.set((80+0.515*np.sqrt(3.))*MHz)
                    self.dds_729_dp.set_att(20*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    self.dds_729_sp_aux.sw.on()
                    delay(12*us)
                    self.dds_729_dp.sw.off()
                    self.dds_729_sp_aux.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                

                self.dds_729_sp.set(80*MHz)
                self.dds_729_sp_aux.set(80*MHz)
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(30):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()


                for GSC in range(30):
                    self.dds_729_dp.set((sbc_freq+freq_offset*2)*MHz)
                    self.dds_729_dp.set_att(15*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(20):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()


                for GSC in range(30):
                    self.dds_729_dp.set((sbc_freq+freq_offset*2)*MHz)
                    self.dds_729_dp.set_att(15*dB)
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()
                    
                                  # OP on resonant
                self.dds_729_dp.set(op_freq*MHz)
                self.dds_729_dp.set_att(18*dB)

                for OP_num in range(20):
            
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()


                for Iteration in range(5):
                    for GSC in range(20):
                        self.dds_729_dp.set((sbc_freq)*MHz)
                        self.dds_729_sp.set((80+0.515)*MHz)
                        self.dds_729_sp_aux.set((80+0.515*np.sqrt(3.))*MHz)
                        self.dds_729_dp.set_att(15*dB)
                        self.dds_729_dp.sw.on()
                        self.dds_729_sp.sw.on()
                        self.dds_729_sp_aux.sw.on()
                        delay(12*us)
                        self.dds_729_dp.sw.off()
                        self.dds_729_sp_aux.sw.off()
                        self.dds_854_dp.sw.on()
                        self.dds_866_dp.sw.on()
                        delay(5*us)
                        self.dds_854_dp.sw.off()
                        self.dds_866_dp.sw.off()
                    

                    self.dds_729_sp.set(80*MHz)
                    self.dds_729_sp_aux.set(80*MHz)
                        
                                    # OP on resonant
                    self.dds_729_dp.set(op_freq*MHz)
                    self.dds_729_dp.set_att(18*dB)

                    for OP_num in range(8):
                
                        self.dds_729_dp.sw.on()
                        self.dds_729_sp.sw.on()
                        delay(7*us)
                        self.dds_729_dp.sw.off()
                        self.dds_854_dp.sw.on()
                        self.dds_866_dp.sw.on()
                        delay(4*us)
                        self.dds_854_dp.sw.off()
                        self.dds_866_dp.sw.off()

                for OP_num in range(15):
                
                    self.dds_729_dp.sw.on()
                    self.dds_729_sp.sw.on()
                    delay(7*us)
                    self.dds_729_dp.sw.off()
                    self.dds_854_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(4*us)
                    self.dds_854_dp.sw.off()
                    self.dds_866_dp.sw.off()

                # # continous cool at 0.6 MHz red detuned
                # self.dds_729_dp.set((239.69+0.26)*MHz)
                # self.dds_729_dp.set_att(18*dB)
                # self.dds_854_dp.set_att(30*dB) # change 854 detuning for optimal quench
                # self.dds_729_dp.sw.on()
                # self.dds_729_sp.sw.on()
                # self.dds_854_dp.sw.on()
                # self.dds_866_dp.sw.on()
                # delay(1*ms) # change delay for different cooling time
                # self.dds_729_dp.sw.off()
                # self.dds_854_dp.sw.off()
                # self.dds_866_dp.sw.off()
                # self.dds_854_dp.set_att(3*dB)


                # # Optical pumping

                # self.dds_729_dp.set(241.7*MHz)
                # self.dds_729_dp.set_att(18*dB)

                # for OP_num in range(50):
            
                #     self.dds_729_dp.sw.on()
                #     self.dds_729_sp.sw.on()
                #     delay(7*us)
                #     self.dds_729_dp.sw.off()
                #     self.dds_854_dp.sw.on()
                #     self.dds_866_dp.sw.on()
                #     delay(4*us)
                #     self.dds_854_dp.sw.off()
                #     self.dds_866_dp.sw.off()



                # for GSC in range(9):
                    
                    
                #     for i in range(3):
                #         self.dds_729_dp.set((239.69+2*axialmodes[i])*MHz)
                #         self.dds_729_dp.set_att(15*dB)
                #         self.dds_729_dp.sw.on()
                #         self.dds_729_sp.sw.on()
                #         delay(12*us)
                #         self.dds_729_dp.sw.off()
                #         self.dds_854_dp.sw.on()
                #         self.dds_866_dp.sw.on()
                #         delay(5*us)
                #         self.dds_854_dp.sw.off()
                #         self.dds_866_dp.sw.off()

                #     for OP_num in range(5):
                #         self.dds_729_dp.set((241.7)*MHz)
                #         self.dds_729_dp.sw.on()
                #         self.dds_729_sp.sw.on()
                #         delay(7*us)
                #         self.dds_729_dp.sw.off()
                #         self.dds_854_dp.sw.on()
                #         self.dds_866_dp.sw.on()
                #         delay(5*us)
                #         self.dds_854_dp.sw.off()
                #         self.dds_866_dp.sw.off()


                #     for i in range(8):
                #         self.dds_729_dp.set((239.69+axialmodes[i])*MHz)
                #         self.dds_729_dp.set_att(18*dB)
                #         self.dds_729_dp.sw.on()
                #         self.dds_729_sp.sw.on()
                #         #delay(10*np.sqrt(axialmodes[i]/axialmodes[0])*us)
                #         delay(15*us)
                #         self.dds_729_dp.sw.off()
                #         self.dds_854_dp.sw. on()
                #         self.dds_866_dp.sw.on()
                #         delay(5*us)
                #         self.dds_854_dp.sw.off()
                #         self.dds_866_dp.sw.off()


                #     for OP_num in range(5):
                #         self.dds_729_dp.set((241.7)*MHz)
                #         self.dds_729_dp.sw.on()
                #         self.dds_729_sp.sw.on()
                #         delay(7*us)
                #         self.dds_729_dp.sw.off()
                #         self.dds_854_dp.sw.on()
                #         self.dds_866_dp.sw.on()
                #         delay(5*us)
                #         self.dds_854_dp.sw.off()
                #         self.dds_866_dp.sw.off()

                #     for i in range(12):
                #         self.dds_729_dp.set((239.69+axialmodes[0])*MHz)
                #         self.dds_729_dp.set_att(18*dB)
                #         self.dds_729_dp.sw.on()
                #         self.dds_729_sp.sw.on()
                #         delay(18*us)
                #         self.dds_729_dp.sw.off()
                #         self.dds_854_dp.sw.on()
                #         self.dds_866_dp.sw.on()
                #         delay(5*us)
                #         self.dds_854_dp.sw.off()
                #         self.dds_866_dp.sw.off()
                #     # 239.64

                    
                    
                #     for OP_num in range(5):
                #         self.dds_729_dp.set((241.7)*MHz)
                #         self.dds_729_dp.sw.on()
                #         self.dds_729_sp.sw.on()
                #         delay(7*us)
                #         self.dds_729_dp.sw.off()
                #         self.dds_854_dp.sw.on()
                #         self.dds_866_dp.sw.on()
                #         delay(5*us)
                #         self.dds_854_dp.sw.off()
                #         self.dds_866_dp.sw.off()

                # continous cool at 0.6 MHz red detuned
                # self.dds_729_dp.set((239.69+0.3)*MHz)
                # self.dds_729_dp.set_att(9*dB)
                # self.dds_854_dp.set_att(27*dB) # change 854 detuning for optimal quench
                # self.dds_729_dp.sw.on()
                # self.dds_729_sp.sw.on()
                # self.dds_854_dp.sw.on()
                # self.dds_866_dp.sw.on()
                # delay(1*ms) # change delay for different cooling time
                # self.dds_729_dp.sw.off()
                # self.dds_854_dp.sw.off()
                # self.dds_866_dp.sw.off()
                # self.dds_854_dp.set_att(3*dB)


                  # OP on resonant
                # self.dds_729_dp.set(241.7*MHz)
                # self.dds_729_dp.set_att(18*dB)

                # for OP_num in range(30):
            
                #     self.dds_729_dp.sw.on()
                #     self.dds_729_sp.sw.on()
                #     delay(7*us)
                #     self.dds_729_dp.sw.off()
                #     self.dds_854_dp.sw.on()
                #     self.dds_866_dp.sw.on()
                #     delay(4*us)
                #     self.dds_854_dp.sw.off()
                #     self.dds_866_dp.sw.off()


                self.dds_854_dp.sw.on()

                #self.ttl_awg_trigger.pulse(1*us)
                #delay(500*us)

                self.dds_854_dp.sw.off()

                # Attempt MS Gate
                self.dds_729_dp.set(self.freq_729_dp)
                self.dds_729_sp.set((80+0.515)*MHz+self.MS_detuning, phase=self.phase_729_sp)
                self.dds_729_sp_aux.set((80-0.515)*MHz-self.MS_detuning, phase=self.phase_729_sp_aux)
                self.dds_729_dp.set_att(self.attenuation_729_dp)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                self.dds_729_sp_aux.sw.on()

                delay(self.MS_time)

                self.dds_729_dp.sw.off()
                self.dds_729_sp.sw.off()
                self.dds_729_sp_aux.sw.off()


                # analysis pulse
                self.dds_729_dp.set_att(20*dB)
                self.dds_729_sp.set_att(8*dB)
                self.dds_729_sp.set(80*MHz,phase = sq_phase)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()

                delay(self.sq_pi_2_time)

                self.dds_729_dp.sw.off()
                self.dds_729_sp.sw.off()



                # Collect counts
                
                # leave 866 at cooling frequency
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()

                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.pmt_sampling_time)
                )
                delay(10*us)

                # 854 repump
                self.dds_854_dp.set_att(self.attenuation_854_dp)
                self.dds_854_dp.sw.on()
                delay(self.repump_854_time)
                self.dds_854_dp.sw.off()
                self.dds_854_dp.set_att(30*dB)
                delay(10*us)

                # Update dataset
                self.data.insert_nd_dataset("pmt_counts",
                                            [time_i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                     total_thresh_count += 1

                if num_pmt_pulses > 110:
                    total_thresh_count += 1

                if num_pmt_pulses < 110 and num_pmt_pulses > 45:
                    total_thresh_count -= 1    

                total_pmt_counts += num_pmt_pulses

                delay(1.2*ms)
            
            self.data.append_list_dataset("phase", sq_phase)
            #self.data.append_list_dataset("pmt_counts_avg_thresholded",
            #                              float(total_pmt_counts) / self.samples_per_time)
            self.data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            time_i += 1
            delay(30*ms)

        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.set_att(10*dB)
        self.dds_854_dp.sw.on()

        self.dds_397_dp.set(self.freq_397_cooling)
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        self.dds_866_dp.sw.on()
            
    
    @kernel
    def run_doppler_cooling(self):
        self.dds_397_dp.set(self.freq_397_cooling)
        self.dds_397_far_detuned.set(self.freq_397_far_detuned)
        self.dds_866_dp.set(self.freq_866_cooling)
        
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        self.dds_866_dp.sw.on()
        
        delay(self.doppler_cooling_time * 0.6)
        
        self.dds_397_far_detuned.sw.off()
        
        delay(self.doppler_cooling_time * 0.2)

        self.dds_397_dp.set_att(15*dB)

        delay(self.doppler_cooling_time * 0.1)


        self.dds_397_dp.set_att(18*dB)

        delay(self.doppler_cooling_time * 0.1)
        
        self.dds_397_dp.set_att(self.attenuation_397)

        # self.dds_397_far_detuned.off()
        self.dds_397_dp.sw.off()
        delay(20*us)
        self.dds_866_dp.sw.off()