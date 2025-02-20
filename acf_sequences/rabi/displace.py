from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz
from numpy import int32, int64

class Displacement(Sequence):

    def __init__(self):
        super().__init__()
    @kernel
    def run(self, 
            drive_time, 
            displace_att_729_dp, displace_att_729_sp, displace_att_729_sp_aux,
            displace_freq_729_dp, displace_freq_729_sp, displace_freq_729_sp_aux,
            drive_phase_sp:float = 0.0, drive_phase_sp_aux:float =0.0, ref_time_mu=int64(-1)
            ):
        
        #set attenuation
        self.dds_729_dp.set_att(displace_att_729_dp)
        self.dds_729_sp.set_att(displace_att_729_sp)
        self.dds_729_sp_aux.set_att(displace_att_729_sp_aux)

        #set frequency
        self.dds_729_dp.set(displace_freq_729_dp,         phase=0.0                , ref_time_mu=ref_time_mu)
        self.dds_729_sp.set(displace_freq_729_sp,         phase=drive_phase_sp    , ref_time_mu=ref_time_mu)
        self.dds_729_sp_aux.set(displace_freq_729_sp_aux, phase=drive_phase_sp_aux, ref_time_mu=ref_time_mu)

        #turn on the 729
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.on()
        delay(drive_time)
        self.dds_729_dp.sw.off()
