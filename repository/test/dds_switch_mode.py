from artiq.experiment import *                                             
from artiq.coredevice.ad9910 import (RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_RAMPUP)

class simple_example2(EnvExperiment):
    def build(self): 
        self.setattr_device("core")                                       
        self.dds = self.get_device("urukul2_ch3")                           
      
    @kernel 
    def run(self):
        self.core.break_realtime()
        delay(100*ms)
       
        self.dds.cpld.init() 
        self.dds.init()              
        self.dds.sw.on()    
        delay(100*ms)
        self.profile0_set()
        
        print("Starting loop")                                                                    
        for i in range(1000):  
            delay(1*ms)
            self.dds.cpld.set_profile(0) 
            delay(100*ms)
            self.dds.cpld.set_profile(1)
            delay(100*ms) 
            self.dds.set(1*MHz, amplitude = 1.0, profile=1) # This command does not do anything.

        
    @kernel
    def profile0_set(self):
        data_ram = [-262144, -43253760, -86245376, -128974848, -171966464, -214958080, -257949696, -300941312, -343932928, -386662400, -429654016, -472645632, 
        -515637248, -558628864, -601620480, -644349952, -687341568, -730333184, -773324800, -816316416, -859308032, -902037504, -945029120, -988020736, -1031012352,
        -1074003968, -1116995584, -1159725056, -1202716672, -1245708288, -1288699904, -1331691520, -1374683136, -1417412608, -1460404224, -1503395840, -1546387456,
        -1589379072, -1632370688, -1675100160, -1718091776, -1761083392, -1804075008, -1847066624, -1890058240, -1932787712, -1975779328, -2018770944, -2061762560,
        -2104754176, -2147483648, 2104492032, 2061500416, 2018508800, 1975517184, 1932525568, 1889796096, 1846804480, 1803812864, 1760821248, 1717829632, 1674838016, 
        1632108544, 1589116928, 1546125312, 1503133696, 1460142080, 1417150464, 1374420992, 1331429376, 1288437760, 1245446144, 1202454528, 1159462912, 1116733440,
        1073741824, 1030750208, 987758592, 944766976, 901775360, 859045888, 816054272, 773062656, 730071040, 687079424, 644087808, 601358336, 558366720, 515375104, 
        472383488, 429391872, 386400256, 343670784, 300679168, 257687552, 214695936, 171704320, 128712704, 85983232, 42991616] # This corresponds to a 100 point scan between 1.0 and 0.0 in mu
       
        self.dds.cpld.set_profile(0)
        self.dds.set_profile_ram(start=0 , end=0 + len(data_ram) - 1,step=250,profile=0,mode=RAM_MODE_BIDIR_RAMP)  
        self.dds.cpld.io_update.pulse_mu(8)
        delay(10*ms)
        self.dds.write_ram(data_ram)  
        delay(5*ms) 
        self.dds.set_cfr1(ram_enable=1, ram_destination=RAM_DEST_ASF)         
        self.dds.set_frequency(1*MHz)                                        
        self.dds.cpld.io_update.pulse_mu(8)                                   
        self.dds.set_att(10*dB)  