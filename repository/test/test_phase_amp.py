from artiq.experiment import *
from artiq.coredevice.ad9910 import (
        RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_DEST_FTW, RAM_DEST_POWASF,
        RAM_MODE_CONT_RAMPUP, RAM_MODE_RAMPUP, PHASE_MODE_ABSOLUTE,
        PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING, RAM_MODE_CONT_BIDIR_RAMP
    )
import numpy as np

class RAMAmpPhaseExample(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.dds = self.get_device("urukul2_ch3")
        self.dds_cpld= self.get_device("urukul2_cpld")
    
    def prepare(self):

        n = 400
        max_ = 1.
        min_ = 0.

     
        self.data_amp = [i%2 * 0.5 + 0.5 for i in range(n)] #0.5, 1.0 0.5, 1.0
        self.data_phase = [0.5 * i%2 for i in range(n)]     #0.0, 0.5, 1.0, 1.5, 0.0, 0.5, 1.0, 1.5,

        for i, val in enumerate(self.data_amp):
            if val > max_:
                self.data_amp[i] = max_
            elif val < min_:
                self.data_amp[i] = min_

        self.data = [0] * len(self.data_amp)
        self.dds.turns_amplitude_to_ram(self.data_phase, self.data_amp, self.data)
        for i in range(len(self.data)):
            self.data[i]=np.int32(self.data[i])
        #self.data = int(self.data)


    @kernel
    def run(self):
        
        self.krun()

    @kernel
    def krun(self):
        data = self.data

        pulse_mu=8

        self.core.reset()
        self.dds.cpld.init()
        self.dds.init()
        self.dds.set_cfr1(ram_enable=0)#This is the correct mode for loading or reading values
        self.dds.cpld.set_profile(0)
        self.dds.cpld.io_update.pulse_mu(pulse_mu) #this sends an 8 machine unit long pulse of TTL signal internally to trigger the updated ram_enable value

        self.dds.set_profile_ram(
                                start=0,
                                end=len(data) - 1,
                                step=200, #this controls how long one point last (step*t_DDS[4ns] )
                                profile=0,
                                mode=RAM_MODE_CONT_RAMPUP,
                                # nodwell_high=1
                            )
        

        self.dds.cpld.set_profile(0)
        self.dds.cpld.io_update.pulse_mu(pulse_mu)#another ttl pulse to apply the previous updates
        self.dds.write_ram(data)

        self.core.break_realtime()

        self.dds.set_cfr1(
                    ram_enable=1,
                    ram_destination=RAM_DEST_POWASF, #ASF: amplitude scale factor / POW: phase offset word
                    phase_autoclear=1,
                    internal_profile=0,
                )
        self.dds.cpld.io_update.pulse_mu(pulse_mu)
        self.dds.set_frequency(20*MHz) #50ns period (1 ram point ~ 8 periods=400ns)
        self.dds.set_att(10*dB)
        self.dds.sw.on()

        self.core.break_realtime()
        while True:
            delay(1*ms)
            with parallel:
                self.dds.sw.on()
                self.dds.cpld.io_update.pulse_mu(pulse_mu)
            delay(400*us)
            self.dds.sw.off()