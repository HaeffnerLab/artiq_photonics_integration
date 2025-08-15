from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz
from numpy import int32, int64

class Rabi(Sequence):

    def __init__(self):
        super().__init__()

    @kernel
    def run(self,
            pulse_time,
            frequency_729_dp,
            frequency_729_sp,
            attenuation_729_dp,
            attenuation_729_sp,
            amp_729_dp=1.0,
            phase:float=0.0,
            ref_time_mu=int64(-1)
        ):

        # in the register, the phase is pow_/65536
        # in turns (meaning how many 2pi, 1 turn means 2pi)
        # Ensure sufficient timeline slack before issuing DDS configuration to avoid RTIO underflow
        self.core.break_realtime()
        delay(2*us)
        self.dds_729_dp.set(frequency_729_dp, phase=0.0, amplitude=amp_729_dp, ref_time_mu=ref_time_mu)
        self.dds_729_sp.set(frequency_729_sp, phase=phase, ref_time_mu=ref_time_mu)

        self.dds_729_dp.set_att(attenuation_729_dp)
        self.dds_729_sp.set_att(attenuation_729_sp)
        #delay(5*us)
        
        delay(1*us)
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.on()
        
        delay(pulse_time)
        self.dds_729_dp.sw.off()
        delay(1*us)
       
