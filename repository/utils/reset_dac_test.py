from artiq.experiment import *
from artiq.language.core import  kernel, TerminationRequested

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class ResetDACTest(EnvExperiment):       

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")

        self.channels = [i for i in range(32)]
        self.voltages = [0.1] * 32


    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.zotino0.init()
        delay(10*ms)
        self.zotino0.set_dac(self.voltages, self.channels)
