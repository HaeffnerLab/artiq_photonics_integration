from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ns
from numpy import int32, int64

class Rabi(Sequence):

    def __init__(self):
        super().__init__()

    @kernel
    def run(self,
            pulse_time,
            frequency_729_dp,
            attenuation_729_dp,
        ):

        self.core.break_realtime()
        delay(10*us)
        
        self.dds_729_dp.set_frequency(frequency_729_dp)

        delay(10*us)

        self.dds_729_dp.set_att(attenuation_729_dp)
        #delay(5*us)
        
        delay(10*us)

        self.dds_729_dp.sw.pulse(pulse_time)
        delay(10*us)
       