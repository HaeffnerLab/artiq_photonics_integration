from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms




class Op_pump_sigma(Sequence):

    def __init__(self):
        super().__init__()
        
        # 866
        self.add_parameter("attenuation/866")
        self.add_parameter("frequency/866_cooling")

        #sigma minus 397 light 
        self.add_parameter("optical_pumping/pump_time_sigma")
        self.add_parameter("optical_pumping/att_397_sigma")
        self.add_parameter("frequency/397_resonance")

    @kernel
    def run(self):
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)

        self.dds_397_sigma.set(self.frequency_397_resonance)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)

        self.dds_729_dp.sw.off()
        self.dds_866_dp.sw.on()
        self.dds_397_sigma.sw.on()

        delay(self.optical_pumping_pump_time_sigma)

        self.dds_866_dp.sw.off()
        self.dds_397_sigma.sw.off()
        delay(5*us)
