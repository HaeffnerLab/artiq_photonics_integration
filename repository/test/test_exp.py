from artiq.experiment import *

class TestExp(EnvExperiment):

    def build(self):
        print(self.get_dataset_metadata("abc"))
