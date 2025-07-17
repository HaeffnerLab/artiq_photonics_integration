from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *
import numpy as np
from artiq.coredevice.ad9910 import (
        RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_DEST_FTW, RAM_DEST_POWASF,
        RAM_MODE_CONT_RAMPUP, RAM_MODE_RAMPUP, PHASE_MODE_ABSOLUTE,
        PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING, RAM_MODE_CONT_BIDIR_RAMP
    )

class RamRamsey(_ACFExperiment):

    def build(self):
    
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()

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
        self.add_arg_from_param("readout/pmt_sampling_time")
        self.add_arg_from_param("doppler_cooling/cooling_time")


        self.setattr_argument(
            "repump_854_time",
            NumberValue(default=100*us, min=5*us, max=1*ms, unit="us"),
            tooltip="Time to run 854 repump",
        )
        self.setattr_argument(
            "samples_per_scan",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each scan configuration",
        )
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Threshold PMT counts",
        )

        self.setattr_argument("Scan_Type", EnumerationValue(["Ramsey_wait_time", "Ramsey_pulse_time", "Ramsey_phase"], default="Ramsey_wait_time"))

        self.setattr_argument(
            "Time_Step",
            NumberValue(default=10, min=0, precision=0, max=1000, step=1),
            tooltip="Time Step of each Ram points (in unit of 4ns)",
        )

        self.setattr_argument(
            "Ramsey_wait_time_single",
            NumberValue(default=1, min=0, max=199),
            tooltip="Ramsey wait time if don't scan this dimension in unit of Time_Step",
            group='Ramsey non-scan setting'
        )
        self.setattr_argument(
            "Ramsey_pulse_time_single",
            NumberValue(default=1, min=0, max=199),
            tooltip="Ramsey pulse time if don't scan this dimension in unit of Time_Step",
            group='Ramsey non-scan setting'
        )   
        self.setattr_argument(
            "Ramsey_phase_single",
            NumberValue(default=0, min=0, max=1),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns) if don't scan this dimension",
            group='Ramsey non-scan setting'
        )



        self.setattr_argument(
            "Ramsey_wait_time",
            Scannable(
                default=RangeScan(1, 199, 10),   # Start at 1, end at 10, step by 1
                global_min=0, global_max=199  # Optional global bounds for the scan
            ),
            tooltip="Scan parameter for Ramsey wait time.",
            group='Ramsey scan setting'
        )   
        self.setattr_argument(
            "Ramsey_pulse_time",
            Scannable(
                default=RangeScan(1, 199, 10),   # Start at 1, end at 10, step by 1
                global_min=0, global_max=199  # Optional global bounds for the scan
            ),
            tooltip="Scan parameter for Ramsey pulse time.",
            group='Ramsey scan setting'
        )
        self.setattr_argument(
            "Ramsey_phase",
            Scannable(
                default=RangeScan(
                    start=0.0,
                    stop=1.0,
                    npoints=100
                )
            ),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns)",
            group='Ramsey scan setting'
        )

        self.len_dds_ram_data=500 #maximum size=400
        # if self.Scan_Type == "Ramsey_wait_time":
        #     self.len_dds_ram_data=self.Ramsey_wait_time.sequence[-1]+2*self.Ramsey_pulse_time_single
        # elif self.Scan_Type == "Ramsey_pulse_time":
        #     self.len_dds_ram_data=self.Ramsey_pulse_time.sequence[-1]*2+self.Ramsey_wait_time_single
        # else:
        #     self.len_dds_ram_data=2*self.Ramsey_pulse_time_single+self.Ramsey_wait_time_single

        self.amp_array=[0.0]*self.len_dds_ram_data
        self.phase_array=[0.0]*self.len_dds_ram_data
        self.ram_data_array=[0]*self.len_dds_ram_data

        # the zero amplitude part at the beginning & end
        self.len_zero_amp=5

        

    @kernel
    def Ramsey(self, pulse_time:np.int32, wait_time:np.int32, phase:float):
        #self.stateprep.run(self)

        # self.seq.state_prepare.run()

    
        #generate ram file
        for i in range(pulse_time): 
            self.amp_array[i+self.len_zero_amp]=1.
            self.phase_array[i+self.len_zero_amp]=0.0
        for i in range(wait_time): 
            self.amp_array[pulse_time+i+self.len_zero_amp]=0.0
            self.phase_array[pulse_time+i+self.len_zero_amp]=0.0
        for i in range(pulse_time): 
            self.amp_array[pulse_time+wait_time+i+self.len_zero_amp]=1.
            self.phase_array[pulse_time+wait_time+i+self.len_zero_amp]=phase

        total_time=pulse_time*2+wait_time+2*self.len_zero_amp

        self.init_dds(total_time)

        self.dds_729_dp.sw.on()
        self.dds_729_dp.cpld.io_update.pulse_mu(8)
        
        delay((total_time)*4*ns*self.Time_Step)
        self.dds_729_dp.sw.off()

    @kernel
    def init_dds(self, total_ramsey_length:np.int32):

        dds=self.dds_729_dp

        dds.cpld.init()
        dds.init()
        dds.set_cfr1(ram_enable=0)#This is the correct mode for loading or reading values
        dds.cpld.set_profile(0)
        dds.cpld.io_update.pulse_mu(8) #this sends an 8 machine unit long pulse of TTL signal internally to trigger the updated ram_enable value

        dds.set_profile_ram(
                                start=0,
                                end=total_ramsey_length- 1,
                                step=np.int32(self.Time_Step), #this controls how long one point last (step*t_DDS[4ns] )
                                profile=0,
                                mode=RAM_MODE_CONT_RAMPUP,
                                # nodwell_high=1
                            )
        
        dds.cpld.set_profile(0)
        dds.cpld.io_update.pulse_mu(8)#another ttl pulse to apply the previous updates

        self.dds_729_dp.turns_amplitude_to_ram(self.phase_array, self.amp_array, self.ram_data_array)
        for i in range(len(self.phase_array)):
            self.ram_data_array[i]=np.int32(self.ram_data_array[i])
        
        dds.write_ram(self.ram_data_array[0:total_ramsey_length])

        #self.core.break_realtime()
        delay(1*ms)

        dds.set_cfr1(
                    ram_enable=1,
                    ram_destination=RAM_DEST_POWASF, #ASF: amplitude scale factor / POW: phase offset word
                    phase_autoclear=1,
                    internal_profile=0,
                )
        dds.cpld.io_update.pulse_mu(8)
        dds.set_frequency(self.frequency_729_dp) #50ns period (1 ram point ~ 8 periods=400ns)
        dds.set_att(self.attenuation_729_dp)

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()

        scan_length=max(len(self.Ramsey_wait_time.sequence), max(len(self.Ramsey_pulse_time.sequence),len(self.Ramsey_phase.sequence)))
        
        scan_param0 =[0 for i in range(scan_length)] 
        scan_param1 =[0 for i in range(scan_length)] 
        scan_param2 =[0.0 for i in range(scan_length)]        
        scan_axis=[0.0 for i in range(scan_length)]   
        num_scan_samples = 0
        scan_name=""


        if self.Scan_Type == "Ramsey_wait_time":
            for i in range(len(self.Ramsey_wait_time.sequence)):
                scan_param0[i]=np.int32(self.Ramsey_wait_time.sequence[i])
                scan_param1[i]=np.int32(self.Ramsey_pulse_time_single)
                scan_param2[i]=self.Ramsey_phase_single

                scan_axis[i]=self.Ramsey_wait_time.sequence[i]*4/1000*self.Time_Step#to us
            num_scan_samples=len(self.Ramsey_wait_time.sequence)
            scan_name='Ramsey_wait_time_(us)'


        elif self.Scan_Type == "Ramsey_pulse_time":
            for i in range(len(self.Ramsey_pulse_time.sequence)):
                scan_param0[i]=np.int32(self.Ramsey_wait_time_single)
                scan_param1[i]=np.int32(self.Ramsey_pulse_time.sequence[i])
                scan_param2[i]=self.Ramsey_phase_single

                scan_axis[i]=self.Ramsey_pulse_time.sequence[i]*4/1000*self.Time_Step#to us
            num_scan_samples=len(self.Ramsey_pulse_time.sequence)
            scan_name='Ramsey_pulse_time_(us)'


        
        else: #"Ramsey_phase"
            for i in range(len(self.Ramsey_phase.sequence)):
                scan_param0[i]=np.int32(self.Ramsey_wait_time_single)
                scan_param1[i]=np.int32(self.Ramsey_pulse_time_single)
                scan_param2[i]=self.Ramsey_phase.sequence[i]

                scan_axis[i]=self.Ramsey_phase.sequence[i]
            num_scan_samples=len(self.Ramsey_phase.sequence)
            scan_name='Ramsey_phase_(turns)'




        # create datasets
        # num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [scan_length, self.samples_per_scan], broadcast=True)
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", scan_length, broadcast=True)
        self.experiment_data.set_list_dataset(scan_name, scan_length, broadcast=True)

        # # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name=scan_name,
            pen=True,
        )

        # Init devices#####################################################################################
        self.core.break_realtime()
        self.dds_397_dp.init()
        self.dds_397_far_detuned.init()
        self.dds_866_dp.init()
        #self.dds_729_dp.init()
        self.dds_729_sp.init()
        self.dds_854_dp.init()

        # Set attenuations #####################################################################################
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        #self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(1*ms)

        # Set frequencies #####################################################################################
        self.dds_729_sp.set(self.frequency_729_sp)
        #self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_854_dp.set(self.frequency_854_dp)
        delay(1*ms)

        # while True:
        #     self.Ramsey(40,10,0.5)
        #     delay(10*us)

        for iter in range(num_scan_samples): # scan the frequency

            phase_here=scan_param2[iter]
            wait_time_here=scan_param0[iter]
            pulse_time_here=scan_param1[iter]

            total_thresh_count = 0
            total_pmt_counts = 0
            
            for sample_num in range(self.samples_per_scan): # repeat N times
               
                delay(500*us)
                self.dds_854_dp.set_att(30*dB)
                self.dds_729_dp.sw.off()
                self.dds_729_sp.sw.off()
                self.dds_397_dp.sw.off()
                self.dds_854_dp.sw.off()
                delay(1*ms)
                
                # state_preparation
                #self.seq.state_prepare.run()
                # state_preparation
                self.seq.doppler_cool.run()
                self.dds_397_dp.set(self.frequency_397_resonance)
                self.dds_397_dp.set_att(self.attenuation_397) 
                delay(1*us)

                self.seq.sideband_cool.run()
                delay(1*us)

                self.Ramsey(pulse_time=pulse_time_here, wait_time=wait_time_here, phase=phase_here)
                # Collect counts
                
                # leave 866 at cooling frequency
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                num_pmt_pulses = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                )
                delay(5*us)
                self.dds_397_dp.sw.off()
                self.dds_866_dp.sw.off()
                
                delay(5*us)

                # 854 repump
                self.dds_854_dp.set_att(self.attenuation_854_dp)
                self.dds_854_dp.sw.on()
                delay(self.repump_854_time)
                self.dds_854_dp.sw.off()
                self.dds_854_dp.set_att(30*dB)
                delay(10*us)

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [iter, sample_num],
                                            num_pmt_pulses)
                                            
                #update the total count & thresholded events
                total_pmt_counts += num_pmt_pulses
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                delay(2*ms)
                
            
            self.experiment_data.append_list_dataset(scan_name, scan_axis[iter])


            if not self.enable_thresholding:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_pmt_counts) / self.samples_per_scan)
            else:
            	self.experiment_data.append_list_dataset("pmt_counts_avg",
                                          float(total_thresh_count) / self.samples_per_scan)
            delay(40*ms)
            self.dds_854_dp.sw.on()
            self.dds_397_far_detuned.cfg_sw(True)








