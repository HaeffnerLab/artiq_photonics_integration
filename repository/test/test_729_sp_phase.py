from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *
from artiq.coredevice.ad9910 import (RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_RAMPUP, PHASE_MODE_TRACKING , PHASE_MODE_ABSOLUTE)

class Test729Sp(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        self.setattr_argument(
            "phase",
            NumberValue(default=0.0, min=0.0, max=30, precision=8)
        )
    
    @kernel
    def run(self):

        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()


        while True:
            pass
