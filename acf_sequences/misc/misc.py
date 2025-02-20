from acf.sequence import Sequence

from artiq.experiment import kernel, BooleanValue

class FluoresceAndCount(Sequence):
    """Turn on 397 and 866 to fluoresce and return pmt counts."""

    def __init__(self):
        super().__init__()

        self.add_parameter("frequency/397_resonance")
        self.add_parameter("frequency/866_cooling")
        self.add_parameter("readout/pmt_sampling_time")
        self.add_argument("freq_already_set", BooleanValue(False))

    @kernel
    def run(self):
        return self.sequence(self.frequency_397_resonance,
                      self.frequency_866_cooling,
                      self.readout_pmt_sampling_time,
                      self.freq_already_set)

    @kernel
    def sequence(self, freq_397_resonance,
                       freq_866_cooling,
                       pmt_sampling_time,
                       freq_already_set):
        if not freq_already_set:
            self.dds_397_dp.set(freq_397_resonance)
            self.dds_866_dp.set(freq_866_cooling)

        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()

        num_pmt_pulses = self.ttl_pmt_input.count(
            self.ttl_pmt_input.gate_rising(pmt_sampling_time)
        )

        return num_pmt_pulses


