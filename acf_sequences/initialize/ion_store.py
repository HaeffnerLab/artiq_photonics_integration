from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms


class Ion_Storage(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("frequency/397_cooling")
        self.add_parameter("frequency/397_far_detuned")
        self.add_parameter("frequency/866_cooling")
     
        self.add_parameter("attenuation/397")
        self.add_parameter("attenuation/397_far_detuned")
        self.add_parameter("attenuation/866")

    @kernel
    def update_parameters(self):
        self.attenuation_397=self.exp.parameter_manager.get_float_param("attenuation/397")
        self.attenuation_866=self.exp.parameter_manager.get_float_param("attenuation/866")
        self.attenuation_397_far_detuned=self.exp.parameter_manager.get_float_param("attenuation/397_far_detuned")

        self.frequency_397_cooling=self.exp.parameter_manager.get_float_param("frequency/397_cooling")
        self.frequency_397_far_detuned=self.exp.parameter_manager.get_float_param("frequency/397_far_detuned")
        self.frequency_866_cooling=self.exp.parameter_manager.get_float_param("frequency/866_cooling")

    @kernel
    def run(self):


        
        self.dds_729_sp_aux.sw.off()
        self.dds_729_sp.set_att(13*dB)
        delay(2*us)
        self.dds_729_sp.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        # self.dds_Raman_1.sw.off()
        # self.dds_Raman_2.sw.off()
        delay(1*us)
        
        #set attenuation
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)

        #set frequency
        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_866_dp.set(self.frequency_866_cooling)

        delay(1*us)

        self.dds_866_dp.sw.on()
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.cfg_sw(True)
        delay(5*us)

        # self.dds_397_sigma.set(213*MHz)
        # self.dds_397_sigma.set_att(19*dB)

        # self.dds_397_sigma.sw.on()

