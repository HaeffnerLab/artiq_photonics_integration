from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, ms, dB, us, NumberValue, MHz


class DopplerCool(Sequence):


    def __init__(self):
        super().__init__()

        self.add_parameter("frequency/397_cooling")
        #self.add_parameter("frequency/397_cooling_stark")
        self.add_parameter("frequency/866_cooling")
        self.add_parameter("frequency/397_far_detuned")
        
        self.add_parameter("attenuation/866")
        self.add_parameter("attenuation/397_far_detuned")

      
        self.add_argument_from_parameter("attenuation_397", "doppler_cooling/att_397") 

        self.add_parameter("doppler_cooling/cooling_time")


        # self.add_argument("interesting_arg", NumberValue(default=5*MHz, unit="MHz"))

    @kernel
    def run(self, att_397=-1.0, freq_397=-1.0, doppler_time=-1.0):

        if att_397>0:
            self.attenuation_397 = att_397
        
        if doppler_time>0:
            self.doppler_cooling_cooling_time =  doppler_time
        
        if freq_397>0:
            self.frequency_397_cooling =freq_397
        

        self.doppler(self.frequency_397_cooling,
                    self.frequency_866_cooling,
                    self.frequency_397_far_detuned,
                    self.attenuation_397,
                    self.attenuation_866,
                    self.attenuation_397_far_detuned,
                    self.doppler_cooling_cooling_time)

    @kernel
    def doppler(self, freq_397_cooling,
                       freq_866_cooling,
                       freq_397_far_detuned,
                       attenuation_397,
                       attenuation_866,
                       attenuation_397_far_detuned,
                       doppler_cooling_time):
        
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()
        delay(10*ms)  # Ensure proper initialization timing with larger buffer

        #set initial parameters for all the lasers
        self.dds_397_far_detuned.set(freq_397_far_detuned)
        delay(5*ms)
        self.dds_397_far_detuned.set_att(attenuation_397_far_detuned)
        delay(5*ms)

        self.dds_866_dp.set(freq_866_cooling)
        delay(5*ms)
        self.dds_866_dp.set_att(attenuation_866)
        delay(5*ms)

        self.dds_397_dp.set_att(attenuation_397)
        delay(5*ms) 
        self.dds_397_dp.set(freq_397_cooling)
        delay(5*ms)

        #coarse cooling
        self.dds_397_dp.set(freq_397_cooling)#+3*MHz)
        delay(3*ms)
        self.dds_397_dp.sw.on()
        delay(2*ms)
        self.dds_397_far_detuned.cfg_sw(True)
        delay(2*ms)
        self.dds_866_dp.sw.on()
        delay(doppler_cooling_time * 0.2)

        #fine cooling      
        self.dds_397_dp.set(freq_397_cooling)
        delay(3*ms)
        self.dds_397_far_detuned.cfg_sw(False)
        delay(2*ms)
        self.dds_397_dp.set_att(attenuation_397+2*dB)
        delay(doppler_cooling_time * 0.3)

        
        delay(doppler_cooling_time * 0.5)
        
        #turn off the cooling laser at the end 
        self.dds_397_far_detuned.cfg_sw(False)
        delay(2*ms)
        self.dds_397_dp.sw.off()
        delay(2*ms)
        self.dds_866_dp.sw.off()
        delay(5*ms)

