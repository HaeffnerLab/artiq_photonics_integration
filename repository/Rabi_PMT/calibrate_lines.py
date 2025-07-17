from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_lines(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

      
    def submit_line(self, 
                    line="Sm1_2_Dm5_2", 
                    rabi_t=1000,
                    range=0.002, 
                    att_sp=29*dB,
                    att_dp=30*dB,
                    num_points=30,
                    channel="calibration_main")->np.int32:
        
        expid_3_1 = {
            "file": "Rabi/rabi_freq_scan.py",
            "class_name": "RabiFreqScan",
            "arguments": {
                "scan_freq_729_dp": {
                                     "start": self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                     "stop": self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                     "npoints":  num_points,
                                     "randomize": False,  
                                     "ty": "RangeScan"
                                    },
                "att_729_sp":att_sp,
                "rabi_t": rabi_t*us,
                "att_729_dp": att_dp
                #"cooling_option": 'opticalpumping'
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)

    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())
    # @kernel
    def run(self):
        
        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=100, range=0.06, att_sp=27, att_dp=30, num_points=60)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.003, att_sp=30 , att_dp=31)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_line('Sm1_2_Dm1_2', rabi_t=60, range=0.06, att_dp=30, att_sp=29,  num_points=60)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_line('Sm1_2_Dm1_2', rabi_t=600, range=0.003, att_dp=30, att_sp=31)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)


