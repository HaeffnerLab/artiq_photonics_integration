from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz


class EITCool(Sequence):

    def __init__(self):
        super().__init__()

        # 397 pi light
        self.add_parameter("frequency/397_cooling")
        self.add_parameter("attenuation/397")

        # 397 sigma minus light 
        self.add_argument_from_parameter("frequency_397_sigma", "EIT_cooling/freq_397_sigma") 
        self.add_argument_from_parameter("attenuation_397_sigma", "EIT_cooling/att_397_sigma") 

        # 866
        self.add_parameter("frequency/866_cooling")
        self.add_parameter("attenuation/866")

        # EIT cooling time
        self.add_argument_from_parameter("eit_cooling_time", "EIT_cooling/cooling_time") 

    @kernel
    def run(self):

        self.eit_run(self.frequency_397_cooling,
                     self.frequency_397_sigma,
                     self.frequency_866_cooling,
                    
                     self.attenuation_397,
                     self.attenuation_397_sigma,
                     self.attenuation_866,

                     self.eit_cooling_time
                     )

    @kernel
    def eit_run(self,   freq_397_cooling,
                        freq_397_sigma,
                        freq_866_cooling,
                        attenuation_397,
                        attenuation_397_sigma,
                        attenuation_866,
                        eit_cooling_time
                        ):

     
        # 866
        self.dds_866_dp.set(freq_866_cooling)
        self.dds_866_dp.set_att(attenuation_866)

        # 397 pi light
        self.dds_397_dp.set_att(attenuation_397) 
        self.dds_397_dp.set(freq_397_cooling)

        # 397 sigma minus light 
        self.dds_397_sigma.set_att(attenuation_397_sigma) 
        self.dds_397_sigma.set(freq_397_sigma)        

        #coarse cooling
        self.dds_397_dp.sw.on()
        self.dds_397_sigma.sw.on()
        self.dds_866_dp.sw.on()

        delay(eit_cooling_time)

        self.dds_397_dp.sw.off()
        self.dds_397_sigma.sw.off()
        self.dds_866_dp.sw.off()



        # for i in range(10):

        #     # ground state optical pumping
        #     self.dds_729_dp.sw.on()
        #     self.dds_729_sp.sw.on()
        #     delay(10*us)
        #     self.dds_729_dp.sw.off()

        #     self.dds_854_dp.set_att(10*dB)
        #     self.dds_866_dp.set_att(15*dB)
        #     self.dds_854_dp.sw.on()
        #     self.dds_866_dp.sw.on()
        #     delay(10*us)
        #     self.dds_854_dp.sw.off()
        #     self.dds_866_dp.sw.off()
        
        # self.dds_729_dp.sw.off()
        # self.dds_729_sp.sw.off()
        # self.dds_854_dp.sw.off()
        # self.dds_866_dp.sw.off()

