from artiq.experiment import *
from artiq.coredevice import ad9910
   
import numpy as np
from artiq.master.worker_db import DeviceManager

from artiq.master.databases import DeviceDB
from artiq.master.scheduler import Scheduler

import time

class track_sideband_one_ion(EnvExperiment):


    def build(self):
        self.setattr_device("core") 
        self.setattr_device("scheduler")
        self.set_default_scheduling(priority=-90)

        self.setattr_argument("ion_type", EnumerationValue([
            "two_ion", "single_ion"], default="single_ion"))


      
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
                "cooling_option": 'opticalpumping',
                    "enable_human_check":False,
                    "Ca_line":"Sm1_2_Dm5_2"
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }

        
        return self.scheduler.submit(channel,  expid_3_1)

    def submit_sidebands(self, 
                    freq_vib,
                    range,
                    line="BSB_SDF_single_ion", 
                    channel="calibration_main")->np.int32:
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")
        print(line)
        if line == 'BSB_SDF_single_ion':

            
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp-freq_vib-range, 
                                        "stop": freq_sp-freq_vib+range, 
                                        "npoints": 50,   
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":31*dB, 
                    "att_729_sp":31*dB,
                    "amp_729_dp":0.5,
                    "rabi_t": 2000*us,
                    "cooling_option": "opticalpumping",
                    "samples_per_time":50,
                    "Ca_line":line,
                    "enable_854":False,
                    "enable_human_check":False
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        elif line == 'RSB_SDF_single_ion':
            expid_3_1 = {
                "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp.py",
                "class_name": "A6_Rabi_Freq_AWG_Sp",
                "arguments": {
                    "scan_freq_729_sp": {
                                        "start": freq_sp+freq_vib-range, 
                                        "stop": freq_sp+freq_vib+range, 
                                        "npoints": 50,   
                                        "randomize": False,  
                                        "ty": "RangeScan"
                                        },
                    "att_729_dp":31*dB, 
                    "att_729_sp":31*dB,
                    "amp_729_dp":0.5,
                    "rabi_t": 2000*us,
                    "cooling_option": "opticalpumping",
                    "samples_per_time":50,
                    "Ca_line":line,
                    "enable_854":False,
                    "enable_human_check":False
                    },
                "log_level": 10,
                "repo_rev": "N/A"
                }
        return self.scheduler.submit(channel,  expid_3_1)

    
    def submit_sidebands_motion(self, 
                    range,
                    channel="calibration_main")->np.int32:
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")
      
        expid_3_1 = {
            "file": "VdP_Two_Ion/Rabi/A6_rabi_freq_scan_sp_Motion.py",
            "class_name": "A6_Rabi_Freq_AWG_Sp_Motion",
            "arguments": {
                "num_points":50,
                "freq_range":range,
                "att_729_dp":31*dB, 
                "att_729_sp":31*dB,
                "amp_729_dp":0.6,
                "rabi_t": 2000*us,
                "cooling_option": "opticalpumping",
                "vib_mode":"mode_single_ion",
                "samples_per_time":50
                },
            "log_level": 10,
            "repo_rev": "N/A"
            }
       
        return self.scheduler.submit(channel,  expid_3_1)


    def check_status(self, rid:np.int32)->bool:
        return (rid not in self.scheduler.get_status())


    def run(self):

        rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=75, range=0.008, awg_power=0.1,  num_points=30)
        time.sleep(1)
        while True:
            if self.check_status(rid):
                break
            time.sleep(2)
        '''
        RSB=[]
        RSB_var=[]
        BSB=[]
        BSB_var=[]
        time_BSB=[]
        time_RSB=[]
        
        if self.ion_type == "single_ion":

            for _ in range(20):

                print(_, " out of 100")
                
                if _ % 5==0:
                    rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02,  num_points=30)
                    time.sleep(1)
                    while True:
                        if self.check_status(rid):
                            break
                        time.sleep(2)
                
                
                scan_freq_vib=self.get_dataset("__param__VdP1mode/vib_freq", archive=False)
                scan_range=0.0015*MHz
                if _==0:
                    scan_range=0.003*MHz
                if _!=0:
                    scan_freq_vib=BSB[-1]
                rid=self.submit_sidebands(scan_freq_vib, scan_range,'BSB_SDF_single_ion')
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                time.sleep(2)
                BSB.append(self.get_dataset("__param__VdP1mode/vib_freq", archive=False))
                BSB_var.append(self.get_dataset("__param__VdP1mode/vib_freq_var", archive=False))
                time_BSB.append(time.time())
                if _!=0:
                    scan_freq_vib=RSB[-1]
                rid=self.submit_sidebands(scan_freq_vib, scan_range,'RSB_SDF_single_ion')
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                time.sleep(2)
                RSB.append(self.get_dataset("__param__VdP1mode/vib_freq", archive=False))
                RSB_var.append(self.get_dataset("__param__VdP1mode/vib_freq_var", archive=False))
                time_RSB.append(time.time())


            with open("RSB.txt", "w") as f:
                f.write("RSB_frequencies_MHz RSB_timestamps\n")
                for rsb, rsb_t, rsb_var in zip(RSB, time_RSB, RSB_var):
                    f.write(f"{rsb} {rsb_t} {rsb_var}\n")

            with open("BSB.txt", "w") as f:
                f.write("BSB_frequencies_MHz BSB_timestamps BSB_var\n")
                for bsb, bsb_t, bsb_var in zip(BSB, time_BSB, BSB_var):
                    f.write(f"{bsb} {bsb_t} {bsb_var}\n")
        '''
        vib_freq=[]
        time_vib=[]
        with open("vib_freq.txt", "w") as f:
            f.write("vib_freq_MHz timestamp\n")
            
        for i in range(100):

            if i % 3==0:
                rid=self.submit_line('Sm1_2_Dm5_2', rabi_t=1000, range=0.002, awg_power=0.02,  num_points=30)
                time.sleep(1)
                while True:
                    if self.check_status(rid):
                        break
                    time.sleep(2)
                    
            if i==0:
                rid=self.submit_sidebands_motion(0.004*MHz)
            else:
                rid=self.submit_sidebands_motion(0.0020*MHz)
            time.sleep(1)
            while True:
                if self.check_status(rid):
                    break
            time.sleep(2)

            vib_freq = self.get_dataset("__param__VdP1mode/vib_freq", archive=False)
            timestamp = time.time()
            
            with open("vib_freq.txt", "a") as f:
                f.write(f"{vib_freq} {timestamp}\n")

        # elif self.ion_type == "two_ion":
        #     rid=self.submit_sidebands("BSB_SDF_mode1")
        #     time.sleep(1)
        #     while True:
        #         if self.check_status(rid):
        #             break
        #         time.sleep(2)

        #     rid=self.submit_sidebands("BSB_SDF_mode2")
        #     time.sleep(1)
        #     while True:
        #         if self.check_status(rid):
        #             break
        #         time.sleep(2)

