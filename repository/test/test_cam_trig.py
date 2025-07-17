from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class Cam_Trig(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        self.setattr_device("grabber0")
    
    @kernel
    def run(self):

        self.core.reset()

        self.core.break_realtime()

        size=8

        self.grabber0.setup_roi(0, 0, 0,  size, size)
        self.grabber0.setup_roi(1, 0, 11, size, 11+size)

        self.grabber0.gate_roi(7)
        n=[0]*2#1 ROI

        self.ttl_camera_trigger.pulse(10*us)

        self.grabber0.input_mu(n)

        #self.core.break_realtime()
        delay(5*ms)

        self.grabber0.gate_roi(0)
        
        print("ROI sums:", n)

        
