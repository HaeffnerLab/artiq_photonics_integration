from artiq.experiment import *                                             
from artiq.coredevice.ad9910 import (RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_RAMPUP, PHASE_MODE_TRACKING , PHASE_MODE_ABSOLUTE)

class simple_two_dds_phase(EnvExperiment):
    def build(self): 
        self.setattr_device("core")                               
        self.dds1 = self.get_device("urukul1_ch3")
        self.dds2 = self.get_device("urukul2_ch3")
        self.dds3 = self.get_device("urukul1_ch0")

    @kernel
    def run(self):
        self.core.break_realtime()
        self.core.reset()

        self.dds1.init()
        self.dds2.init()
        self.dds3.init()
        self.dds1.cpld.init()
        self.dds2.cpld.init()
        self.dds3.cpld.init()

        self.dds1.set_phase_mode(PHASE_MODE_TRACKING)
        self.dds2.set_phase_mode(PHASE_MODE_TRACKING)
        self.dds3.set_phase_mode(PHASE_MODE_TRACKING)

        self.dds1.sw.off()
        self.dds2.sw.off()
        self.dds3.sw.off()

        at_mu(now_mu() & ~7)
        start_time_mu = now_mu()

        delay(2*s)
        
        #with parallel:
        self.dds1.set(200*MHz,phase=0.0,ref_time_mu=start_time_mu)
        self.dds2.set(200*MHz,phase=0.,ref_time_mu=start_time_mu)
        self.dds3.set(200*MHz,phase=0.,ref_time_mu=start_time_mu)


        self.dds1.set_att(5*dB)
        self.dds1.sw.on()
        self.dds2.set_att(5*dB)
        self.dds2.sw.on()
        self.dds3.set_att(5*dB)
        self.dds3.sw.on()


        while True:
            pass             
'''
    # @kernel
    # def run(self):
    #     self.core.break_realtime()
    #     self.core.reset()

    #     self.dds1.init()
    #     self.dds2.init()
    #     self.dds3.init()
    #     self.dds1.cpld.init()
    #     self.dds2.cpld.init()
    #     self.dds3.cpld.init()

    #     self.dds1.set_phase_mode(PHASE_MODE_ABSOLUTE)
    #     self.dds2.set_phase_mode(PHASE_MODE_ABSOLUTE)
    #     self.dds3.set_phase_mode(PHASE_MODE_ABSOLUTE)

    #     self.dds1.sw.off()
    #     self.dds2.sw.off()
    #     self.dds3.sw.off()

    #     delay(1*s)

    #     with parallel:
    #         self.dds1.set(200*MHz,phase=0.0)
    #         self.dds2.set(200*MHz,phase=0.)
    #         self.dds3.set(200*MHz,phase=0.)


    #     self.dds1.set_att(5*dB)
    #     self.dds1.sw.on()
    #     self.dds2.set_att(5*dB)
    #     self.dds2.sw.on()
    #     self.dds3.set_att(5*dB)
    #     self.dds3.sw.on()


    #     while True:
    #         pass             


    #sync urukuls https://github.com/m-labs/artiq/issues/1143
    @kernel
    def run(self):
        self.core.break_realtime()
        self.dds1.cpld.init()
        self.dds1.init()
        self.dds2.init()
        self.dds3.init()

        # This calibration needs to be done only once to find good values.
        # The rest is happening at each future init() of the DDS.
        if 1:#self.dds1.sync_delay_seed == -1:
            delay(100*us)

            self.dds1.tune_io_update_delay()
            #self.dds1.tune_sync_delay()
            self.dds2.tune_io_update_delay()
            #self.dds2.tune_sync_delay()
            self.dds3.tune_io_update_delay()
            #self.dds3.tune_sync_delay()
            # d0, w0 = self.dds1. tune_io_update_delay
            # t0 = self.dds1.tune_io_update_delay()
            # d1, w1 = self.dds2.tune_sync_delay()
            # t1 = self.dds1.tune_io_update_delay()
            # d2, w2 = self.dds3.tune_sync_delay()
            # t2 = self.dds1.tune_io_update_delay()
            # Add the values found to each of the four channels in your
            # device_db.py so that e.g. for urukul0_ch0 it looks like:
            #    "urukul0_ch0": {
            #       ...
            #        "class": "AD9910",
            #        "arguments": {
            #            "pll_n": 32,
            #            "chip_select": 4,
            #           "sync_delay_seed": D,
            #           "io_update_delay": T,
            #           "cpld_device": "urukul0_cpld",
            #           ...
            #       }
            # where T is the io_update_delay of the channel and
            # D is the sync_delay_seed of the channel below:
            # print("sync_delay_seed", [d0, d1, d2])
            # print("io_update_delay", [t0, t1, t2])
            # As long as the values don't differ too much between the channels,
            # using the mean for them is also fine.
            # This one is for information purposes only:
            # print("validation delays", [w0, w1, w2, w3])
            #
            # then run this script again
            return

        self.dds1.set_phase_mode(PHASE_MODE_TRACKING)
        self.dds2.set_phase_mode(PHASE_MODE_TRACKING)
        self.dds3.set_phase_mode(PHASE_MODE_TRACKING)
       

        self.dds1.set_att(10*dB)
        self.dds2.set_att(10*dB)
        self.dds3.set_att(10*dB)

        t = now_mu()
        self.dds1.set(80*MHz, phase=0., ref_time_mu=t)
        self.dds2.set(80*MHz, phase=.5, ref_time_mu=t)
        self.dds3.set(80*MHz, phase=.25, ref_time_mu=t)

        
        self.dds1.sw.on()
        self.dds2.sw.on()
        self.dds3.sw.on()
'''