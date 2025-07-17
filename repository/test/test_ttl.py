from artiq.experiment import *                                             
from artiq.coredevice.ad9910 import (RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_RAMPUP)

class simple_ttl(EnvExperiment):
    def build(self): 
        self.setattr_device("core")                               
        self.setattr_device("ttl0")     

    @kernel
    def run(self):
        self.core.break_realtime()
        self.core.reset()
        self.ttl0.input()                          