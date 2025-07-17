from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class TestAOM(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_sp")

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )


        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )

    @kernel
    def run(self):

        # set attenuation
        self.core.break_realtime()

        self.dds_729_dp.set_att(self.att_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)

        # set frequency and phase
        self.dds_729_dp.set(self.freq_729_dp)
        self.dds_729_sp.set(self.frequency_729_sp)

        # turn devices on
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()
        

        while True:
            pass
