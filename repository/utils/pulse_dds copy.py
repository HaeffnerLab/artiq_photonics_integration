from artiq.experiment import *
from artiq.language.core import  kernel, TerminationRequested

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class PulseDDS2(EnvExperiment):       

    def build(self):
        self.setattr_device("core")
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul0_ch1")      


    @kernel
    def run(self):
        self.core.reset()
        # self.urukul0_cpld.init()
        
        # self.urukul0_ch1.cpld.init()
        # self.urukul0_ch1.init()
        delay(100*us)

        delay(100*us)
        self.urukul0_ch1.set(frequency = 89 * MHz, amplitude = 0.5)
        # self.urukul0_ch1.set(90 * MHz)
        self.urukul0_ch1.set_att(10* dB)

        self.urukul0_ch1.sw.on()
        



