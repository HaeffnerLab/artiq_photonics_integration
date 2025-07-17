"""
Sequences container for ARTIQ experiments.
This module initializes and configures all experimental sequences used in the ARTIQ system.
Sequences are organized by functionality: cooling, readout, initialization, etc.
"""

# Core imports
from acf.sequences_container import SequencesContainer

# Cooling sequences
from acf_sequences.cooling.doppler import DopplerCool
from acf_sequences.cooling.sideband import SideBandCool
from acf_sequences.cooling.sideband_two_mode import SideBandCool2Mode
from acf_sequences.cooling.eit import EITCool
from acf_sequences.cooling.sideband_Raman import SideBandCool_Raman
from acf_sequences.cooling.sideband_radial import SideBandCool_Radial

# Readout sequences
from acf_sequences.readout.readout397 import ReadOut397
from acf_sequences.readout.readout397_diff import ReadOut397Diff
from acf_sequences.readout.readout_cam import readout_cam_two_ion

# Initialization sequences
from acf_sequences.initialize.ion_store import Ion_Storage
from acf_sequences.initialize.off_all import Off_DDS
from acf_sequences.initialize.init_device import Init_Device

# Rabi and excitation sequences
from acf_sequences.rabi.rabi import Rabi
from acf_sequences.trigger.trigger import LineTrigger, AWGTrigger

# Optical pumping sequences
from acf_sequences.preparing.repump854 import Repump854
from acf_sequences.preparing.oppump import Op_pump
from acf_sequences.preparing.oppump_sigma import Op_pump_sigma

# Van der Pol experiment sequences
from acf_sequences.Vdp.Vdp import VdP
from acf_sequences.Vdp.Vdp_2mode import VdP2Mode
from acf_sequences.Vdp.Vdp_2mode_one import VdP1mode

# Calibration sequences
from acf_sequences.calibrate.power_adjust import Adjust_729_Power
from acf_sequences.calibrate.calibrate_729_freq import Check_729_Freq
from acf_sequences.calibrate.calibrate_motion import Check_Motion
from acf_sequences.calibrate.calibrate_729_freq_Ramsey import Check_729_Freq_Ramsey
from acf_sequences.calibrate.calibrate_motion_SDF import Check_Motion_SDF
from acf_sequences.calibrate.calibrate_729_pi_pulse import Check_729_Pi_Pulse
# SDF sequences
from acf_sequences.SDF.SDF import SDF_single_ion
from acf_sequences.SDF.SDF import SDF_mode1
from acf_sequences.SDF.SDF import SDF_mode2

# RF sequences
from acf_sequences.rf.rf import RF

# Tickle sequences
from acf_sequences.SDF.Tickle import Tickle

# Utility sequences
from acf_sequences.misc.print_hi import PrintHi

# Initialize the sequences container
sequences = SequencesContainer()

# Readout sequences
sequences.add_sequence("readout_397", ReadOut397())
sequences.add_sequence("readout_397_diff", ReadOut397Diff())
sequences.add_sequence('cam_two_ions', readout_cam_two_ion())

# Cooling sequences
sequences.add_sequence("doppler_cool", DopplerCool())
sequences.add_sequence("eit_cool", EITCool())
sequences.add_sequence("sideband_cool", SideBandCool())
sequences.add_sequence("sideband_cool_2mode", SideBandCool2Mode())
sequences.add_sequence('sideband_Raman', SideBandCool_Raman())
sequences.add_sequence('sideband_Radial', SideBandCool_Radial())
# sequences.add_sequence("sideband_cool_cw", SideBandCoolCW())  # Commented out for future use

# Initialization sequences
sequences.add_sequence("ion_store", Ion_Storage())
sequences.add_sequence("off_dds", Off_DDS())
sequences.add_sequence("init_device", Init_Device())

# Rabi and excitation sequences
sequences.add_sequence("rabi", Rabi())
sequences.add_sequence('ac_trigger', LineTrigger())
sequences.add_sequence('awg_trigger', AWGTrigger())

# Optical pumping sequences
sequences.add_sequence("repump_854", Repump854())
sequences.add_sequence('op_pump', Op_pump())
sequences.add_sequence('op_pump_sigma', Op_pump_sigma())

# Van der Pol experiment sequences
sequences.add_sequence('vdp', VdP())
sequences.add_sequence('vdp2mode_one', VdP1mode())
sequences.add_sequence('vdp2mode', VdP2Mode())

# Calibration sequences
sequences.add_sequence('adjust_729_power', Adjust_729_Power())
sequences.add_sequence('adjust_729_freq', Check_729_Freq())
sequences.add_sequence('adjust_729_freq_ramsey', Check_729_Freq_Ramsey())
sequences.add_sequence('adjust_729_pi_pulse', Check_729_Pi_Pulse())
# Utility sequences
sequences.add_sequence("print_hi", PrintHi())

# SDF sequences
sequences.add_sequence('sdf_single_ion', SDF_single_ion())
sequences.add_sequence('sdf_mode1', SDF_mode1())
sequences.add_sequence('sdf_mode2', SDF_mode2())

# RF sequences
sequences.add_sequence('rf', RF())

# Calibration sequences
sequences.add_sequence('calibrate_motion', Check_Motion())
sequences.add_sequence('calibrate_motion_SDF', Check_Motion_SDF())

# Tickle sequences
sequences.add_sequence('tickle', Tickle())