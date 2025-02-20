from acf.sequence import Sequence
from artiq.experiment import kernel

class PrintHi(Sequence):

    @kernel
    def run(self):
        self.sequence()

    @kernel
    def sequence(self):
        print("hi hi hi!")
