# utils/init_default_params.py
from artiq.experiment import *

_DEFAULTS = {
    "frequency/397_cooling":    (200*MHz, "MHz"),
    "frequency/866_cooling":    ( 85*MHz, "MHz"),
    "frequency/397_far_detuned":(205*MHz, "MHz"),
    "attenuation/397":          (  23.5,   "dB"),
    "attenuation/866":          (  12.0,   "dB"),
    "frequency/397_resonance":(215*MHz, "MHz"),
    "attenuation/854_dp":(  12.0,   "dB"),
    "frequency/854_dp":(80*MHz, "MHz"),
    "EIT_cooling/freq_397_sigma":(200*MHz, "MHz"),
    "EIT_cooling/att_397_sigma":(  20.0,   "dB"),
    "EIT_cooling/cooling_time":(100*us, "s"),
    "sideband/vib_freq": (100*MHz, "MHz"),
    "sideband/att_729": (  20.0,   "dB"),
    "sideband/att_854": (  20.0,   "dB"),
    "sideband/att_866": (  20.0,   "dB"),
    "optical_pumping/pump_time_sigma":(100*us, "s"),
    "optical_pumping/att_397_sigma": (  20.0,   "dB"),
    "frequency/729_dp":(200*MHz, "MHz"),
    "qubit/Sm1_2_Dm1_2":(200*MHz, "MHz"),
    "qubit/Sm1_2_Dm5_2":(200*MHz, "MHz"),
    "qubit/Sm1_2_Dm3_2":(200*MHz, "MHz"),
    "qubit/S1_2_D3_2":(200*MHz, "MHz"),
    "qubit/S1_2_Dm3_2":(200*MHz, "MHz"),
    "optical_pumping/att_729_dp":(  20.0,   "dB"),
    "optical_pumping/att_854_dp":(  20.0,   "dB"),
    "optical_pumping/att_866_dp":(  20.0,   "dB"),
    "sideband2mode/att_729_dp":(  20.0,   "dB"),
    "sideband2mode/vib_freq1":(  100*MHz,   "MHz"),
    "sideband2mode/vib_freq2":(  100*MHz,   "MHz"),
    "sideband2mode/att_854":(  20.0,   "dB"),
    "sideband2mode/att_866":(  20.0,   "dB"),
    "attenuation/729_dp":(  20.0,   "dB"),
    "attenuation/397_far_detuned":(  18.0,   "dB"),
    "doppler_cooling/cooling_time":(100*us, "s"),
    "doppler_cooling/att_397": (  20.0,   "dB"),
    "readout/threshold":(  10.0,   "V"),
    "qubit/Sm1_2_S1_2":(200*MHz, "MHz"),
    "frequency/397_sigma":(200*MHz, "MHz"),
    "qubit/vib_freq":(200*MHz, "MHz"),
    "readout/pmt_sampling_time":(100*us, "s"),
    "SDF/beta_range_us": (100*us, "us"),
    "SDF/num_beta": (100, "V"),
    "readout/threshold0": (0.0, "V"),
}

class InitAllDefaults(EnvExperiment):
    def run(self):
        for name, (value, unit) in _DEFAULTS.items():
            key = "__param__" + name
            if self.get_dataset(key, default=None) is None:
                self.set_dataset(key, value, unit=unit, persist=True)
                print("seeded", key)
            else:
                print("exists", key, "exists")
