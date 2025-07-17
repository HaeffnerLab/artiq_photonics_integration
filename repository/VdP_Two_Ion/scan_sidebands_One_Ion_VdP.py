from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_sidebands_One_Ion_VdP(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("enable_coarse_line_scan", BooleanValue(False))
        self.setattr_argument("enable_854", BooleanValue(False))
        self.setattr_argument("enable_human_check", BooleanValue(False))

        self.setattr_argument("enable_measurement", BooleanValue(False))
        self.setattr_argument("phase_shift", NumberValue(default=0.0, min=0.0, max=360, precision=8))

    def submit_measurement(self, 
                   
                    channel="calibration_main")->np.int32:
        
        expid_3_1 = {
            "file": "VdP_Two_Ion/Tickle/A6_Tickle_VdP1_Wigner.py",
            "class_name": "A6_Tickle_VdP1mode_Wigner_AWG_Cam",
            "arguments": {
               
                "enable_tickle":True,
                "tickle_phase": self.phase_shift,
                "enable_img_readout":True
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)
    
    def submit_sidebands(self, 
                    line="BSB_mode_single_ion", #2RSB_mode2
                    # rabi_t=1000,
                    # range=0.002, 
                    # awg_power=0.03, 
                    # num_points=30,
                    channel="calibration_main")->np.int32:
        
        #self.parameter_manager.get_param("frequency/729_sp")
        freq_sp=self.get_dataset("__param__frequency/729_sp")

        if line == 'BSB_mode_single_ion':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp-0.65*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp-0.45*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  35,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__VdP1mode/att_729_dp"),
                    "att_729_sp":self.get_dataset("__param__VdP1mode/att_BSB_sp"),
                    "rabi_t": 10*us,
                    "cooling_option": "opticalpumping",
                    "samples_per_time":50,
                    "Ca_line":line,

                    "enable_854":self.enable_854,
                    "att_854":self.get_dataset("__param__VdP1mode/att_854"),
                    "att_866":self.get_dataset("__param__VdP1mode/att_866"),
                    "enable_human_check": self.enable_human_check
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == '2RSB_mode_single_ion':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp+1.0*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp+1.12*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  30,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__VdP1mode/att_729_dp"),
                    "att_729_sp":self.get_dataset("__param__VdP1mode/att_2RSB_sp"),
                    "rabi_t": 25*us,
                    "cooling_option": "opticalpumping",
                    "samples_per_time":50,
                    "Ca_line":line,

                    "enable_854":self.enable_854,
                    "att_854":self.get_dataset("__param__VdP1mode/att_854"),
                    "att_866":self.get_dataset("__param__VdP1mode/att_866"),
                    "enable_human_check": self.enable_human_check

                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
   
        return self.scheduler.submit(channel,  expid_3_1)


    def submit_line(self, 
                    line="Sm1_2_Dm5_2", 
                    rabi_t=1000,
                    range=0.002, 
                    awg_power=0.03, 
                    num_points=30,
                    channel="calibration_main")->np.int32:

        cooling_option="opticalpumping"
        
        expid_3_1 = {
            "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_AWG.py",
            "class_name": "A6_Rabi_Freq_AWG_Cam",
            "arguments": {
                "scan_freq_729_dp": {
                                     "start": self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                     "stop": self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                     "npoints":  num_points,
                                     "randomize": False,  
                                     "ty": "RangeScan"
                                    },
                "amp_729_sp":awg_power,
                "rabi_t": rabi_t*us,
                "cooling_option": cooling_option,
                "samples_per_time":50,
                "enable_human_check": self.enable_human_check
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)
    
    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())
    # @kernel
    def run(self):
        
        #scan the lines precisely
        if self.enable_coarse_line_scan:
            rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=100, range=0.06, awg_power=0.15,  num_points=60)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)
############################################################################################################
        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_sidebands("2RSB_mode_single_ion")
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_sidebands("BSB_mode_single_ion")
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)
        
        if self.enable_measurement:
            rid=self.submit_measurement()
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)