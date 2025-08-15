
from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms

import numpy as np
class LineTrigger(Sequence):

    def __init__(self):
        super().__init__()

    @kernel
    def run(self, core, time_gating_mu, time_holdoff_mu):
        return self.wait_trigger(core, time_gating_mu, time_holdoff_mu)

    @kernel(flags={"fast-math"})
    def wait_trigger(self, core, time_gating_mu, time_holdoff_mu):
        """
        Trigger off a rising edge of the AC line.
        Times out if no edges are detected.
        Arguments:
            time_gating_mu  (int)   : the maximum waiting time (in machine units) for the trigger signal.
            time_holdoff_mu (int64) : the holdoff time (in machine units)
        Returns:
                            (int64) : the input time of the trigger signal.
        """ 

        gate_open_mu = now_mu() #current time on the timeline (int kernel)
                                #self.core.get_rtio_counter_mu (hardware time cursor)
        self.ttl_linetrigger_input._set_sensitivity(1)
    
        t_trig_mu = 0
        while True:
            t_trig_mu = self.ttl_linetrigger_input.timestamp_mu(gate_open_mu + time_gating_mu)
            if t_trig_mu < 0 or t_trig_mu >= gate_open_mu:
                break
        
        #self.trigger.count(self.core.get_rtio_counter_mu() + time_holdoff_mu) #drain the FIFO to avoid input overflow

        # Provide extra slack for subsequent SPI/Urukul transactions
        at_mu(core.get_rtio_counter_mu()+200000)

        self.ttl_linetrigger_input._set_sensitivity(0)

        # Increase additional offset to ensure following DDS configs are safely in the future
        at_mu(core.get_rtio_counter_mu() + time_holdoff_mu + 200000) # set current time relative to hardware timeline with ample margin

        # if t_trig_mu < 0:
        #     raise Exception("MissingTrigger")

        return t_trig_mu


class AWGTrigger(Sequence):

    def __init__(self):
        super().__init__()

    @kernel
    def run(self, core, time_gating_mu, time_holdoff_mu):
        return self.wait_trigger(core, time_gating_mu, time_holdoff_mu)

    @kernel(flags={"fast-math"})
    def wait_trigger(self, core, time_gating_mu, time_holdoff_mu):
        """
        Trigger off a rising edge of the AC line.
        Times out if no edges are detected.
        Arguments:
            time_gating_mu  (int)   : the maximum waiting time (in machine units) for the trigger signal.
            time_holdoff_mu (int64) : the holdoff time (in machine units)
        Returns:
                            (int64) : the input time of the trigger signal.
        """ 
        time_gating_mu = core.seconds_to_mu(5000*ms)
        time_holdoff_mu = core.seconds_to_mu(50*us)

        gate_open_mu = now_mu() #current time on the timeline (int kernel)
                                #self.core.get_rtio_counter_mu (hardware time cursor)
        self.ttl_awg_ready._set_sensitivity(1)
    
        t_trig_mu = 0
        while True:
            t_trig_mu = self.ttl_awg_ready.timestamp_mu(gate_open_mu + time_gating_mu)
            if t_trig_mu < 0 or t_trig_mu >= gate_open_mu:
                break
        
        #self.trigger.count(self.core.get_rtio_counter_mu() + time_holdoff_mu) #drain the FIFO to avoid input overflow

        at_mu(core.get_rtio_counter_mu()+20000)

        self.ttl_awg_ready._set_sensitivity(0)

        at_mu(core.get_rtio_counter_mu() + time_holdoff_mu +200) #set the current time (software) to be the same as the current hardware timeline + a shift in time

        # if t_trig_mu < 0:
        #     raise Exception("MissingTrigger")

        return t_trig_mu
