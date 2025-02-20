
from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

#ddb = DeviceDB("device_db.py")
#devmgr = DeviceManager(ddb)

#create a scheduler 

class Calibrate_all(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        
        

    def run(self):
        expid_1 = {
            "file": "Calibration/freq_scan_397.py",
            "class_name": "FreqScan397",
            "arguments": None,
            "log_level": 10,
            "repo_rev": "N/A",
            }
        
        expid_2 = {
            "file": "Calibration/freq_scan_866.py",
            "class_name": "FreqScan866",
            "arguments": None,
            "log_level": 10,
            "repo_rev": "N/A",
            }

        self.scheduler.submit("main", expid_1)
        self.scheduler.submit("main", expid_2)
        # delay(10*s)
        #self._scheduler.submit("main", expid_2)
        