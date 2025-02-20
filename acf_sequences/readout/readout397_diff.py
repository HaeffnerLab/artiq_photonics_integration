from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms

import numpy as np
class ReadOut397Diff(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("readout/pmt_sampling_time")

        self.add_parameter("attenuation/397")
        self.add_parameter("attenuation/866")
        self.add_parameter("frequency/397_resonance")
        self.add_parameter("frequency/866_cooling")

    @kernel
    def run(self):

        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_dp.set(self.frequency_397_resonance)

        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)

        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_729_dp.sw.off()
        
        num_pmt_pulses1=0
        num_pmt_pulses2=0

        with parallel:

            num_pmt_pulses1 = self.ttl_pmt_input.count(
                self.ttl_pmt_input.gate_rising(self.m_pmt_sampling_time)
            )
            with sequential:
                delay(20*us+self.readout_pmt_sampling_time)
                
        delay(50*us)
        self.dds_866_dp.sw.off()
        delay(50*us)
        
        with parallel:

            num_pmt_pulses2 = self.ttl_pmt_input.count(
                self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
            )
            with sequential:
                delay(20*us+self.readout_pmt_sampling_time)
                self.dds_397_dp.sw.off()
                self.dds_866_dp.sw.off() 
        
        delay(5*us)

        return num_pmt_pulses1-num_pmt_pulses2
