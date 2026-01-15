from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class SetDDS729(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("attenuation/729_dp")


    @kernel
    def run(self):

        self.core.break_realtime()

        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_dp.set(self.frequency_729_dp)

        self.dds_729_dp.sw.on()
        

        while True:
            pass
