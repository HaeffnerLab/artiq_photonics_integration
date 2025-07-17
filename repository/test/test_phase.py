from artiq.experiment import *                                             
from artiq.coredevice.ad9910 import (RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_RAMPUP)

class simple_two_dds(EnvExperiment):
    def build(self): 
        self.setattr_device("core")                               
        self.dds1 = self.get_device("urukul0_ch1")
        self.dds2 = self.get_device("urukul0_ch2")

    @kernel
    def run(self):
        self.core.break_realtime()
        self.core.reset()
        self.dds1.set(80.5*MHz)
        self.dds2.set(79.5*MHz)
        self.dds1.set_att(15*dB)
        self.dds2.set_att(15*dB)

        self.dds1.sw.on()
        self.dds2.sw.on()       

        while True:
            pass             