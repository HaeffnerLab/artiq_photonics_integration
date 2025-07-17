from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms


class Off_DDS(Sequence):

    def __init__(self):
        super().__init__()


    @kernel
    def run(self):
        
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(False)
    
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        delay(1*us)
        self.dds_854_dp.sw.off()
        self.dds_Raman_1.sw.off()
        delay(1*us)
        self.dds_Raman_1.sw.off()
        self.dds_Raman_2.sw.off()
        delay(1*us)
        self.dds_866_dp.sw.off()
        self.dds_397_dp.sw.off()
        self.dds_397_far_detuned.cfg_sw(False)
        self.dds_397_sigma.sw.off()
        delay(1*us)

        

