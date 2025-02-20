from artiq.experiment import *
from acf.experiment import _ACFExperiment
from acf_config.arguments_definition import argument_manager

from acf_sequences.sequences import sequences

import numpy as np

from utils_func.otsu import otsu_threshold_manual, kapur_entropy_thresholding
from acf.utils import get_config_dir

class Plot_Cam(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
    	
        self.setattr_argument(
            "freq_397",
            NumberValue(default=self.parameter_manager.get_param("frequency/397_resonance"), min=50*MHz, max=300*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "freq_866",
            NumberValue(default=self.parameter_manager.get_param("frequency/866_cooling"), min=50*MHz, max=300*MHz, unit="MHz",precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "att_397",
            NumberValue(default=self.parameter_manager.get_param("attenuation/397"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "att_866",
            NumberValue(default=self.parameter_manager.get_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )

        self.setattr_argument(
            "samples",
            NumberValue(default=30, precision=0, step=1),
        )

    def prepare(self):

        self.image_x= 50 #326 for x at 203
        self.image_y= 4
        self.experiment_data.set_list_dataset("pmt_counts", self.image_x*self.image_y, broadcast=True)

    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(5*us)

        for i_x in range(self.image_x):
            for i_y in range(self.image_y):
                
                #camera
                cam_input=[0]
                self.cam.setup_roi(0, i_x, i_y, i_x+1, i_y+1)
                self.cam.gate_roi(1)
                self.core.break_realtime()
                self.ttl_camera_trigger.pulse(10*us)
                self.cam.input_mu(cam_input)
                self.core.break_realtime()
                # print(cam_input)
                # self.core.break_realtime()

                pix_avg=0

                sample_num=0
                while sample_num< self.samples:
                    
                    sample_num+=1
                
                    # Doppler cooling    
                    self.seq.doppler_cool.run()
                    
                    # setup laser
                    self.dds_397_dp.set_att(self.att_397)
                    self.dds_397_dp.set(self.freq_397)
                    self.dds_866_dp.set(self.freq_866)
                    self.dds_866_dp.set_att(self.att_866)
                    self.dds_397_dp.sw.on()
                    self.dds_866_dp.sw.on()
                    delay(5*us) 


                    self.ttl_camera_trigger.pulse(10*us)
                    self.cam.input_mu(cam_input)
                    self.core.break_realtime()
                    
                    pix_avg+=cam_input[0]
                    self.core.break_realtime()
                    
                # self.experiment_data.insert_nd_dataset("pmt_counts",
                #                                     [i_x, i_y],
                #                                     pix_avg/self.samples)
                self.experiment_data.append_list_dataset("pmt_counts",  pix_avg)
                self.core.break_realtime()
        
        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

    def analyze(self):
        dt=np.array(self.get_dataset("pmt_counts"))
        np.savetxt(get_config_dir()/'../repository/image.txt', dt)
