from acf.sequences_container import SequencesContainer
from acf_sequences.cooling.doppler import DopplerCool
from acf_sequences.cooling.sideband import SideBandCool
from acf_sequences.cooling.sideband_two_mode import SideBandCool2Mode
from acf_sequences.misc.print_hi import PrintHi
from acf_sequences.preparing.repump854 import Repump854
from acf_sequences.readout.readout397 import ReadOut397

from acf_sequences.readout.readout397_diff import ReadOut397Diff

from acf_sequences.initialize.ion_store import Ion_Storage

from acf_sequences.initialize.off_all import Off_DDS
from acf_sequences.initialize.init_device import Init_Device

from acf_sequences.rabi.rabi import Rabi
from acf_sequences.rabi.displace import Displacement
from acf_sequences.trigger.trigger import LineTrigger, AWGTrigger

from acf_sequences.preparing.oppump import Op_pump
from acf_sequences.preparing.oppump_sigma import Op_pump_sigma

from acf_sequences.cooling.eit import EITCool
from acf_sequences.Vdp.Vdp import VdP
from acf_sequences.Vdp.Vdp_2mode import VdP2Mode
from acf_sequences.Vdp.Vdp_2mode_one import VdP1mode

from acf_sequences.readout.readout_cam import readout_cam_two_ion
sequences = SequencesContainer()

sequences.add_sequence("readout_397", ReadOut397())
sequences.add_sequence("readout_397_diff", ReadOut397Diff())

sequences.add_sequence("repump_854", Repump854())
sequences.add_sequence("eit_cool", EITCool())
sequences.add_sequence("sideband_cool", SideBandCool())
sequences.add_sequence("sideband_cool_2mode", SideBandCool2Mode())
# sequences.add_sequence("sideband_cool_cw", SideBandCoolCW())
sequences.add_sequence("doppler_cool", DopplerCool())
sequences.add_sequence("ion_store", Ion_Storage())
sequences.add_sequence("off_dds", Off_DDS())
sequences.add_sequence("init_device", Init_Device())
sequences.add_sequence("rabi", Rabi())
sequences.add_sequence('ac_trigger',LineTrigger())
sequences.add_sequence('awg_trigger',AWGTrigger())


sequences.add_sequence('op_pump',Op_pump())
sequences.add_sequence('op_pump_sigma',Op_pump_sigma())
 

sequences.add_sequence("print_hi", PrintHi())

sequences.add_sequence('displacement',Displacement())

sequences.add_sequence('vdp', VdP())
sequences.add_sequence('vdp2mode_one', VdP1mode())
sequences.add_sequence('vdp2mode', VdP2Mode())

sequences.add_sequence('cam_two_ions', readout_cam_two_ion())