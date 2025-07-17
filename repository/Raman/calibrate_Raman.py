from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_Raman_lines(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

      
    def submit_line(self, 
                    center_freq,
                    rabi_t=200,
                    range=0.002, 
                    att_Raman1=20.0*dB,
                    att_Raman2=20.0*dB,
                    amp_Raman1=1.0,
                    amp_Raman2=1.0,
                    num_points=30,
                    channel="calibration_main")->np.int32:
        
        expid_3_1 = {
            "file": "Raman/raman_freq_scan_cam.py",
            "class_name": "RamanFreqScan_Cam",
            "arguments": {
                "scan_freq_Raman1": {
                                     "start": center_freq-range*MHz, 
                                     "stop": center_freq+range*MHz, 
                                     "npoints":  num_points,
                                     "randomize": False,  
                                     "ty": "RangeScan"
                                    },
                "att_Raman1":att_Raman1,
                "att_Raman2": att_Raman2,
                "amp_Raman1": amp_Raman1,
                "amp_Raman2": amp_Raman2,
                "rabi_t": rabi_t*us
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        return self.scheduler.submit(channel,  expid_3_1)

    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())
    # @kernel
    def run(self):
        
        rid=self.submit_line(center_freq = self.get_dataset("__param__frequency/Raman1"),
                             rabi_t=20, 
                             range=0.1, 
                             amp_Raman1=1,
                             amp_Raman2=1,
                             num_points=30)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        rid=self.submit_line(center_freq = self.get_dataset("__param__frequency/Raman1") -self.get_dataset("__param__sideband_Raman/vib_freq1"), 
                             rabi_t=15, 
                             range=0.2, 
                             amp_Raman1=1,
                             amp_Raman2=1,
                             num_points=60)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)


