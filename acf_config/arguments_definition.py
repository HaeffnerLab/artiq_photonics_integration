from acf.argument_manager import ArgumentManager
from artiq.language.units import *
import numpy as np

argument_manager = ArgumentManager()

###
##  RF Signal Arguments
###

# 397
freq_397_min = 190*MHz
freq_397_max = 245*MHz
argument_manager.add_argument(
    "freq_397_resonance",
    default_parameter="frequency/397_resonance",
    unit="MHz",
    min=freq_397_min,
    max=freq_397_max,
    tooltip="Resonance frequency for 397 RF signal."
)

argument_manager.add_argument(
    "freq_397_cooling",
    default_parameter="frequency/397_resonance",
    param_mod_func=lambda freq : freq - 10*MHz,
    unit="MHz",
    min=freq_397_min,
    max=freq_397_max,
    tooltip="Cooling frequency for 397 RF signal."
)

argument_manager.add_argument(
    "attenuation_397",
    default_value=11*dB,
    unit="dB",
    min=9*dB,
    tooltip="Attenuation for the 397 RF signal."
)

argument_manager.add_argument(
    "freq_397_far_detuned",
    default_value=80*MHz,
    unit="MHz",
    min=70*MHz,
    max=90*MHz,
    tooltip="Far detuned frequency for 397 RF signal."
)
argument_manager.add_argument(
    "attenuation_397_far_detuned",
    default_value=16.3*dB,
    unit="dB",
    min=10*dB
)

# 866
freq_866_min = 65*MHz
freq_866_max = 95*MHz
argument_manager.add_argument(
    "freq_866_resonance",
    default_parameter="frequency/866_resonance",
    unit="MHz",
    min=freq_866_min,
    max=freq_866_max,
    tooltip="Resonance frequency for 866 RF signal."
)
argument_manager.add_argument(
    "freq_866_cooling",
    default_parameter="frequency/866_cooling",
    #param_mod_func=lambda freq : freq + 20*MHz,
    # param_mod_func=lambda freq : freq,
    unit="MHz",
    min=freq_866_min,
    max=freq_866_max,
    tooltip="Cooling frequency for 866 RF signal."
)
argument_manager.add_argument(
    "attenuation_866",
    default_value=8.43*dB,
    unit="dB",
    min=8.0*dB,
    tooltip="Attenuation for the 866 RF signal."
)
argument_manager.add_argument(
    "freq_866_addressing",
    default_value=85*MHz,
    unit="MHz",
    min=60*MHz, 
    max=90*MHz,
    tooltip="Frequency for the 866 addressing RF signal."
)
argument_manager.add_argument(
    "attenuation_866_addressing",
    default_value=14.5*dB,
    unit="dB",
    min=13*dB,
    tooltip="Attenuation for the 866 addressing RF signal."
)

# 729
argument_manager.add_argument(
    "freq_729_sp",
    default_value=80*MHz,
    unit="MHz",
    min=60*MHz, 
    max=90*MHz,
    tooltip="Frequency for the 729 single pass RF signal."
)

argument_manager.add_argument(
    "attenuation_729_sp",
    default_value=7*dB,
    unit="dB",
    min=6*dB,
    tooltip="Attenuation for the 729 single pass RF signal."
)


argument_manager.add_argument(
    "phase_729_sp",
    default_value=0.0,
 
    min=0.0,
    max = 1.0,
    tooltip="Phase for the 729 single pass RF signal."
)

argument_manager.add_argument(
    "freq_729_sp_aux",
    default_value=80*MHz,
    unit="MHz",
    min=60*MHz, 
    max=90*MHz,
    tooltip="Frequency for the 729 single pass aux RF signal."
)


argument_manager.add_argument(
    "attenuation_729_sp_aux",
    default_value=7.0*dB,
    unit="dB",
    min=6.0*dB,
    tooltip="Attenuation for the 729 single pass aux RF signal."
)

argument_manager.add_argument(
    "phase_729_sp_aux",
    default_value= 0.53,
 
    min=0,
    max = 1.0,
    tooltip="Phase for the 729 single pass RF signal."
)


argument_manager.add_argument(
    "attenuation_729_dp",
    default_value=9*dB,
    unit="dB",
    min=8.0*dB,
    tooltip="Attenuation for the 729 double pass RF signal."
)


# 854
argument_manager.add_argument(
    "freq_854_dp",
    default_value=80.0*MHz,
    unit="MHz",
    min=60*MHz, 
    max=90*MHz,
    tooltip="Frequency for the 854 double pass RF signal."
)
argument_manager.add_argument(
    "attenuation_854_dp",
    default_value=3*dB,
    unit="dB",
    min=3.0*dB,
    tooltip="Attenuation for the 854 double pass RF signal."
)

# rf ground state qubit
argument_manager.add_argument(
    "freq_rf_g_qubit",
    default_value=8.96*MHz,
    unit="MHz",
    min=8*MHz, 
    max=12*MHz,
    tooltip="Frequency for the ground state qubit."
)
argument_manager.add_argument(
    "attenuation_rf_g_qubit",
    default_value=5*dB,
    unit="dB",
    min=3.0*dB,
    tooltip="Attenuation for the ground state qubit RF signal."
)




###
##  Misc Arguments
###
argument_manager.add_argument(
    "doppler_cooling_time",
    default_value=500*us,
    unit="us",
    tooltip="The time it takes to do the cooling."
)

argument_manager.add_argument(
    "pmt_sampling_time",
    default_value=10*ms,
    unit="ms",
    tooltip="Time to take pmt counts for each sample."
)

