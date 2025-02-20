from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms


class Init_Device(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("frequency/397_cooling")
        self.add_parameter("frequency/397_far_detuned")
        self.add_parameter("frequency/866_cooling")

        self.add_parameter("frequency/729_dp")
        self.add_parameter("frequency/729_sp")
        self.add_parameter("frequency/854_dp")

        self.add_parameter("attenuation/397")
        self.add_parameter("attenuation/397_far_detuned")
        self.add_parameter("attenuation/866")
        self.add_parameter("attenuation/729_dp")
        self.add_parameter("attenuation/729_sp")
        self.add_parameter("attenuation/854_dp")


    @kernel
    def run(self):

        # Init devices
        self.exp.core.break_realtime()
        self.dds_397_dp.init()
        self.dds_397_far_detuned.init()
        self.dds_866_dp.init()
        self.dds_729_dp.init()
        self.dds_729_sp.init()
        self.dds_854_dp.init()
        delay(5*us)
        
        # Set attenuations
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)

        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_729_sp_aux.set_att(self.attenuation_729_sp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        delay(5*us)

        # Set frequencies
        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        
        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_sp_aux.set(self.frequency_729_sp)

        self.dds_854_dp.set(self.frequency_854_dp)
        
        delay(5*us)

        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_397_dp.sw.off()
        self.dds_397_far_detuned.sw.off()
        self.dds_rf_g_qubit.sw.off()

        delay(5*us)
        

