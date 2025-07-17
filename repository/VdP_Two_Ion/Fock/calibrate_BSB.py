from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_qubit_Fock(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("ion_type", EnumerationValue([
            "two_ion", "single_ion"], default="single_ion"))

        self.setattr_argument("enable_human_check", BooleanValue(True))
      
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
                "cooling_option": "sidebandcool_single_ion",
                "enable_human_check":self.enable_human_check
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)

    def submit_pi_time(self, 
                    channel="calibration_main"):
        expid_4_3 = {
            "file": "VdP_Two_Ion/Rabi/A6_rabi_time_scan.py",
            "class_name": "A6_Rabi_Time_Cam",
            "arguments": { 
                "scan_rabi_t": {"start": 0.0*us, "stop": 200.*us, "npoints": 50, "randomize": False,  "ty": "RangeScan"},
                "att_729_dp":self.get_dataset("__param__Fock/att_729_dp"), 
                "att_729_sp":13.0*dB,
                "freq_729_sp":self.get_dataset("__param__frequency/729_sp")-self.get_dataset("__param__Fock/freq_BSB_sp"),
                "cooling_option": 'sidebandcool_single_ion',
                #"enable_human_check":self.enable_human_check
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        return self.scheduler.submit(channel,  expid_4_3)
    

    def submit_sidebands(self, 
                    line="Fock_BSB_single_ion", 
                    channel="calibration_main")->np.int32:
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")

        if line == "Fock_BSB_single_ion":

            freq_vib=self.get_dataset("__param__Fock/freq_BSB_sp")
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp-freq_vib-0.04*MHz, 
                                        "stop": freq_sp-freq_vib+0.04*MHz, 
                                        "npoints": 65,   
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__Fock/att_729_dp"), 
                    "att_729_sp":13*dB,
                    "rabi_t": 35*us,
                    "cooling_option": "sidebandcool_single_ion",
                    "samples_per_time":50,
                    "Ca_line":line,
                    "enable_854":False,
                    "enable_human_check":self.enable_human_check
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
                                        "start": 81.08*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": 81.10*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
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
                                        "start": 81.465*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": 81.485*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
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
        

        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=150, range=0.04, awg_power=0.1,  num_points=60)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)
        
        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1500, range=0.0015, awg_power=0.01)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        if self.ion_type == "single_ion":
            rid=self.submit_sidebands("Fock_BSB_single_ion")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_pi_time()
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

