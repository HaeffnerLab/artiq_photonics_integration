from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class Calibration_SDF_Rabi_One_Ion(EnvExperiment):


    def build(self):
        #self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("calibration_platform", 
                              EnumerationValue(["single_ion", 
                                                "Ca44_Ca40"
                                                ], default="single_ion"))
        self.setattr_argument(
            "frequency_calibration",
            NumberValue(default=1, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

    def prepare(self):

        expid_0 = {
            "file": "default_experiment.py",
            "class_name": "DefaultExperiment",
            "arguments": {
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        ########################################################################################
        cooling_option="sidebandcool2mode" if self.calibration_platform=="Ca40_Ca44" else "sidebandcool_single_ion"
        ########################################################################################
        expid_5_1 = {
            "file": "VdP_Two_Ion/SDF_Calibration/A6_att_scan_SDF.py",
            "class_name": "A6_att_scan_SDF_AWG_Cam",
            "arguments": { 
                "vib_mode":  "mode_single_ion",
                "cooling_option": cooling_option,
                "scan_amp_729_sp_aux":{"start": self.get_dataset("__param__SDF/mode_single_ion/amp_729_sp_aux")-0.02, "stop": self.get_dataset("__param__SDF/mode_single_ion/amp_729_sp_aux")+0.02, "npoints": 10, "randomize": True,  "ty": "RangeScan"},
                "rabi_t": 12.0*us
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }


        ########################################################################################
        expid_6_1 = {
            "file": "VdP_Two_Ion/A6_Displacement_Time.py",
            "class_name": "A6_Displacement_Time",
            "arguments": { 
                "scan_rabi_t": {"start": 0.0*us, "stop": 50.*us, "npoints": 30, "randomize": False,  "ty": "RangeScan"},
                "freq_729_dp":self.get_dataset("__param__qubit/Sm1_2_Dm5_2")+self.get_dataset("__param__qubit/vib_freq"),
                "vib_mode":  "mode_single_ion",
                "freq_delta_m": 0.0,
                "power_calibration":"SDF/mode_single_ion/Rabi_Freq",
                "cooling_option": cooling_option
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        expid_6_2 = {
            "file": "VdP_Two_Ion/A6_Displacement_Time.py",
            "class_name": "A6_Displacement_Time",
            "arguments": { 
                "scan_rabi_t": {"start": 0.0*us, "stop": 50.*us, "npoints": 30, "randomize": False,  "ty": "RangeScan"},
                "freq_729_dp":self.get_dataset("__param__qubit/Sm1_2_Dm5_2")-self.get_dataset("__param__qubit/vib_freq"),
                "vib_mode": "mode_single_ion",
                "freq_delta_m": 0.0,
                "power_calibration":"SDF/mode_single_ion/Rabi_Freq",
                "cooling_option": cooling_option
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        
        ########################################################################################

        expid_7_1 = {
            "file": "VdP_Two_Ion/SDF_Calibration/A6_att_scan_SDF.py",
            "class_name": "A6_att_scan_SDF_AWG_Cam",
            "arguments": { 
                "rabi_t":2.75*(1.0/self.get_dataset("__param__SDF/mode_single_ion/Rabi_Freq")),
                "vib_mode":  "mode_single_ion",
                "cooling_option": cooling_option,
                "scan_amp_729_sp_aux":{"start": self.get_dataset("__param__SDF/mode_single_ion/amp_729_sp_aux")-0.005, "stop": self.get_dataset("__param__SDF/mode_single_ion/amp_729_sp_aux")+0.005, "npoints": 10, "randomize": True,  "ty": "RangeScan"},
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }


        
        #SDF power balancer ####################################################################

        ########################################################################################
        self.expid_list=[#expid_0,
                        #  expid_1, 

                        #  expid_2, 
                        #  expid_3, 
                        #  expid_4_1, #4
                        #  expid_4_2, #5
                        #  expid_4_3, #6
                        #  expid_4_4, #7

                          expid_5_1, #8
                        #   expid_6_1, #8
                        #   #expid_6_2,  #9
                        #   expid_7_1,
                          expid_6_1, #8
                          expid_6_2,
                        #   expid_6_4  #9

                         # expid_7_1
                         ]
        
    def submit_line(self, 
                    line="Sm1_2_Dm5_2", 
                    rabi_t=1000,
                    range=0.002, 
                    awg_power=0.03, 
                    num_points=30,
                    channel="calibration_main")->np.int32:

        cooling_option="sidebandcool2mode" if self.calibration_platform=="Ca40_Ca44" else "sidebandcool_single_ion"
        
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
                "cooling_option": cooling_option
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)
    def submit(self, index:np.int32, channel="calibration_main")->np.int32:
        return self.scheduler.submit(channel, self.expid_list[index])

    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())

    @kernel
    def flip_mirror(self):
        self.core.break_realtime()
        self.ttl6.pulse(1*ms)
        self.core.break_realtime()

   # @kernel
    def run(self):

        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=100, range=0.06, awg_power=0.1,  num_points=60)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)
    
        for i in range(0, len(self.expid_list)):

            if i%self.frequency_calibration==0: #recalibrate lines
                rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1500, range=0.0015, awg_power=0.01)
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                    time.sleep(2)

            rid=self.submit(i)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

                

        # rid=self.submit(0, channel="main")
        # time.sleep(1)








####################################################################
        # queue=[expid_1, expid_2, expid_3]

        # rid=self.scheduler.submit("calibration_main", expid_1)
        # time.sleep(1)
        # i=1
        # while i<len(queue):
        #     if (rid not in self.scheduler.get_status()):
        #         rid=self.scheduler.submit("calibration_main", queue[i])
        #         time.sleep(1)
        #         i=i+1

        # while rid in self.scheduler.get_status():
        #     pass