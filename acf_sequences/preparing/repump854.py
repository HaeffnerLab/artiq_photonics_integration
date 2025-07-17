from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms


class Repump854(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("attenuation/854_dp")
        self.add_parameter("frequency/854_dp")
        
        self.add_parameter("attenuation/866")
        self.add_parameter("frequency/866_cooling")
        # self.add_argument("interesting_arg", NumberValue(default=5*MHz, unit="MHz"))

        self.add_argument(
            "repump_854_time",
            NumberValue(default=60*us, min=5*us, max=1*ms, unit="us")
        )

    @kernel
    def run(self):
        
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_397_dp.sw.off()
        self.dds_397_far_detuned.cfg_sw(False)
        delay(2*us)
        # 854 repump
        self.dds_854_dp.set(self.frequency_854_dp)
        self.dds_866_dp.set(self.frequency_866_cooling)
        #print(self.attenuation_854_dp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        self.dds_866_dp.set_att(self.attenuation_866)
        
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(self.repump_854_time)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        #self.dds_854_dp.set_att(30*dB)
        delay(2*us)
