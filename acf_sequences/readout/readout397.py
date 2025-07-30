from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms

import numpy as np
class ReadOut397(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("readout/pmt_sampling_time")

        self.add_parameter("attenuation/397")
        self.add_parameter("attenuation/866")
        self.add_parameter("frequency/397_resonance")
        self.add_parameter("frequency/866_cooling")
        

    @kernel
    def run(self, 
         freq_397_dp=-1.0*MHz, 
         freq_866_dp=-1.0*MHz,
         turn_off_866=False)-> np.int32:

        if freq_397_dp < 0.0:
            freq_397_dp = self.frequency_397_resonance

        self.core.break_realtime()
        delay(10*us)

        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_dp.set(freq_397_dp)

        self.core.break_realtime()
        delay(10*us)

        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)

        self.core.break_realtime()
        delay(10*us)

        self.dds_729_dp.sw.off()
        self.dds_397_dp.sw.on()
        if turn_off_866:
            self.dds_866_dp.sw.off()
        else:
            self.dds_866_dp.sw.on()

        self.core.break_realtime()
        delay(10*us)

        num_pmt_pulses = self.ttl_pmt_input.count(
            self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
        )
        with sequential:
            delay(20*us)
            self.dds_397_dp.sw.off()
            self.dds_866_dp.sw.off()
        
        delay(20*us)

        return num_pmt_pulses
