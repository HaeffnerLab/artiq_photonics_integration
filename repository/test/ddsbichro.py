from artiq.experiment import *
from artiq.coredevice.ad9910 import (
        RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_DEST_FTW, RAM_DEST_POWASF,
        RAM_MODE_CONT_RAMPUP, RAM_MODE_RAMPUP, PHASE_MODE_ABSOLUTE,
        PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING, RAM_MODE_CONT_BIDIR_RAMP
    )
import numpy as np

class sp_bic(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("urukul0_ch1")
        self.setattr_device("urukul0_cpld")

        self.setattr_argument(
            "freq",
            NumberValue(default=20.0*MHz, unit="MHz", min=10*MHz, max=200*MHz),
            tooltip="Frequency"
        )


        self.setattr_argument(
            "Kappa",
            NumberValue(default=1, precision=6),
            tooltip="B/A. "
        )

        self.setattr_argument(
            "Phi",
            NumberValue(default=0, precision=6),
            tooltip="Phase difference of two tone (in unit of turns)"
        )

        self.setattr_argument(
            "N",
            NumberValue(default=400, max=800, precision=0, step=1),
            tooltip="Number of points in RAM"
        )      

        self.setattr_argument(
            "Scale",
            NumberValue(default=10, precision=0, step=1),
            tooltip="4ns * Scale is the time of a point's lasting time"
        )



    def prepare(self):

        self.dds = self.urukul0_ch1
        self.dds_cpld= self.urukul0_cpld

        self.dds.set_phase_mode(PHASE_MODE_CONTINUOUS)

        n = self.N

        self.delta=2*np.pi/self.N 

        self.Phi=self.Phi*2*np.pi #from turns to radius

        #self.Gamma=[ self.x+self.delta*i for i in range(n)]
        self.data_cos=[ (np.cos(self.delta*i)+self.Kappa*np.cos(self.delta*i+self.Phi)) for i in range(n)] # self.step * 4 ns
        self.data_sin=[ (-np.sin(self.delta*i)+self.Kappa*np.sin(self.delta*i+self.Phi)) for i in range(n)] # self.step * 4 ns

        self.data_amp=[ np.sqrt(np.abs(self.data_cos[i])**2+np.abs(self.data_sin[i])**2) for i in range(n)]

        self.Gamma=[ np.arctan(self.data_sin[i]/self.data_cos[i]) for i in range(n)]
        self.data_phase= [self.Gamma[i]/2/np.pi for i in range(n)]
         #from radius to turns

        
        max_amp=np.max(np.abs(self.data_amp))
        for i in range(len(self.data_amp)):
            self.data_amp[i]/=max_amp

            if self.data_cos[i]*np.cos(self.Gamma[i])<0:
                self.data_phase[i]+=0.5



        self.data = [np.int32(0)] * len(self.data_amp)
        self.dds.turns_amplitude_to_ram(self.data_phase, self.data_amp, self.data)
        for i in range(len(self.data)):
            self.data[i]=np.int32(self.data[i])

        print("The delta frequency is: ",250/self.N/self.Scale," MHz")
        print("The frequency difference between two side bands: ", 500/self.N/self.Scale, " MHz")


    @kernel
    def run(self):
        
        self.krun()
    
    @kernel
    def dds_init(self, dds):
        dds.cpld.init()
        dds.init()
    
    @kernel
    def set_dds_mode(self, ram_id=False):
        if ram_id is False: #not working
            self.dds.set_cfr1(
                    ram_enable=0,
                    #ram_destination=RAM_DEST_POWASF, #ASF: amplitude scale factor / POW: phase offset word
                    #phase_autoclear=1,
                    #internal_profile=0,
                )
            self.dds.cpld.set_profile(1)
            self.dds.cpld.io_update.pulse_mu(8)
        else:
            self.dds.set_cfr1(
                    ram_enable=1,
                    ram_destination=RAM_DEST_POWASF, #ASF: amplitude scale factor / POW: phase offset word
                    phase_autoclear=1,
                    internal_profile=0
                )
            self.dds.cpld.set_profile(0)
            self.dds.cpld.io_update.pulse_mu(8)
    
    @kernel
    def write_to_dds_ram(self, dds, data, time_scale):
        
        dds.set_cfr1(ram_enable=0)#This is the correct mode for loading or reading values
        dds.cpld.set_profile(0)
        dds.cpld.io_update.pulse_mu(8) #this sends an 8 machine unit long pulse of TTL signal internally to trigger the updated ram_enable value
        dds.set_profile_ram(
            start=0,
            end=len(data) - 1,
            step=time_scale, #this controls how long one point last (step*t_DDS[4ns] )
            profile=0,
            mode=RAM_MODE_CONT_RAMPUP,
            # nodwell_high=1
        )
        dds.cpld.set_profile(0)
        dds.cpld.io_update.pulse_mu(8)#another ttl pulse to apply the previous updates
        dds.write_ram(data)
        dds.cpld.io_update.pulse_mu(8)
        # self.dds.set_cfr1(
        #             ram_enable=1,
        #             ram_destination=RAM_DEST_POWASF, #ASF: amplitude scale factor / POW: phase offset word
        #             phase_autoclear=1,
        #             internal_profile=0,
        #         )
        # self.dds.cpld.io_update.pulse_mu(8)
    
    @kernel
    def turn_off_dds(self, dds):
        #dds.cfg_sw(False)

        dds.sw.off()
    @kernel
    def turn_on_dds(self, dds):
        #dds.cfg_sw(True)

        dds.sw.on()
        
    @kernel
    def krun(self):

        self.core.break_realtime()

        self.write_to_dds_ram(self.dds,self.data, self.Scale)
        delay(3*ms)
        self.dds.set_cfr1(
                    ram_enable=1,
                    ram_destination=RAM_DEST_POWASF, #ASF: amplitude scale factor / POW: phase offset word
                    phase_autoclear=1,
                    internal_profile=0,
                )
        self.dds.cpld.io_update.pulse_mu(8)
        delay(3*ms)

        self.dds.set_frequency(self.freq) #50ns period (1 ram point ~ 8 periods=400ns)
        self.dds.set_att(10*dB)
        self.dds.sw.on()

        # self.core.break_realtime()
        # self.core.reset()

        # self.write_to_dds_ram(self.dds,self.data, self.Scale)

        # #self.set_dds_mode(ram_id=0)
        
        # self.dds.set_frequency(self.freq) #50ns period (1 ram point ~ 8 periods=400ns)
        # self.dds.set_att(15*dB)
        # self.core.break_realtime()

        # self.set_dds_mode(ram_id=True)
        # self.dds.set(self.freq, profile=0)
        # self.turn_on_dds(self.dds)

        # while True:
        #     #self.dds.cpld.io_update.pulse_mu(8)
        #     self.turn_on_dds(self.dds)
        #     delay(0.2*ms)

#         while True:
#             self.set_dds_mode(ram_id=True)
#             self.dds.set(self.freq, profile=0)
#             self.turn_on_dds(self.dds)
#             delay(0.02*ms)

#             self.turn_off_dds(self.dds)
#             delay(0.02*ms)
        '''
            self.set_dds_mode(ram_id=False)
            self.dds.set(self.freq, profile=1)
            # self.dds.set_frequency(self.freq) #50ns period (1 ram point ~ 8 periods=400ns)
            # self.dds.set_att(10*dB)
            self.turn_on_dds(self.dds)
            delay(0.02*ms)

            self.turn_off_dds(self.dds)
            delay(0.02*ms)
'''
      
