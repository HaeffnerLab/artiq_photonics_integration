from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz
from numpy import int32, int64

class Displacement(Sequence):

    def __init__(self):
        super().__init__()
    @kernel
    def run(self, 
            drive_time, 
            displace_att_729_dp,
            displace_freq_729_dp,
            ref_time_mu=int64(-1)
            ):
        
        #set attenuation
        self.dds_729_dp.set_att(displace_att_729_dp)

        #set frequency
        self.dds_729_dp.set(displace_freq_729_dp,         phase=0.0                , ref_time_mu=ref_time_mu)

        #turn on the 729
        self.dds_729_dp.sw.on()
        delay(drive_time)
        self.dds_729_dp.sw.off()