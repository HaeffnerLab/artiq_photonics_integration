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


# SDF sequences
from acf_sequences.SDF.SDF import SDF_single_ion
from acf_sequences.SDF.SDF import SDF_mode1
from acf_sequences.SDF.SDF import SDF_mode2


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

# Utility sequences
sequences.add_sequence("print_hi", PrintHi())

# SDF sequences
sequences.add_sequence('sdf_single_ion', SDF_single_ion())
sequences.add_sequence('sdf_mode1', SDF_mode1())
sequences.add_sequence('sdf_mode2', SDF_mode2())



# Tickle sequences
sequences.add_sequence('tickle', Tickle())