from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class Test_ADC(_ACFExperiment):
    def build(self):
        self.setup(sequences)
    
    @kernel
    def run(self):

        self.core.reset()

        self.dac.init()
        self.core.break_realtime()

        self.dac.write_dac(0, 0.0)
        self.dac.load()
        
