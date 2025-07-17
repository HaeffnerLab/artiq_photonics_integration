from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para

class A6_Rabi_Freq_AWG_Sp_Motion(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.seq.cam_two_ions.build()

        ######################################################################################################################################
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=2000*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="rabi"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=30*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 nm double-pass laser attenuation for Rabi excitation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=40*MHz, max=260*MHz, unit="MHz", precision=8),
            tooltip="729 nm double-pass laser frequency for Rabi excitation",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_sp",
            NumberValue(default=30*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 nm single-pass laser attenuation for Rabi excitation",
            group="rabi"
        )
        self.setattr_argument(
            "amp_729_dp",
            NumberValue(default=0.5, min=0.0, max=1.0, precision=8),
            tooltip="729 nm double-pass laser amplitude for Rabi excitation",
            group="rabi"
        ) 
        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of measurements to average for each frequency point",
        )
        self.setattr_argument(
            "num_points",
            NumberValue(default=45, precision=0, step=1),
            tooltip="Number of points to scan",
        )
        self.setattr_argument(
            "freq_range",
            NumberValue(default=0.003*MHz, min=0*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="Frequency range to scan"
        )
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="Frequency difference between double-pass laser positions for two ions",
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool_mode1","sidebandcool_mode2", "sidebandcool2mode", "opticalpumping", "sidebandcool_single_ion"], default="opticalpumping"))
        self.setattr_argument("vib_mode", EnumerationValue(["mode1","mode2","mode_single_ion"], default="mode_single_ion"))
        
        self.freq_vib1=self.get_vib_freq1()
        self.freq_vib2=self.get_vib_freq2()
        self.sideband_mode1_att729=self.parameter_manager.get_float_param('sideband2mode/mode1_att_729')
        self.sideband_mode1_att854=self.parameter_manager.get_float_param('sideband2mode/mode1_att_854')
        self.sideband_mode2_att729=self.parameter_manager.get_float_param('sideband2mode/mode2_att_729')
        self.sideband_mode2_att854=self.parameter_manager.get_float_param('sideband2mode/mode2_att_854')

    def get_qubit_freq(self)->float:
        return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_vib_freq1(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq1', archive=False)
    def get_vib_freq2(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq2', archive=False)
    
    def prepare(self):
        if self.vib_mode=="mode1":
            self.vib_freq=self.parameter_manager.get_param("VdP2mode/vib_freq1")
        elif self.vib_mode=="mode2":
            self.vib_freq=self.parameter_manager.get_param("VdP2mode/vib_freq2")
        elif self.vib_mode=="mode_single_ion":
            self.vib_freq=self.parameter_manager.get_param("VdP1mode/vib_freq")

        self.freq_sp=self.parameter_manager.get_param("frequency/729_sp")
        self.freq_729_RSB_sp=np.linspace(self.freq_sp+self.vib_freq-self.freq_range, self.freq_sp+self.vib_freq+self.freq_range, self.num_points)
        self.freq_729_BSB_sp=np.linspace(self.freq_sp-self.vib_freq-self.freq_range, self.freq_sp-self.vib_freq+self.freq_range, self.num_points)

        # Create datasets
        num_samples = self.num_points*2
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)

        self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=False,
            fit_data_name='fit_signal',
            pos_data_name='pos'

        )

        # shuffle the frequency arrays
        self.indices = [i for i in range(self.num_points)]
        np.random.shuffle(self.indices)


    @kernel
    def rabi_AWG(self, pulse_time, 
                 freq_729_dp, 
                 att_729_dp,
                 freq_729_sp, 
                 att_729_sp
                 ):

        self.seq.rabi.run(pulse_time,
                        freq_729_dp,
                        freq_729_sp,
                        att_729_dp,
                        att_729_sp,
                        amp_729_dp=self.amp_729_dp)
        

    @kernel
    def exp_seq(self, rabi_t, 
                freq_729_dp, 
                att_729_dp,
                freq_729_sp, 
                att_729_sp,
                ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()
        freq_diff_dp = self.freq_diff_dp if ion_status_detect==2 else 0.0
        if self.cooling_option == "sidebandcool_single_ion":
            self.seq.sideband_cool.run(freq_diff_dp=freq_diff_dp)
        elif self.cooling_option == "sidebandcool_mode2":
            self.seq.sideband_cool.run(freq_offset=self.freq_vib2, 
                                           att_729_here=self.sideband_mode2_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.sideband_mode2_att854) 
        elif self.cooling_option == "sidebandcool_mode1":
          
            self.seq.sideband_cool.run(freq_offset=self.freq_vib1, 
                                           att_729_here=self.sideband_mode1_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.sideband_mode1_att854) 
            
            
        elif self.cooling_option == "sidebandcool2mode":
            self.seq.sideband_cool_2mode.run(freq_diff_dp=freq_diff_dp) 
        else:
            self.seq.op_pump.run(freq_diff_dp=freq_diff_dp) 
        delay(5*us)
        
        # rabi 
        self.rabi_AWG(
            rabi_t, 
            freq_729_dp+freq_diff_dp, 
            att_729_dp,
            freq_729_sp, 
            att_729_sp
                )
        
        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()

        self.seq.cam_two_ions.cam_setup()

        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1

        #detecting the initial position of the ion 
        # while ion_status_detect_last!=1 and ion_status_detect_last!=2:
        #     delay(2*ms)
        #     self.seq.repump_854.run()
        #     self.seq.doppler_cool.run()
        #     delay(5*us)
        #     ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
        #     self.seq.ion_store.run()
        #     delay(1*ms)
        
        if(ion_status_detect_last==3): 
            i=self.num_points*2
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        i=0
        while i < self.num_points*2:

            total_thresh_count = 0
            sample_num=0

            j=i//2
            if i%2==0:
                freq_729_sp =self.freq_729_RSB_sp[self.indices[j]]
            else:
                freq_729_sp =self.freq_729_BSB_sp[self.indices[j]]


            delay(20*us)
            self.seq.ion_store.run()
            
           
            num_try_save_ion = 0 
            self.core.break_realtime()

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(self.rabi_t, 
                                 self.freq_729_dp, 
                                 self.att_729_dp, 
                                 freq_729_sp, 
                                 self.att_729_sp, 
                                 ion_status_detect)
                    ################################################################################
                    ion_status=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()
                    delay(50*us)
                    ################################################################################
                    if ion_status==0: #if the ion is not bright then it's possible it's being kicked
                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        ion_status_detect=self.seq.cam_two_ions.cam_readout() #by the way get the position
                        self.seq.ion_store.run()
                        delay(20*us)
                    else: 
                        ion_status_detect=ion_status

                      
                    if (ion_status_detect==ion_status_detect_last  and ion_status_detect==1): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [i, sample_num],
                        #                             cam_input[0])
                        
                        if ion_status==0:
                            total_thresh_count += 1

                        #total_pmt_counts += cam_input[0]

                        self.core.break_realtime()
                    elif ion_status_detect==ion_status_detect_last and ion_status_detect==2: 
                        self.seq.rf.tickle()
                    elif (ion_status_detect==1 or ion_status_detect==2):
                        ion_status_detect_last=ion_status_detect
                        self.seq.ion_store.run()
                        delay(1*s)
                        self.seq.doppler_cool.run()
                        self.seq.ion_store.run()
                    
                    # print(ion_status_detect)
                    # delay(10*ms)

                else:
                    self.seq.ion_store.run()
                    self.seq.rf.save_ion()
                    self.seq.doppler_cool.run()
                    ion_status_detect=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()

                    if ion_status_detect==1 or ion_status_detect==2:
                        num_try_save_ion = 0
                        ion_status_detect_last=ion_status_detect
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>60):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break
                    delay(1*ms)

            if i%2==0:
                self.experiment_data.insert_nd_dataset("frequencies_MHz", self.num_points+self.indices[j], freq_729_sp/MHz)
                self.experiment_data.insert_nd_dataset("pos", self.num_points+self.indices[j], 2)
                self.experiment_data.insert_nd_dataset("pmt_counts_avg", self.num_points+self.indices[j], float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.insert_nd_dataset("frequencies_MHz", self.indices[j], (self.freq_sp*2-freq_729_sp)/MHz)
                self.experiment_data.insert_nd_dataset("pos", self.indices[j], 1)
                self.experiment_data.insert_nd_dataset("pmt_counts_avg", self.indices[j], float(total_thresh_count) / self.samples_per_time)
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()

    def analyze(self):
        freq=self.get_dataset("frequencies_MHz")
        PMT_count=self.get_dataset('pmt_counts_avg')

        # Calculate the average PMT count for each frequency

        success1, fitted_curve1, params1 = find_peak_lorentzian(freq[:self.num_points], PMT_count[:self.num_points])
        success2, fitted_curve2, params2 = find_peak_lorentzian(freq[self.num_points:], PMT_count[self.num_points:])

        if success1 and success2:

            self.set_dataset('fit_signal', np.concatenate((fitted_curve1, fitted_curve2)), broadcast=True)

            peak1=self.freq_sp*2-params1[1]*MHz #BSB
            peak2=params2[1]*MHz

            self.parameter_manager.set_param(
                "VdP1mode/vib_freq",
                (peak2-peak1)/2,
                "MHz"
            )