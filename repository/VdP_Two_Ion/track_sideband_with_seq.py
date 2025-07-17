from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import stark_shift_SDF_kernel
import time
import random

class track_sideband_with_seq(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        
        self.seq.adjust_729_freq.build()
        self.seq.calibrate_motion.build()
        self.seq.cam_two_ions.build()

        self.setattr_argument("vib_mode", EnumerationValue(["mode1","mode2","mode_single_ion","mode1_mode2"], default="mode1"))
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )

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
    def get_vib_freq0(self)->float:
        return self.get_dataset('__param__VdP1mode/vib_freq', archive=False)
    def get_vib_freq(self)->float:
        if self.vib_mode=="mode1":
            return self.get_vib_freq1()
        elif self.vib_mode=="mode2":
            return self.get_vib_freq2()
        elif self.vib_mode=="mode1_mode2":
            return self.get_vib_freq1()
        else:
            return self.get_vib_freq0()

    def prepare(self):
        self.seq.calibrate_motion.prepare()
        self.seq.adjust_729_freq.prepare()

        self.num_samples=5000
        self.experiment_data.set_list_dataset("vib_freq", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("vib_freq2", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("time", self.num_samples, broadcast=True)
        self.experiment_data.enable_experiment_monitor(
            "vib_freq",
            x_data_name="time",
            pen=False
        )
    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()

        time_start=self.core.mu_to_seconds(now_mu())

        self.seq.cam_two_ions.cam_setup()
        #################################################################################################################################
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
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
            i=1000000
        else:
            i=0
        ion_status_detect = ion_status_detect_last
        #################################################################################################################################

        i=0
        #################################################################################################################################
        while i < self.num_samples:

            self.core.break_realtime()
            self.seq.ion_store.run()

            #calibrate qubit frequency
            #if self.seq.adjust_729_freq.check_interval():
            ion_status_detect=self.seq.adjust_729_freq.calibrate_freq_qubit(
                line="Sm1_2_Dm5_2", 
               # cooling_option="opticalpumping",
                wait_time=100*us
                )
            ion_status_detect_last=ion_status_detect
            self.core.break_realtime()
            
            #if self.seq.calibrate_motion.check_interval():

            if i==0:# and False:
                if self.vib_mode=="mode1_mode2":
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(
                        vib_mode="mode1",
                        cooling_option="opticalpumping",
                        cal_freq_range=0.004*MHz,
                    )
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(
                        vib_mode="mode2",
                        cooling_option="opticalpumping",
                        cal_freq_range=0.004*MHz,
                    )
                else:
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(
                        vib_mode=self.vib_mode,
                        cooling_option="opticalpumping",
                        cal_freq_range=0.004*MHz,
                    )
            else:
                if self.vib_mode=="mode1_mode2":
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(
                        vib_mode="mode1",
                        cooling_option="opticalpumping",
                        #cal_freq_range=0.002*MHz,
                    )
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(
                        vib_mode="mode2",
                        cooling_option="opticalpumping",
                        #cal_freq_range=0.002*MHz,
                    )
                else:
                    ion_status_detect=self.seq.calibrate_motion.calibrate_freq_motion(
                        vib_mode=self.vib_mode,
                        cooling_option="opticalpumping",
                        #cal_freq_range=0.002*MHz,
                    )
            ion_status_detect_last=ion_status_detect

            self.core.break_realtime()

            self.experiment_data.insert_nd_dataset("vib_freq", i, self.get_vib_freq())
            self.experiment_data.insert_nd_dataset("time", i, self.core.mu_to_seconds(now_mu())-time_start)
            i+=1

            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()
