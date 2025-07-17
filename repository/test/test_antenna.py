from artiq.experiment import *                                              #Imports everything from experiment library
from artiq.coredevice.ad9910 import (                                       #Imports RAM destination amplitude scale factor and RAM mode bidirectional ramp methods from AD9910 Source
    RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP)

#This code demonstrates use of the urukul RAM. It produces a 125MHz pulse that ramps up in amplitude, holds a fixed amplitude and then ramps back down
    
class TestAntenna(EnvExperiment):
    '''Urukul RAM Amplitude Ramp'''
    def build(self): #this code runs on the host computer
        self.setattr_device("core")                                          #sets ttl channel 6 device drivers as attributes
        self.dds = self.get_device("urukul2_ch3")                             #sets urukul 0, channel 1 device drivers as attributes and renames object self.dds 

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.dds.init()
        delay(10*ms)
        self.dds.set_att(17*dB) 
        # 16.5dB ~ 1W
        # 10dB ~ almost 5W

        self.dds.set(8.95*MHz)
        delay(10*ms)
        self.dds.sw.on()