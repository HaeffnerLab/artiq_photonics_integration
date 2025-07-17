from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class Ramsey_Calibrate(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("enable_line_scan", BooleanValue(True))

        # self.setattr_argument("enable_BSB_mode1", BooleanValue(True))
        # self.setattr_argument("enable_BSB_mode2", BooleanValue(False))

        
        #vib_freq0_2=self.get_dataset("__param__sideband_Radial/vib_freq0_2")

        # self.setattr_argument(
        #     "vib_freq0_1",
        #     NumberValue(default=vib_freq0_1, min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
        #     tooltip="double pass frequency different in two position"
        # )
        # self.setattr_argument(
        #     "vib_freq0_2",
        #     NumberValue(default=vib_freq0_2, min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
        #     tooltip="double pass frequency different in two position"
        # )
        # self.setattr_argument("cooling_option", EnumerationValue(["opticalpumping", "sidebandcool_Radial"], default="opticalpumping"))
        


    def submit_sidebands(self, 
                    line="Radial_BSB_mode1", 
                    # rabi_t=1000,
                    range=0.02, 
                    # awg_power=0.03, 
                    num_points=50,
                    channel="calibration_main")->np.int32:
        

        vib_freq0_1=self.get_dataset("__param__sideband_Radial/vib_freq0_1")

        if line == 'Radial_BSB_mode1':
            freq_scan_center=self.get_dataset("__param__qubit/Sm1_2_Dm5_2")+vib_freq0_1/2.0
            expid_3_1 = {
                "file": "VdP_Two_Ion/Radial/A6_Radial_rabi_freq_scan.py",
                "class_name": "Rabi_Freq",
                "arguments": {
                    "scan_freq_729_dp": {
                                        "start": freq_scan_center-range*MHz, 
                                        "stop": freq_scan_center+range*MHz, 
                                        "npoints":  num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp": 10.0*dB,
                    "rabi_t": 30*us,
                    "cooling_option": "opticalpumping",
                    "calibration_option": "Radial/vib_freq0_1"
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        return self.scheduler.submit(channel,  expid_3_1)


    def submit_line(self, 
                    channel="calibration_main")->np.int32:

        expid_3_1 = {
            "file": "VdP_Two_Ion/Radial/A6_Radial_rabi_freq_scan.py",
            "class_name": "Rabi_Freq",
            "arguments": {
                "att_729_dp": 30.0*dB,
                "rabi_t":100*us
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        
        return self.scheduler.submit(channel,  expid_3_1)


    def submit_time_RSB_mode1(self, 
                    channel="calibration_main")->np.int32:

        vib_freq0_1=self.get_dataset("__param__sideband_Radial/vib_freq0_1")

        expid_3_1 = {
            "file": "VdP_Two_Ion/Radial/A6_Radial_rabi_time_scan.py",
            "class_name": "Rabi_Time",
            "arguments": {
                "scan_rabi_t": {
                    "start": 0*us, 
                    "stop": 1000*us, 
                    "npoints":  30,
                    "randomize": False,  
                    "ty": "RangeScan"
                },
                "freq_729_dp": self.get_dataset("__param__qubit/Sm1_2_Dm5_2")+vib_freq0_1/2.0,
                "att_729_dp": 10.0*dB,
                "cooling_option": "sidebandcool_Radial",

                "enable_pi_pulse": True
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        
        return self.scheduler.submit(channel,  expid_3_1)



    def submit_time_carrier(self, 
                    channel="calibration_main")->np.int32:

        expid_3_1 = {
            "file": "VdP_Two_Ion/Radial/A6_Radial_rabi_time_scan.py",
            "class_name": "Rabi_Time",
            "arguments": {
                "scan_rabi_t": {
                    "start": 0*us, 
                    "stop": 200*us, 
                    "npoints":  30,
                    "randomize": False,  
                    "ty": "RangeScan"
                },
                "freq_729_dp": self.get_dataset("__param__qubit/Sm1_2_Dm5_2"),
                "att_729_dp": 20.0*dB,
                "cooling_option": "sidebandcool_Radial"
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        
        return self.scheduler.submit(channel,  expid_3_1)


    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())
    # @kernel
    def run(self):
        

        if self.enable_line_scan:
            rid=self.submit_line('Sm1_2_Dm5_2')
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

        #pi time scan
        rid=self.submit_time_carrier()
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
        time.sleep(2)

        #scan freq on RSB
        rid=self.submit_sidebands()
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
        time.sleep(2)


        #pi time on RSB
        rid=self.submit_time_RSB_mode1()
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
        time.sleep(2)

