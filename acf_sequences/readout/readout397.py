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
    def run(self, turn_off_866=False)-> np.int32:

        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_dp.set(self.frequency_397_resonance)

        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_729_dp.sw.off()
        self.dds_397_dp.sw.on()
        if turn_off_866:
            self.dds_866_dp.sw.off()
        else:
            self.dds_866_dp.sw.on()

        with parallel:

            num_pmt_pulses = self.ttl_pmt_input.count(
                self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
            )
            with sequential:
                delay(20*us+self.readout_pmt_sampling_time)
                self.dds_397_dp.sw.off()
                self.dds_866_dp.sw.off()
        
        delay(10*us)

        return num_pmt_pulses