''' potential code for 3D scan
        # ramsey_wait_time=scan_seq[0][0]
        # ramsey_pulse_time=scan_seq[1][0]
        # ramsey_phase=scan_seq[2][0]

        # for index0 in range(len(scan_seq[0])):
        #     for index1 in range(len(scan_seq[1])):
        #         for index2 in range(len(scan_seq[2])):

        #             ramsey_wait_time=scan_seq[0][index0]
        #             ramsey_pulse_time=scan_seq[1][index1]
        #             ramsey_phase=scan_seq[2][index2]
        #             for sample_num in range(self.samples_per_time):

        #                 self.dds_854_dp.set_att(30*dB)

        #                 self.Ramsey(wait_time=ramsey_wait_time, pulse_time=ramsey_pulse_time,phase=ramsey_phase)

        #                 num_pmt_pulses = self.ttl_pmt_input.count(
        #                     self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
        #                 )
        #                 delay(10*us)

        #                 # 854 repump
        #                 self.dds_854_dp.set_att(self.attenuation_854_dp)
        #                 self.dds_854_dp.sw.on()
        #                 delay(self.repump_854_time)
        #                 self.dds_854_dp.sw.off()
        #                 self.dds_854_dp.set_att(30*dB)
        #                 delay(10*us)

        #                 # Update dataset
        #                 self.experiment_data.insert_nd_dataset("pmt_counts",
        #                                     [index0, index1],#, sample_num
        #                                     num_pmt_pulses)
        #                 delay(2*ms)

                    # self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)
                    # self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                    #                       float(total_thresh_count) / self.samples_per_time)
'''