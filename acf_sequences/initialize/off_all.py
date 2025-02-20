from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms


class Off_DDS(Sequence):

    def __init__(self):
        super().__init__()


    @kernel
    def run(self):

        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_rf_g_qubit.sw.off()
        delay(2*us)

        self.dds_866_dp.sw.off()
        self.dds_397_dp.sw.off()
        self.dds_397_far_detuned.sw.off()
        self.dds_397_sigma.sw.off()
        delay(2*us)

        

