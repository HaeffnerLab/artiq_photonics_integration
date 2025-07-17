from artiq.experiment import *

class ReSetDDSSLOW(EnvExperiment):
    def build(self):
        self.setattr_device("core")                                          #sets ttl channel 6 device drivers as attributes

        self.setattr_device("urukul0_ch0")         
        self.setattr_device("urukul0_ch1")         
        self.setattr_device("urukul0_ch2")         
        self.setattr_device("urukul0_ch3")         
        self.setattr_device("urukul1_ch0")         
        self.setattr_device("urukul1_ch1")         
        self.setattr_device("urukul1_ch2")         
        self.setattr_device("urukul1_ch3")          
        self.setattr_device("urukul2_ch0")         
        self.setattr_device("urukul2_ch1")           
        self.setattr_device("urukul2_ch2")         
        self.setattr_device("urukul2_ch3")         
        self.setattr_device("urukul3_ch0")         
        self.setattr_device("urukul3_ch1")         
        self.setattr_device("urukul3_ch2")         
        self.setattr_device("urukul3_ch3")      
        # self.dv=[
        #     self.urukul0_ch0,
        #     self.urukul0_ch1,                 
        #     self.urukul0_ch2,
        #     self.urukul0_ch3,                

        #     self.urukul1_ch0,
        #     self.urukul1_ch1,                 
        #     self.urukul1_ch2,
        #     self.urukul1_ch3,   

        #     self.urukul2_ch0,
        #     self.urukul2_ch1,                 
        #     self.urukul2_ch2,
        #     self.urukul2_ch3
        #         ]
        self.slow_dv=[
            self.urukul3_ch0,
            self.urukul3_ch1,                 
            self.urukul3_ch2,
            self.urukul3_ch3  
        ]

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()

        # for i in self.dv:
        #     i.init()
        #     i.cpld.init()
        #     i.sw.off()
        #     i.set_att(30*dB)

        for i in self.slow_dv:
            i.cpld.init()
            i.init()
            
            i.set_att(30*dB)
        #     delay(1*us)
            i.cfg_sw(False)
        
        # self.urukul3_ch0.set_att(30.0*dB)
        # self.urukul3_ch0.set(100.0*MHz)
        # self.urukul3_ch0.cfg_sw(False)
        
        delay(20*ms)