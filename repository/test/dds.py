from artiq.experiment import * 

 
class DDS_ON(EnvExperiment):
    
    def build(self): #this code runs on the host computer
        self.setattr_device("core")                                          #sets ttl channel 6 device drivers as attributes
        self.dds = self.get_device("urukul2_ch3")                             


    @kernel
    def run(self):
        
        self.core.break_realtime()
        self.dds.init()
        delay(10*ms)
        self.dds.set(235*MHz)
        self.dds.set_att(25*dB)

        delay(10*ms)
        self.dds.sw.on()
