from artiq.experiment import *                
from artiq.coredevice.core import *

class TTL_Input_As_Trigger(EnvExperiment):
    """TTL Input Edge as Trigger"""
    def build(self): #Adds the device drivers as attributes and adds the keys to the kernel invarients     

        self.setattr_device("core")             #sets drivers of core device as attributes
        self.setattr_device("ttl1")             #input the line trigger signal
        self.setattr_device("ttl12")             #sets drivers of TTL6 as attributes

        self.trigger=self.ttl1
        self.ttl_out=self.ttl12

        
    @kernel #this code runs on the FPGA
    def run(self):                              
        self.core.reset()                       #resets core device
        

        self.ttl1.input()                       #sets TTL0 as an input
        self.ttl_out.output()                      #sets TTL6 as an output

        self.core.break_realtime()

        self.ttl_out.off()
     
        while True:
            
            flag = self.wait_trigger(self.core.seconds_to_mu(5*ms), 0 )
            delay(10*us) # the delay here is very important

            if flag>0:
                self.ttl_out.pulse(500*us)
    

    @kernel(flags={"fast-math"})
    def wait_trigger(self, time_gating_mu, time_holdoff_mu):
        """
        Trigger off a rising edge of the AC line.
        Times out if no edges are detected.
        Arguments:
            time_gating_mu  (int)   : the maximum waiting time (in machine units) for the trigger signal.
            time_holdoff_mu (int64) : the holdoff time (in machine units)
        Returns:
                            (int64) : the input time of the trigger signal.
        """

        ttl_end=self.trigger.gate_rising_mu(time_gating_mu)
        # wait for line trigger input
        time_trigger_mu = self.trigger.timestamp_mu(ttl_end)

        # ensure input timestamp is valid
        if time_trigger_mu > 0:
            # set rtio hardware time to input trigger time
            at_mu(time_trigger_mu + time_holdoff_mu)
            return time_trigger_mu

        # reset RTIO if we don't get receive trigger signal for some reason
        else:
            # add slack before resetting system
            self.core.break_realtime()
            self.trigger._set_sensitivity(0)
            self.core.reset()

        self.trigger.count(ttl_end)

        # return -1 if we time out
        return -1


    
    # @kernel
    # def wait_for_trigger(self, delay_time):
    #     self.core.wait_until_mu(now_mu())
    #     t_edge = -1
    #     while t_edge<0:
    #         at_mu(rtio_get_counter() + delay_time) # rtio_get_counter() imported from artiq.coredevice.core
    #         gate_end_mu = self.trigger.gate_rising(1*ms) # TTLInOut
    #         t_edge = self.trigger.timestamp_mu(gate_end_mu)
    #         delay(10*us)
    #         self.core.wait_until_mu(now_mu())
    #     at_mu(t_edge)
    #     delay(1.2*ms)


    # @kernel
    # def wait_for_trigger(self):
    #     gate_open_mu = now_mu()
    #     self.trigger._set_sensitivity(1)

    #     # Loop until any old left-over events (before current gate open) are
    #     # consumed, or the specified timeout has elapsed.
    #     t_trig_mu = 0
    #     while True:
    #         t_trig_mu = self.trigger.timestamp_mu(gate_open_mu + self.max_wait_mu)
    #         if t_trig_mu < 0 or t_trig_mu >= gate_open_mu:
    #             break

    #     at_mu(self.core.get_rtio_counter_mu() + self.slack_mu)
    #     self.trigger._set_sensitivity(0)

    #     if t_trig_mu < 0:
    #         raise MissingTrigger
    #     return t_trig_mu