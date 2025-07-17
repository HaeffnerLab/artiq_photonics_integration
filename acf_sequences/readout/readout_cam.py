from acf.sequence import Sequence

from artiq.experiment import *

import numpy as np
class readout_cam_two_ion(Sequence):

    def __init__(self):
        super().__init__()

    def build(self):
        self.setattr_argument(
            "freq_397",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/397_resonance"), min=50*MHz, max=300*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "freq_397_cooling",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/397_cooling"), min=50*MHz, max=300*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "freq_866",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/866_cooling"), min=50*MHz, max=300*MHz, unit="MHz",precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "att_397",
            NumberValue(default=self.exp.parameter_manager.get_param("attenuation/397"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "att_866",
            NumberValue(default=self.exp.parameter_manager.get_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass frequency",
            group="camera readout"
        )
        self.setattr_argument(
            "exposure_time",
            NumberValue(default=self.exp.parameter_manager.get_param("readout/camera_sampling_time"), min=0*us, max=50*ms, unit="ms",precision=8),
            group="camera readout",
            tooltip="camera exposure time"
        )
        
        self.setattr_argument(
            "cam_ROI_size",
            NumberValue(default=self.exp.parameter_manager.get_param("readout/cam_ROI_size"), precision=0, step=1),
            tooltip="ROI size for camera",
            group="camera readout"
        )
        self.setattr_argument(
            "cam_threshold0",
            NumberValue(default=self.exp.parameter_manager.get_param("readout/cam_threshold0"), precision=0, step=1),
            tooltip="threshold for camera",
            group="camera readout"
        )
        self.setattr_argument(
            "cam_threshold1",
            NumberValue(default=self.exp.parameter_manager.get_param("readout/cam_threshold1"), precision=0, step=1),
            tooltip="threshold for camera",
            group="camera readout"
        )
        
        self.setattr_argument("enable_binning", BooleanValue(True),
                              tooltip="threshold for camera",
                                group="camera readout")
        
    @kernel
    def cam_setup(self):
        #setup camera readout parameters

        cam_input=[0,0]
        offset=self.cam_ROI_size

        if self.enable_binning:
            #for binning to 12*1
            # self.cam.setup_roi(0, offset , 1, offset*2,   2)
            # self.cam.setup_roi(1, 0     , 1, offset,   2)
            #for binning from 12*12 to 12*2
            self.cam.setup_roi(0, offset, 1, offset*2, 2)
            self.cam.setup_roi(1, 0     , 2, offset, 3)

        else:
            #for normal 12*12 ROI
            self.cam.setup_roi(0, offset, 1, offset*2, 1+offset)
            self.cam.setup_roi(1, 0     , 1+offset, offset, 2+offset*2)

            #for normal 12*12 ROI crop x
            # self.cam.setup_roi(0, offset, 0, offset*2, offset)
            # self.cam.setup_roi(1, 0     , offset, offset, offset*2)

        self.cam.gate_roi(3)
        delay(2*ms)
        self.ttl_camera_trigger.pulse(10*us)
        self.cam.input_mu(cam_input)
        self.exp.core.break_realtime()



    @kernel
    def cam_readout_raw(self, cam_output, off_866=False, 
                        freq_397_here=-999.0*MHz, 
                        freq_866_here=-999.0*MHz,
                        att_397_here=-1.0*dB,
                        att_866_here=-1.0*dB):

        if freq_397_here<0:
            freq_397_here=self.freq_397
        
        if freq_866_here<0:
            freq_866_here=self.freq_866
        
        if att_397_here<0:
            att_397_here=self.att_397
        
        if att_866_here<0:
            att_866_here=self.att_866

        self.dds_729_dp.sw.off()

        # Readout
        self.dds_397_dp.set_att(att_397_here)
        self.dds_397_dp.set(freq_397_here)
        self.dds_866_dp.set(freq_866_here)
        self.dds_866_dp.set_att(att_866_here)
        
        self.dds_397_dp.sw.on()
        if off_866:
            self.dds_866_dp.sw.off()
        else:
            self.dds_866_dp.sw.on()
        delay(5*us) 

        cam_input=[0,0]

        #t1=self.exp.core.get_rtio_counter_mu()

        '''old version
        self.ttl_camera_trigger.pulse(10*us)
        self.cam.input_mu(cam_input)
        self.exp.core.break_realtime()
        '''

        self.ttl_camera_trigger.pulse(10*us)
        delay(self.exposure_time)
        self.dds_397_dp.set(self.freq_397_cooling)
        #self.dds_397_far_detuned.cfg_sw(True)
        self.cam.input_mu(cam_input)
        self.exp.core.break_realtime()

        #t2=self.exp.core.get_rtio_counter_mu()

        #print(self.exp.core.mu_to_seconds(t2-t1))
        #self.exp.core.break_realtime()
        self.dds_397_far_detuned.cfg_sw(False)
        self.dds_397_dp.sw.off()
        self.dds_866_dp.sw.off()

        if self.enable_binning:
            cam_output[0]=1.0*(cam_input[0]*1.0/self.cam_ROI_size/4.0)#/self.cam_ROI_size)#/2)#/2)#/2)
            cam_output[1]=1.0*(cam_input[1]*1.0/self.cam_ROI_size/4.0)#/2/self.cam_ROI_size/2)#/2)#/2)
        else:
            cam_output[0]=1.0*(cam_input[0]*1.0/self.cam_ROI_size/self.cam_ROI_size)
            cam_output[1]=1.0*(cam_input[1]*1.0/self.cam_ROI_size/self.cam_ROI_size)
        
        

    @kernel
    def cam_readout(self, off_866=False, output_debug=False):
        # Readout
        cam_output=[0.0,0.0]

        self.cam_readout_raw(cam_output, off_866)

        ion_status=0
        ion_status = ion_status | 2 if cam_output[1]>self.cam_threshold1 else ion_status
        ion_status = ion_status | 1 if cam_output[0]>self.cam_threshold0 else ion_status

        if output_debug:
            print("cam_output", cam_output[0], cam_output[1])
            self.core.break_realtime()
        
        return ion_status

