# utils/init_default_params.py
from artiq.experiment import *

_DEFAULTS = {
    "frequency/397_cooling":    (110*MHz, "Hz"),
    "frequency/866_cooling":    ( 80*MHz, "Hz"),
    "frequency/397_far_detuned":(200*MHz, "Hz"),
    "attenuation/397":          (  3.0,   "dB"),
    "attenuation/866":          (  0.0,   "dB"),
    "frequency/397_resonance":(200*MHz, "Hz"),
    "attenuation/854_dp":(  0.0,   "dB"),
    "frequency/854_dp":(200*MHz, "Hz"),
    "EIT_cooling/freq_397_sigma":(200*MHz, "Hz"),
    "EIT_cooling/att_397_sigma":(  0.0,   "dB"),
    "EIT_cooling/cooling_time":(100*us, "s"),
    "sideband/vib_freq": (100*MHz, "Hz"),
    "sideband/att_729": (  0.0,   "dB"),
    "sideband/att_854": (  0.0,   "dB"),
    "sideband/att_866": (  0.0,   "dB"),
    "optical_pumping/pump_time_sigma":(100*us, "s"),
    "optical_pumping/att_397_sigma": (  0.0,   "dB"),
    "frequency/729_sp":(200*MHz, "Hz"),
    "attenuation/729_sp":(  0.0,   "dB"),
    "frequency/729_dp":(200*MHz, "Hz"),
    "qubit/Sm1_2_Dm1_2":(200*MHz, "Hz"),
    "qubit/Sm1_2_Dm5_2":(200*MHz, "Hz"),
    "qubit/Sm1_2_Dm3_2":(200*MHz, "Hz"),
    "qubit/S1_2_D3_2":(200*MHz, "Hz"),
    "qubit/S1_2_Dm3_2":(200*MHz, "Hz"),
    "optical_pumping/att_729_dp":(  0.0,   "dB"),
    "optical_pumping/att_854_dp":(  0.0,   "dB"),
    "optical_pumping/att_866_dp":(  0.0,   "dB"),
    "optical_pumping/att_729_sp":(  0.0,   "dB"),
    "sideband2mode/att_729_dp":(  0.0,   "dB"),
    "sideband2mode/freq_729_sp":(  0.0,   "dB"),
    "sideband2mode/att_729_sp":(  0.0,   "dB"),
    "sideband2mode/vib_freq1":(  0.0,   "Hz"),
    "sideband2mode/vib_freq2":(  0.0,   "Hz"),
    "sideband2mode/att_854":(  0.0,   "dB"),
    "sideband2mode/att_866":(  0.0,   "dB"),
    "attenuation/729_dp":(  0.0,   "dB"),
    "attenuation/397_far_detuned":(  0.0,   "dB"),
    "doppler_cooling/cooling_time":(100*us, "s"),
    "doppler_cooling/att_397": (  0.0,   "dB"),
    "readout/threshold":(  0.0,   "dB"),
    "qubit/Sm1_2_S1_2":(200*MHz, "Hz"),
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
