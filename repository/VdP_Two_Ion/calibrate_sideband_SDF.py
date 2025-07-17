from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_qubit_sideband(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("ion_type", EnumerationValue([
            "two_ion", "single_ion"], default="single_ion"))


      
    def submit_line(self, 
                    line="Sm1_2_Dm5_2", 
                    rabi_t=1000,
                    range=0.002, 
                    awg_power=0.03, 
                    num_points=30,
                    channel="calibration_main")->np.int32:
        
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
                "cooling_option": 'opticalpumping'
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)

    def submit_sidebands(self, 
                    line="BSB_SDF_single_ion", 
                    channel="calibration_main")->np.int32:
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")

        if line == 'BSB_SDF_single_ion':

            freq_vib=self.get_dataset("__param__VdP1mode/vib_freq")
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp-freq_vib-0.02*MHz, 
                                        "stop": freq_sp-freq_vib+0.02*MHz, 
                                        "npoints": 65,   
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":30*dB, 
                    "att_729_sp":30*dB,
                    "rabi_t": 500*us,
                    "cooling_option": "opticalpumping",
                    "samples_per_time":50,
                    "Ca_line":line,
                    "enable_854":False
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'BSB_SDF_mode2':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": 81.07*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": 81.13*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  40,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":27*dB,
                    "att_729_sp":30*dB,
                    "rabi_t": 1000*us,
                    "cooling_option":  "opticalpumping",
                    "samples_per_time":100,
                    "Ca_line":line,
                    "enable_854":False
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'BSB_SDF_mode1':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": 81.47*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": 81.50*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  40,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":27*dB,
                    "att_729_sp":30*dB,
                    "rabi_t": 1000*us,
                    "cooling_option":  "opticalpumping",
                    "samples_per_time":100,
                    "Ca_line":line,
                    "enable_854":False
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        return self.scheduler.submit(channel,  expid_3_1)
            
    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())


    def run(self):
        

        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=150, range=0.04, awg_power=0.15,  num_points=60)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        if self.ion_type == "single_ion":
            rid=self.submit_sidebands("BSB_SDF_single_ion")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)
        elif self.ion_type == "two_ion":
            rid=self.submit_sidebands("BSB_SDF_mode1")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_sidebands("BSB_SDF_mode2")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

