from acf.sequence import Sequence
from artiq.experiment import *
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import stark_shift_kernel

class SDF_single_ion(Sequence):

    def __init__(self):
        super().__init__()

    def build(self):
        super().build()

        # Readout mode 2
        self.del_m=self.parameter_manager.get_param("SDF/mode_single_ion/delta_m") 
        self.del_s=self.parameter_manager.get_param("SDF/mode_single_ion/delta_s") 

        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode_single_ion/att_729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group='Readout Mode Single Ion'
        )

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP1mode/vib_freq")+self.del_s-self.del_m, min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Readout Mode Single Ion'
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP1mode/vib_freq")+self.del_s+self.del_m, min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Readout Mode Single Ion'
        )

        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='Readout Mode Single Ion'
        )
        
        self.setattr_argument(
            "amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp_aux"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='Readout Mode Single Ion'
        )

    @kernel
    def prepare(self, use_motion_tracking=False):
        if use_motion_tracking:
            vib_freq=self.exp.seq.calibrate_motion.get_motional_freq_tracker(mode='mode_single_ion')
        else:
            vib_freq=self.parameter_manager.get_float_param("VdP1mode/vib_freq")
        freq_729_sp=self.parameter_manager.get_float_param("frequency/729_sp")

        self.freq_729_sp=freq_729_sp-vib_freq+self.del_s
        self.freq_729_sp_aux=freq_729_sp+vib_freq+self.del_s

    @kernel
    def run(self, pulse_length, att_729_dp=-1.0):
        if att_729_dp >0:
            self.dds_729_dp.set_att(att_729_dp)
        else:
            self.dds_729_dp.set_att(self.att_729_dp)
        self.ttl_rf_switch_AWG_729SP.on()
        #turn on 
        self.ttl_awg_trigger.pulse(1*us)
        delay(2*us)
        if (pulse_length>10*ns):
            self.dds_729_dp.sw.on()
            delay(pulse_length)
            self.dds_729_dp.sw.off()


class SDF_mode1(Sequence):

    def __init__(self):
        super().__init__()

    def build(self):
        super().build()

        # Readout mode 2
        self.del_m1=self.parameter_manager.get_param("SDF/mode1/delta_m") 
        self.del_s1=self.parameter_manager.get_param("SDF/mode1/delta_s") 

        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode1/att_729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group='Readout Mode 1'
        )

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP2mode/vib_freq1")+self.del_s1-self.del_m1, min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Readout Mode 1'
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq1")+self.del_s1+self.del_m1, min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Readout Mode 1'
        )

        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode1/amp_729_sp"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='Readout Mode 1'
        )
        
        self.setattr_argument(
            "amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode1/amp_729_sp_aux"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='Readout Mode 1'
        )

    @kernel
    def prepare(self, use_motion_tracking=False):
        if use_motion_tracking:
            vib_freq=self.exp.seq.calibrate_motion.get_motional_freq_tracker(mode='mode1')
        else:
            vib_freq=self.parameter_manager.get_float_param("VdP2mode/vib_freq1")
        freq_729_sp=self.parameter_manager.get_float_param("frequency/729_sp")

        self.freq_729_sp=freq_729_sp-vib_freq+self.del_s1
        self.freq_729_sp_aux=freq_729_sp+vib_freq+self.del_s1

    @kernel
    def run(self, pulse_length, att_729_dp=-1.0):
        if att_729_dp >0:
            self.dds_729_dp.set_att(att_729_dp)
        else:
            self.dds_729_dp.set_att(self.att_729_dp)
        self.ttl_rf_switch_AWG_729SP.on()
        #turn on 
        self.ttl_awg_trigger.pulse(1*us)
        delay(2*us)
        if (pulse_length>10*ns):
            self.dds_729_dp.sw.on()
            delay(pulse_length)
            self.dds_729_dp.sw.off()

class SDF_mode2(Sequence):

    def __init__(self):
        super().__init__()

    def build(self):
        super().build()

        # Readout mode 2
        self.del_m2=self.parameter_manager.get_param("SDF/mode2/delta_m") 
        self.del_s2=self.parameter_manager.get_param("SDF/mode2/delta_s") 

        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode2/att_729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group='Readout Mode 2'
        )

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-self.parameter_manager.get_param("VdP2mode/vib_freq2")+self.del_s2-self.del_m2, min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Readout Mode 2'
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq2")+self.del_s2+self.del_m2, min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Readout Mode 2'
        )

        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode2/amp_729_sp"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='Readout Mode 2'
        )
        
        self.setattr_argument(
            "amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode2/amp_729_sp_aux"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='Readout Mode 2'
        )

    @kernel
    def prepare(self, use_motion_tracking=False):
        if use_motion_tracking:
            vib_freq=self.exp.seq.calibrate_motion.get_motional_freq_tracker(mode='mode2')
        else:
            vib_freq=self.parameter_manager.get_float_param("VdP2mode/vib_freq2")
        freq_729_sp=self.parameter_manager.get_float_param("frequency/729_sp")

        self.freq_729_sp=freq_729_sp-vib_freq+self.del_s2
        self.freq_729_sp_aux=freq_729_sp+vib_freq+self.del_s2

    @kernel
    def run(self, pulse_length, att_729_dp=-1.0):
        if att_729_dp >0:
            self.dds_729_dp.set_att(att_729_dp)
        else:
            self.dds_729_dp.set_att(self.att_729_dp)
        self.ttl_rf_switch_AWG_729SP.on()

        #turn on 
        self.ttl_awg_trigger.pulse(1*us)
        delay(2*us)
        if (pulse_length>10*ns):
            self.dds_729_dp.sw.on()
            delay(pulse_length)
            self.dds_729_dp.sw.off()