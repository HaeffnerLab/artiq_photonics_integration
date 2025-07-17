from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class scan_sidebands_Two_Ion_VdP(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("enable_coarse_line_scan", BooleanValue(False))
        self.setattr_argument("enable_854", BooleanValue(False))

        self.setattr_argument("enable_RSB", BooleanValue(False))
        self.setattr_argument("enable_BSB", BooleanValue(True))
        self.setattr_argument("enable_2RSB", BooleanValue(True)) 
        self.setattr_argument("enable_human_check", BooleanValue(False))

        self.setattr_argument("enable_measurement", BooleanValue(False))
        self.setattr_argument("Px1x2", BooleanValue(True))
        self.setattr_argument(
            "freq_detune",
            NumberValue(default=0, min=-10000, max=10000, unit="Hz", precision=8),
            tooltip="double pass frequency different in two position"
        )        
        self.setattr_argument(
            "VdP2Mode_Vdp_sync_phase_degree",
            NumberValue(default=0, min=-10000, max=10000,  precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

    def submit_sidebands(self, 
                    line="2RSB_mode1", #2RSB_mode2
                    # rabi_t=1000,
                    # range=0.002, 
                    # awg_power=0.03, 
                    # num_points=30,
                    channel="calibration_main")->np.int32:
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")

        if line == '2RSB_mode1':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp+0.98*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp+1.10*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  35,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__VdP2mode/att_729_dp"),
                    "att_729_sp":self.get_dataset("__param__VdP2mode/att_729_mode1_2RSB"),
                    "rabi_t": 35*us,
                    "cooling_option": "sidebandcool_mode2",
                    "samples_per_time":50,
                    "Ca_line":line,                    
                    
                    "enable_854":self.enable_854,
                    "att_854":self.get_dataset("__param__VdP2mode/att_854"),
                    "att_866":self.get_dataset("__param__VdP2mode/att_866"),
                    "enable_human_check": self.enable_human_check
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == '2RSB_mode2':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp+1.7*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp+1.9*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  40,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__VdP2mode/att_729_dp"),
                    "att_729_sp":self.get_dataset("__param__VdP2mode/att_729_mode2_2RSB"),
                    "rabi_t": 50*us,
                    "cooling_option":  "sidebandcool_mode1",
                    "samples_per_time":50,
                    "Ca_line":line,                    
                    
                    "enable_854":self.enable_854,
                    "att_854":self.get_dataset("__param__VdP2mode/att_854"),
                    "att_866":self.get_dataset("__param__VdP2mode/att_866"),
                    "enable_human_check": self.enable_human_check
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'BSB_mode2':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp-1.0*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp-0.85*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  40,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__VdP2mode/att_729_dp"),
                    "att_729_sp":self.get_dataset("__param__VdP2mode/att_729_mode2_BSB"),
                    "rabi_t": 35*us,
                    "cooling_option":  "sidebandcool2mode",
                    "samples_per_time":50,
                    "Ca_line":line,                    
                    
                    "enable_854":self.enable_854,
                    "att_854":self.get_dataset("__param__VdP2mode/att_854"),
                    "att_866":self.get_dataset("__param__VdP2mode/att_866"),
                    "enable_human_check": self.enable_human_check
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'BSB_mode1':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp-0.57*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp-0.47*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  40,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":self.get_dataset("__param__VdP2mode/att_729_dp"),
                    "att_729_sp":self.get_dataset("__param__VdP2mode/att_729_mode1_BSB"),
                    "rabi_t": 45*us,
                    "cooling_option":  "sidebandcool2mode",
                    "samples_per_time":50,
                    "Ca_line":line,                    
                    
                    "enable_854":self.enable_854,
                    "att_854":self.get_dataset("__param__VdP2mode/att_854"),
                    "att_866":self.get_dataset("__param__VdP2mode/att_866"),
                    "enable_human_check": self.enable_human_check
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'RSB_mode1':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp_RSB.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp_RSB",
                "arguments": {
                    "att_729_dp":self.get_dataset("__param__VdP2mode/att_729_dp"),

                    "scan_freq_729_sp": {
                                        "start": freq_sp+0.49*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop": freq_sp+0.55*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  25,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "amp_729_sp":self.get_dataset("__param__VdP2mode/amp_729_mode1_RSB"),
                    
                    "amp_729_sp_fixed":self.get_dataset("__param__VdP2mode/amp_729_mode2_RSB"),
                    "freq_729_sp_fixed": self.get_dataset("__param__frequency/729_sp")+self.get_dataset("__param__VdP2mode/freq_RSB_mode2")-0.1*MHz, #detuned 

                    "rabi_t": 100*us,
                    "cooling_option": "sidebandcool_mode2",
                    "samples_per_time":50,
                    "Ca_line":line,                    
                    
                    # "enable_854":self.enable_854,
                    # "att_854":self.get_dataset("__param__VdP2mode/att_854"),
                    # "att_866":self.get_dataset("__param__VdP2mode/att_866")
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'RSB_mode2':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp_RSB.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp_RSB",
                "arguments": {
                    "att_729_dp":self.get_dataset("__param__VdP2mode/att_729_dp"),

                    "scan_freq_729_sp": {
                                        "start": freq_sp+0.88*MHz, #self.get_dataset("__param__qubit/"+line)-range*MHz, 
                                        "stop":freq_sp+0.93*MHz, #self.get_dataset("__param__qubit/"+line)+range*MHz, 
                                        "npoints":  20,   #num_points,
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "amp_729_sp":self.get_dataset("__param__VdP2mode/amp_729_mode2_RSB"),
                    
                    "amp_729_sp_fixed":self.get_dataset("__param__VdP2mode/amp_729_mode1_RSB"),
                    "freq_729_sp_fixed": self.get_dataset("__param__frequency/729_sp")+self.get_dataset("__param__VdP2mode/freq_RSB_mode1")+0.1*MHz, #detuned 

                    "rabi_t": 150*us,
                    "cooling_option": "sidebandcool_mode1",
                    "samples_per_time":50,
                    "Ca_line":line,                    
                    
                    # "enable_854":self.enable_854,
                    # "att_854":self.get_dataset("__param__VdP2mode/att_854"),
                    # "att_866":self.get_dataset("__param__VdP2mode/att_866")
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

        cooling_option="sidebandcool2mode" 
        
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
                "cooling_option": cooling_option,
                "enable_human_check": self.enable_human_check
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)

    def submit_Px1x2(self):
        expid_3_1 = {
            "file": "VdP_Two_Ion/A7_final_Vdp2_Px1x2.py",
            "class_name": "A7_Sync_VdP2_Px1x2",
            "arguments": {
                "freq_detune":self.freq_detune,
                "Px1p2":self.Px1x2,
                "samples_per_time":self.samples_per_time,
                "VdP2Mode_Vdp_sync_phase_degree":self.VdP2Mode_Vdp_sync_phase_degree
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
        return self.scheduler.submit("calibration_main",  expid_3_1)

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

        if self.enable_2RSB:
            rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.01)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_sidebands("2RSB_mode1")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.01)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_sidebands("2RSB_mode2")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)
############################################################################################################

        if self.enable_BSB:
            rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.01)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_sidebands("BSB_mode1")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)

            rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.01)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)
                
            rid=self.submit_sidebands("BSB_mode2")
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)
############################################################################################################
        if self.enable_measurement:
            rid=self.submit_Px1x2()
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
                time.sleep(2)
        # if self.enable_RSB:
        #     rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.01)

        #     time.sleep(1)
        #     while True:
        #         if self.check_status(rid):
        #             break
        #         time.sleep(2)


        #     rid=self.submit_sidebands("RSB_mode1")
        #     time.sleep(1)
        #     while True:
        #         if self.check_status(rid):
        #             break
        #         time.sleep(2)

        #     rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.01)
        #     time.sleep(1)
        #     while True:
        #         if self.check_status(rid):
        #             break
        #         time.sleep(2)
                
        #     rid=self.submit_sidebands("RSB_mode2")
        #     time.sleep(1)
        #     while True:
        #         if self.check_status(rid):
        #             break
        #         time.sleep(2)

############################################################################################################