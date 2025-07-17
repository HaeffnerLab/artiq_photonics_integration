from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from artiq.experiment import *
import time
import serial
from acf.utils import get_config_dir
import os
import subprocess

class Ion_Dump(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        self.seq.ion_store.add_arguments_to_gui()

        
    @kernel
    def run(self):
        self.setup_run()
        self.core.break_realtime()

        self.seq.ion_store.run()

        self.seq.rf.set_voltage('dump')

        time.sleep(2)

        self.core.break_realtime()

        self.seq.rf.set_voltage('store')

        



                