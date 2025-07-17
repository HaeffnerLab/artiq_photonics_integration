from artiq.experiment import *
from artiq.coredevice.ad9910 import (
        RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP,
        RAM_MODE_CONT_RAMPUP, RAM_MODE_RAMPUP, PHASE_MODE_ABSOLUTE,
        PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING, RAM_MODE_CONT_BIDIR_RAMP
    )
import numpy as np

class SineRamp(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.dds = self.get_device("urukul0_ch1")
        self.dds_cpld= self.get_device("urukul0_cpld")
        #self.dds = self.get_device("urukul2_ch0")
        #self.ttl = self.get_device("blue_PIs")

        n = 400
        self.dataf = [np.sin((np.pi / 2)* (i / (n-1))) for i in range(n)]

    @kernel
    def run(self):
        
        self.krun()

    @kernel
    def krun(self):
        dataf = self.dataf
        data = [0] * len(dataf)
        self.dds.amplitude_to_ram(dataf, data)

        self.core.reset()
        self.dds_cpld.init()
        self.dds.cpld.init()
        self.dds.init()
        self.dds.set_cfr1(ram_enable=0)
        self.dds.cpld.set_profile(0)
        self.dds.cpld.io_update.pulse_mu(8)
        delay(1*ms)
        self.dds.set_profile_ram(
                                start=0,
                                end=len(data) - 1,
                                step=1,
                                profile=0,
                                mode=RAM_MODE_CONT_BIDIR_RAMP,
                                # nodwell_high=1
                            )
        self.dds.cpld.set_profile(0)
        self.dds.cpld.io_update.pulse_mu(8)
        self.dds.write_ram(data)
        delay(300*ms)
        self.dds.set_cfr1(
                    ram_enable=1,
                    ram_destination=RAM_DEST_ASF,
                    phase_autoclear=1,
                    #internal_profile=0,
                )
        self.dds.cpld.io_update.pulse_mu(8)
        self.dds.set_frequency(125*MHz)
        self.dds.set_att(10*dB)
        self.dds.sw.on()
        delay(30*ms)
        self.core.break_realtime()
        while True:
            delay(1*ms)
            with parallel:
                self.dds.sw.on()
                #self.ttl.on()
                self.dds.cpld.io_update.pulse_mu(8)
            delay(10*us)
            #self.ttl.off()
            self.dds.sw.off()