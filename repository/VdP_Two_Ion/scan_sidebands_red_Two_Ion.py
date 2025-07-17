from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_sidebands_red_Two_Ion(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)
      

    def submit_sidebands(self, 
                    line='RSB_mode2',
                    channel="calibration_main")->np.int32:
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")

        if line == 'RSB_mode2':
            expid_3_1 = {
                "file": "VdP_Two_Ion/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": 82.9*MHz, 
                                        "stop": 82.925*MHz, 
                                        "npoints":  40, 
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "enable_pi_pulse":True,
                    "att_729_dp":27*dB,
                    "att_729_sp":30*dB,
                    "rabi_t": 1000*us,
                    "cooling_option":  "sidebandcool2mode",
                    "samples_per_time":100,
                    "Ca_line":line
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'RSB_mode1':
            expid_3_1 = {
                "file": "VdP_Two_Ion/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": 82.515*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": 82.535*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  40,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "enable_pi_pulse":True,
                    "att_729_dp":27*dB,
                    "att_729_sp":30*dB,
                    "rabi_t": 1000*us,
                    "cooling_option":   "sidebandcool2mode",
                    "samples_per_time":100,
                    "Ca_line":line
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
                "cooling_option":  "sidebandcool2mode"
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

        # rid=self.submit_sidebands("RSB_mode1")
        # time.sleep(1)
        # while True:
        #     if self.check_status(rid):
        #         break
        #     time.sleep(2)

        # rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02)
        # time.sleep(1)
        # while True:
        #     if self.check_status(rid):
        #         break
        #     time.sleep(2)
            
        rid=self.submit_sidebands("RSB_mode2")
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)