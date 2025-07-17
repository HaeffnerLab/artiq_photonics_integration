from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_BSB_Freq_One_Ion_Radial(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("enable_coarse_line_scan", BooleanValue(True))
        self.setattr_argument("enable_fine_line_scan", BooleanValue(False))
        #self.setattr_argument("enable_scan_Radial_BSB", BooleanValue(False))
        #self.setattr_argument("enable_scan_Radial_RSB", BooleanValue(True))

        vib_freq0_1=self.get_dataset("__param__sideband_Radial/vib_freq0_1")
        vib_freq0_2=self.get_dataset("__param__sideband_Radial/vib_freq0_2")

        self.setattr_argument(
            "vib_freq0_1",
            NumberValue(default=vib_freq0_1, min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument(
            "vib_freq0_2",
            NumberValue(default=vib_freq0_2, min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("cooling_option", EnumerationValue(["opticalpumping", "sidebandcool_Radial"], default="opticalpumping"))
        


    def submit_sidebands(self, 
                    line="Radial_BSB_mode1", 
                    # rabi_t=1000,
                    range=0.02, 
                    # awg_power=0.03, 
                    num_points=50,
                    channel="calibration_main")->np.int32:
        
        cooling_option=self.cooling_option

        if line == 'Radial_BSB_mode1':
            freq_scan_center=self.get_dataset("__param__qubit/Sm1_2_Dm5_2")-self.vib_freq0_1/2.0
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
                    "att_729_dp": 20.0*dB,
                    "rabi_t": 120*us,
                    "cooling_option": cooling_option,
                    "calibration_option": "Radial/vib_freq0_1"
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        else:
            freq_scan_center=self.get_dataset("__param__qubit/Sm1_2_Dm5_2")-self.vib_freq0_2/2.0
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
                    "att_729_dp":  20.0*dB,
                    "rabi_t": 120*us,
                    "cooling_option": cooling_option,
                    "calibration_option": "Radial/vib_freq0_2"
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

        cooling_option=self.cooling_option
        
        # expid_3_1 = {
        #     "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_AWG.py",
        #     "class_name": "A6_Rabi_Freq_AWG_Cam",
        #     "arguments": {
        #         "scan_freq_729_dp": {
        #                              "start": self.get_dataset("__param__qubit/"+line)-range*MHz, 
        #                              "stop": self.get_dataset("__param__qubit/"+line)+range*MHz, 
        #                              "npoints":  num_points,
        #                              "randomize": False,  
        #                              "ty": "RangeScan"
        #                             },
        #         "amp_729_sp":awg_power,
        #         "rabi_t": rabi_t*us,
        #         "cooling_option": cooling_option
        #         },
        #     "log_level": 10,
        #     "repo_rev": "N/A"
        #     }
        expid_3_1 = {
            "file": "VdP_Two_Ion/Radial/A6_Radial_rabi_freq_scan.py",
            "class_name": "Rabi_Freq",
            "arguments": {
                # "scan_freq_729_dp": {
                #                      "start": self.get_dataset("__param__qubit/"+line)-range*MHz, 
                #                      "stop": self.get_dataset("__param__qubit/"+line)+range*MHz, 
                #                      "npoints":  num_points,
                #                      "randomize": False,  
                #                      "ty": "RangeScan"
                #                     },
                # "amp_729_sp":awg_power,
                # "rabi_t": rabi_t*us,
                # "cooling_option": cooling_option
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

        if self.enable_fine_line_scan:
            rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

        #if self.enable_scan_Radial_BSB:
        rid=self.submit_sidebands("Radial_BSB_mode1")
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

        #if self.enable_scan_Radial_RSB:
        rid=self.submit_sidebands("Radial_RSB_mode2")
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)

