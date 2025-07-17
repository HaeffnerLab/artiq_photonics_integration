from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_qubit_carrier(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("coarse", BooleanValue(True))
        self.setattr_argument("fine", BooleanValue(True))

        self.setattr_argument("Sm12Dm52", BooleanValue(True))
        self.setattr_argument("Sm12Dm12", BooleanValue(True))

        self.setattr_argument("use_AWG", BooleanValue(True))


      
    def submit_line(self, 
                    line="Sm1_2_Dm5_2", 
                    rabi_t=1000,
                    range=0.002, 
                    awg_power=0.03, 
                    num_points=30,
                    channel="calibration_main")->np.int32:
        if self.use_AWG:
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
        else:
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan.py",
                "class_name": "A6_Rabi_Freq_Cam",
                "arguments": {
                    "scan_freq_729_dp": {
                                        "start": self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_sp":20*dB,
                    "rabi_t": rabi_t*us,
                    "cooling_option": 'opticalpumping'
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        
        return self.scheduler.submit(channel,  expid_3_1)

    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())
    # @kernel
    def run(self):
        
        if self.coarse:

            if self.Sm12Dm52:
                rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=150, range=0.04, awg_power=0.15,  num_points=60)
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                    time.sleep(2)

            if self.Sm12Dm12:      
                rid=self.submit_line('Sm1_2_Dm1_2', rabi_t=60, range=0.06, awg_power=0.15,  num_points=60)
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                    time.sleep(2)

        if self.fine:
            if self.Sm12Dm52:
                rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02)
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                    time.sleep(2)


            if self.Sm12Dm12:    
                rid=self.submit_line('Sm1_2_Dm1_2', rabi_t=800, range=0.001, awg_power=0.01)
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                    time.sleep(2)


