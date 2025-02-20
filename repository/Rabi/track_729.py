from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d

class track_729(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        self.build_calibrate()
        self.setattr_argument("cooling_option", EnumerationValue(["opticalpumping", "nothing"], default="nothing"))
        self.setattr_argument("enable_collision_detection", BooleanValue(True))
        self.setattr_argument(
            "samples_total",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        self.setattr_argument(
            "samples_per_freq",
            NumberValue(default=25, precision=0, step=1),
            tooltip="Number of samples to take for each frequency",
        )
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )
    def prepare(self):
        self.experiment_data.set_list_dataset("qubit_freq_MHz", self.samples_total, broadcast=True)
       

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "qubit_freq_MHz",
            pen=False
        )
        self.prepare_calibrate()

    def get_qubit_freq(self, mS=0.0, mD=0.0)->float:
        if np.abs(mD+2.5)<1e-5:
            return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
        elif np.abs(mD+0.5)<1e-5:
            return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    
    # def Solve_center

    # def Solve_B(self, mS1, mD1, mS2, mD2, gS, gD, freq_1, freq_2):
    #     '''
    #     freq_1: MHz = B*g['D52']*mD1*muB/(h*10^6) -B*g['S12']*mS1*muB/(h*10^6) + linecenter
    #     freq_2: MHz = B*g['D52']*mD2*muB/(h*10^6) -B*g['S12']*mS2*muB/(h*10^6) + linecenter
    #     '''

    #     B_field= (freq_1-freq_2)/(gD*mD1*muB/(h*1e6) -gS*mS1*muB/(h*1e6) - gD*mD2*muB/(h*1e6) +gS*mS2*muB/(h*1e6) )

    #     linecenter=freq_1-B_field*(gD*mD1*muB/(h*1e6) -gS*mS1*muB/(h*1e6))

    #     return B_field, linecenter

        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        last_time_calibrate=-5000*s
        self.core.break_realtime()

        #################################################################################################################################
        i=0
        while i<self.samples_total:
            delay(20*us)
            self.seq.ion_store.run()
    
            #calibrate qubit frequency
            if self.core.mu_to_seconds(now_mu())-last_time_calibrate>self.cal_interval and self.enable_calibration:
                self.calibrate_freq_qubit(-0.5,-2.5)
                freq=self.update_729_freq(-0.5,-2.5)
                self.experiment_data.append_list_dataset("qubit_freq_MHz", freq)

                last_time_calibrate=self.core.mu_to_seconds(now_mu())

                i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)

############################################################################################################################################################################3

    def prepare_calibrate(self):
        self.experiment_data.set_list_dataset('cal_fit_signal', self.cal_num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_count", self.cal_num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_freq", self.cal_num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("cal_pos", self.cal_num_samples, broadcast=True)

    def build_calibrate(self):

        self.setattr_argument("enable_calibration", BooleanValue(True), group="calibrate_qubit")

        self.setattr_argument(
            "cal_num_samples",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group="calibrate_qubit"
        )
        self.setattr_argument(
            "cal_freq_range",
            NumberValue(default=0.006*MHz, min=0*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="calibrate_qubit"
        )

        self.setattr_argument(
            "cal_rabi_t",
            NumberValue(default=100*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="calibrate_qubit"
        )

        self.setattr_argument(
            "cal_interval",
            NumberValue(default=20*s, min=0*s, max=500*s, unit="s",precision=8),
            group="calibrate_qubit"
        )

    
    @kernel
    def calibrate_freq_qubit(self, mS = 0.0, mD = 0.0):

        freq_729_dp=self.get_qubit_freq(mS,mD)
        print("calibration: ",freq_729_dp)
        self.core.break_realtime()
        self.seq.ion_store.run()
        self.core.break_realtime()
        i=0
        while i < self.cal_num_samples:

            total_thresh_count = 0
            sample_num=0
            rabi_t=self.cal_rabi_t
            freq_729_dp_here = freq_729_dp-self.cal_freq_range+ self.cal_freq_range*2/self.cal_num_samples*i
            num_try_save_ion = 0 

            delay(20*us)
            self.seq.ion_store.run()
            self.core.break_realtime()
            is_ion_good= True
           

            while sample_num<self.samples_per_freq:

                if is_ion_good:
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue

                    delay(50*us)
                    
                    #protect ion
                    self.seq.ion_store.run()
                    #854 repump
                    self.seq.repump_854.run()
                    # Cool
                    self.seq.doppler_cool.run()

                    if self.cooling_option=="opticalpumping":
                        self.seq.op_pump.run()
                    
                    # Attempt Rabi flop
                    self.seq.rabi.run(rabi_t,
                                    freq_729_dp_here,
                                    self.freq_729_sp,
                                    self.att_729_dp,
                                    self.att_729_sp
                    )
                    delay(10*us)

                    #qubit readout
                    num_pmt_pulses=self.seq.readout_397.run()
                    delay(10*us)

                    if num_pmt_pulses < self.threshold_pmt_count and self.enable_collision_detection:
                        # 854 repump
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()

                        num_pmt_pulses_detect=self.seq.readout_397.run()
                        self.seq.ion_store.run()
                        delay(20*us)

                        if num_pmt_pulses_detect < self.threshold_pmt_count:
                            is_ion_good = False
                    
                    if is_ion_good:
                        self.seq.ion_store.run()
                        sample_num += 1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [freq_i, sample_num],
                        #                             num_pmt_pulses)
                                                    
                        #update the total count & thresolded events
                        #total_pmt_counts += num_pmt_pulses
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        delay(2*ms)
                        
                else:
                    self.seq.ion_store.run()
                    delay(0.2*s)
                    self.seq.doppler_cool.run()
                    num_pmt_pulses_detect=self.seq.readout_397.run()
                    if num_pmt_pulses_detect >= self.threshold_pmt_count:
                        is_ion_good = True
                        num_try_save_ion = 0
                    else:
                        num_try_save_ion +=1
                    
                    if num_try_save_ion > 120:
                        print("Ion Lost")
                        i=1000000
                        sample_num+=100000
                        break

            self.seq.ion_store.run()
            
            self.experiment_data.insert_nd_dataset("cal_pos",i,  1)
            self.experiment_data.insert_nd_dataset("cal_freq",i,  freq_729_dp_here/MHz)
            self.experiment_data.insert_nd_dataset("cal_count", i, 
                                        float(total_thresh_count) / self.samples_per_freq)


            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)


    @rpc
    def update_729_freq(self, mS=0.0, mD=0.0)->float:
        freq=self.get_dataset("cal_freq")
        PMT_count=self.get_dataset('cal_count')

        is_success, fitted_array, param=find_peak_lorentzian(freq, PMT_count)

        peak=param[1]

        freq_729_dp=self.get_qubit_freq(mS, mD)

        #update frequency of 729 
        if is_success and np.abs(peak*MHz-freq_729_dp)<self.cal_freq_range:
            self.set_dataset('cal_fit_signal', fitted_array, broadcast=True)
            print("Finished Calibration: ", peak, " from: ",freq_729_dp/MHz)

            if mS == 0.5 and mD == -1.5:
                self.parameter_manager.set_param("qubit/S1_2_Dm3_2", peak*MHz, "MHz")
            elif mS == -0.5 and mD == -2.5:
                self.parameter_manager.set_param('qubit/Sm1_2_Dm5_2', peak*MHz, "MHz")
            else:
                self.parameter_manager.set_param("qubit/cal_freq_qubit", peak*MHz, "MHz")
        return  peak*MHz