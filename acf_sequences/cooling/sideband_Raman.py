from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, ms, NumberValue, MHz, EnumerationValue

import numpy as np

class SideBandCool_Raman(Sequence):
    def __init__(self):
        super().__init__()

        #repump
        self.add_parameter("frequency/866_cooling")
        self.add_parameter("frequency/854_dp")

        self.add_argument_from_parameter("sideband_att_854", "sideband_Raman/att_854")
        self.add_argument_from_parameter("sideband_att_866", "sideband_Raman/att_866")


        #cycle times
        self.add_argument("SideBandCool_num_cycle", NumberValue(default=10, min=0, max=60, precision=0, step=1))
        self.add_argument("SideBandCool_Cooling_Type", EnumerationValue(["cw"], default="cw"))

        #Raman SBC
        self.add_parameter("frequency/Raman1")
        self.add_parameter("frequency/Raman2")
        self.add_parameter("attenuation/Raman1")
        self.add_parameter("attenuation/Raman2")
        self.add_parameter("sideband_Raman/vib_freq1")
        self.add_parameter("sideband_Raman/vib_freq2")
        self.add_parameter("sideband_Raman/amp_Raman")

        #729 optical pumping
        self.add_argument_from_parameter("Op_pump_freq_729_dp", "qubit/S1_2_Dm3_2")
        self.add_argument_from_parameter("Op_pump_att_729_dp", "sideband_Raman/att_729_dp")
        self.add_argument_from_parameter("Op_pump_freq_729_sp", "frequency/729_sp")
        self.add_argument_from_parameter("Op_pump_att_729_sp", "optical_pumping/att_729_sp")

        #sigma minus 397 light 
        self.add_argument("optical_pumping", EnumerationValue(["397_op", "729_op"], default="729_op"))
        self.add_parameter("optical_pumping/pump_time_sigma")
        self.add_argument_from_parameter("optical_pumping_att_397_sigma", "sideband_Raman/att_397_sigma")
        self.add_argument_from_parameter("optical_pumping_freq_397_sigma", "frequency/397_resonance")
        self.add_parameter("frequency/397_resonance")
      

    @kernel
    def run(self, 
            freq_vib1=-1.0*MHz,
            att_397_sigma_here=-1.0*dB,
            amp_Ramam_here=-1.0, 
            att_729_dp_here=-1.0*dB,
            att_854_here=-1.0*dB, 
            att_866_here=-1.0*dB):      
        if self.SideBandCool_Cooling_Type == "cw":

            #mainly for outside scan
            if (att_854_here/dB)>0.0:
                self.sideband_att_854=att_854_here
            if (att_866_here/dB)>0.0:
                self.sideband_att_866=att_866_here
            if (att_729_dp_here/dB)>0.0:
                self.Op_pump_att_729_dp=att_729_dp_here

            if (att_397_sigma_here>0.0):
                self.optical_pumping_att_397_sigma=att_397_sigma_here
            
            if amp_Ramam_here>0.0:
                self.sideband_Raman_amp_Raman=amp_Ramam_here
            
            if freq_vib1>0.0:
                self.sideband_Raman_vib_freq1=freq_vib1
            
            self.SideBandCoolingCW(self.Op_pump_freq_729_dp)



    @kernel
    def OP_Sigma(self):
        self.dds_397_sigma.set(self.optical_pumping_freq_397_sigma, amplitude=1.)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
       
        self.dds_397_sigma.sw.on()
        delay(self.optical_pumping_pump_time_sigma)
        self.dds_397_sigma.sw.off()

    @kernel
    def SideBandCoolingCW(
        self, 
        op_freq
        ):

        att_866 = self.sideband_att_866
        att_854 = self.sideband_att_854
        
        

        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_397_sigma.sw.off()
        delay(2*us)

        #set laser power & frequency
        self.dds_729_dp.set(op_freq)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)
        self.dds_854_dp.set_att(att_854)
        self.dds_866_dp.set_att(att_866)
        delay(2*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        

        delay(5*us)

        for i in range(self.SideBandCool_num_cycle):


            if self.optical_pumping=="397_op" and i<int(3*self.SideBandCool_num_cycle/5) :
           
                self.dds_729_dp.sw.off()
                self.dds_729_sp.sw.off()
                self.dds_397_sigma.set(self.optical_pumping_freq_397_sigma, amplitude=1.0)
                self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
                self.dds_397_sigma.sw.on()
                delay(1*us)
            else:
                self.dds_397_sigma.sw.off()
                self.dds_729_dp.set(op_freq)
                self.dds_729_dp.set_att(self.Op_pump_att_729_dp)
                self.dds_729_sp.set_att(self.Op_pump_att_729_sp)
                self.dds_729_sp.set(self.Op_pump_freq_729_sp)
                delay(1*us)
                self.dds_854_dp.set_att(att_854)
                self.dds_866_dp.set_att(att_866)
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(1*us)

            
            self.dds_Raman_1.set_att(self.attenuation_Raman1)
            self.dds_Raman_2.set(self.frequency_Raman2, amplitude=self.sideband_Raman_amp_Raman)
            self.dds_Raman_2.set_att(self.attenuation_Raman2)
            delay(2*us)

            delay_time=400*us

            #mode1
            if i<int(1*self.SideBandCool_num_cycle/5):
                self.dds_Raman_1.set(self.frequency_Raman1-self.sideband_Raman_vib_freq1*4, amplitude=self.sideband_Raman_amp_Raman)
                
            elif i<int(3*self.SideBandCool_num_cycle/5):
                self.dds_Raman_1.set(self.frequency_Raman1-self.sideband_Raman_vib_freq1*2, amplitude=self.sideband_Raman_amp_Raman)
               
            else:
                self.dds_Raman_1.set(self.frequency_Raman1-self.sideband_Raman_vib_freq1*1, amplitude=self.sideband_Raman_amp_Raman)
              

            self.dds_Raman_1.sw.on()
            self.dds_Raman_2.sw.on()
            delay(delay_time)
            
            #mode2
            
            # if i<int(1*self.SideBandCool_num_cycle/5):
            #     self.dds_Raman_1.set(self.frequency_Raman1-self.sideband_Raman_vib_freq2*3, amplitude=self.sideband_Raman_amp_Raman)
                
            # elif i<int(3*self.SideBandCool_num_cycle/5):
            #     self.dds_Raman_1.set(self.frequency_Raman1-self.sideband_Raman_vib_freq2*2, amplitude=self.sideband_Raman_amp_Raman)
               
            # else:
            #     self.dds_Raman_1.set(self.frequency_Raman1-self.sideband_Raman_vib_freq2*1, amplitude=self.sideband_Raman_amp_Raman)
              

            # self.dds_Raman_1.sw.on()
            # self.dds_Raman_2.sw.on()
            # delay(delay_time)

        
        self.dds_397_sigma.sw.off()
        self.dds_Raman_1.sw.off()
        self.dds_Raman_2.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()

        #upper state clean upd
        self.dds_854_dp.set_att(15*dB)
        self.dds_866_dp.set_att(15*dB)
        for i in range(10):

            # ground state optical pumping
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()
            self.dds_854_dp.sw.on()
            self.dds_866_dp.sw.on()
            delay(10*us)
            self.dds_854_dp.sw.off()
            self.dds_866_dp.sw.off()
        
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        
        delay(5*us)

            