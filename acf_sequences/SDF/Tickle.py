from acf.sequence import Sequence
from artiq.experiment import *

class Tickle(Sequence):

    def __init__(self):
        super().__init__()

    def build(self):
        super().build()


    @kernel
    def run(self, pulse_length):

        self.ttl_awg_trigger.pulse(1*us)
        delay(pulse_length)
        self.ttl_awg_trigger.pulse(1*us)
        delay(2*us)