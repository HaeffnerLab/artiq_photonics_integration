from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *
from awg_utils.transmitter import send_exp_para
class Awg_Trig(_ACFExperiment):
    def build(self):
        self.setup(sequences)
    
    @rpc
    def send_exp_para(self):
        send_exp_para(["test_phase", {}]) 

    @kernel
    def run(self):

        self.core.reset()

        self.core.break_realtime()

        self.seq.ion_store.run()

        self.send_exp_para()
        delay(20*ms)

        

        # self.ttl_awg_trigger.pulse(1*us)
        # delay(50*us)

        # self.ttl_awg_trigger.pulse(1*us)
        # delay(50*us)


        # self.ttl_awg_trigger.pulse(1*us)
        # delay(50*us)


        