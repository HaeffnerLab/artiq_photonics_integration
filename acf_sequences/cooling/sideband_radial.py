from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, ms, NumberValue, MHz, EnumerationValue

import numpy as np

class SideBandCool_Radial(Sequence):
    def __init__(self):
        super().__init__()


        self.add_argument_from_parameter("sideband_freq_729_sp", "frequency/729_sp")
        self.add_argument_from_parameter("sideband_att_729_sp", "attenuation/729_radial_sp")
        self.add_argument_from_parameter("SideBandCool_729_dp_sideband", "qubit/Sm1_2_Dm5_2")


        self.add_argument_from_parameter("sideband_vib_freq1", "sideband_Radial/vib_freq0_1")
        self.add_argument_from_parameter("sideband_vib_freq2", "sideband_Radial/vib_freq0_2")

        self.add_parameter("frequency/866_cooling")
        self.add_parameter("frequency/854_dp")

        self.add_argument_from_parameter("sideband_att_729", "sideband_Radial/att_729")
        self.add_argument_from_parameter("sideband_att_854", "sideband_Radial/att_854")
        self.add_argument_from_parameter("sideband_att_866", "sideband_Radial/att_866")


        self.add_argument("SideBandCool_num_cycle", NumberValue(default=30, min=0, max=600, precision=0, step=1))
        self.add_argument("SideBandCool_Cooling_Type", EnumerationValue(["cw", "pulse"], default="cw"))

        #729 optical pumping
        self.add_argument_from_parameter("Op_pump_freq_729_dp", "qubit/S1_2_Dm3_2")
        self.add_argument_from_parameter("Op_pump_att_729_dp", "optical_pumping/att_729_dp")
        self.add_argument_from_parameter("Op_pump_freq_729_sp", "frequency/729_sp")
        self.add_argument_from_parameter("Op_pump_att_729_sp", "optical_pumping/att_729_sp")
        self.add_argument_from_parameter("Op_pump_att_729", "optical_pumping/att_729_dp")

        self.add_argument_from_parameter("Op_pump_att_854", "attenuation/854_dp")
        self.add_argument_from_parameter("Op_pump_att_866", "attenuation/866")

        #sigma minus 397 light 
        self.add_argument("optical_pumping", EnumerationValue(["397_op", "729_op"], default="397_op"))
        self.add_parameter("optical_pumping/pump_time_sigma")
        self.add_parameter("optical_pumping/att_397_sigma")
        self.add_argument_from_parameter("optical_pumping_freq_397_sigma", "frequency/397_resonance")
        self.add_parameter("frequency/397_resonance")
      

    @kernel
    def run(self, 
           # freq_offset=-0.1*MHz, 
            att_854_here=-1.0*dB, 
            att_729_here=-1.0*dB, 
            att_866_here=-1.0*dB, 
            freq_diff_dp=0.0*MHz):      
        if self.SideBandCool_Cooling_Type == "cw":

            #mainly for outside scan
            if (att_854_here/dB)>0.0:
                self.sideband_att_854=att_854_here
            if (att_729_here/dB)>0.0:
                self.sideband_att_729=att_729_here
            if (att_866_here/dB)>0.0:
                self.sideband_att_866=att_866_here
            
            self.SideBandCoolingCW(self.SideBandCool_729_dp_sideband+freq_diff_dp, self.Op_pump_freq_729_dp+freq_diff_dp*7.0/5.0)#,  self.sideband_vib_freq)

        else:
            #mainly for outside scan
            if (att_854_here/dB)>0.0:
                self.sideband_att_854=att_854_here
            if (att_729_here/dB)>0.0:
                self.sideband_att_729=att_729_here
            if (att_866_here/dB)>0.0:
                self.sideband_att_866=att_866_here
            
            self.SideBandCooling_Pulse(self.SideBandCool_729_dp_sideband+freq_diff_dp, self.Op_pump_freq_729_dp+freq_diff_dp*7.0/5.0)#,  self.sideband_vib_freq)


        delay(5*us)


    @kernel
    def OP_Sigma(self):
        self.dds_397_sigma.set(self.optical_pumping_freq_397_sigma)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
       
        self.dds_397_sigma.sw.on()
        delay(self.optical_pumping_pump_time_sigma)
        self.dds_397_sigma.sw.off()

    @kernel
    def SideBandCoolingCW(
        self, 
        sbc_freq, 
        op_freq#,
        #freq_offset # Half motional freq
        ):

        att_729 = self.sideband_att_729
        att_866 = self.sideband_att_866
        att_854 = self.sideband_att_854


        #set laser power & frequency
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)

        self.dds_854_dp.set_att(att_854)
        self.dds_866_dp.set_att(att_866)

        self.dds_729_radial_dp.set(op_freq)
        self.dds_729_radial_dp.set_att(att_729)

        self.dds_729_radial_sp.set_att(self.sideband_att_729_sp)
        self.dds_729_radial_sp.set(self.sideband_freq_729_sp)

        self.dds_397_sigma.set(self.frequency_397_resonance)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
        

        delay(5*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_729_radial_dp.sw.on()
        self.dds_729_radial_sp.cfg_sw(True)
        self.dds_397_sigma.sw.off()
        delay(5*us)

        for i in range(self.SideBandCool_num_cycle):

            if self.optical_pumping=="397_op": # and i < self.SideBandCool_num_cycle/5*4:
                
                self.dds_729_radial_dp.sw.off()
                delay(5*us)
                self.OP_Sigma()
                self.dds_729_radial_dp.sw.on()

            else:

                ##GS pumping
                self.dds_729_radial_dp.set(op_freq)
                self.dds_729_radial_dp.set_att(self.Op_pump_att_729_dp)
                self.dds_729_radial_sp.set_att(self.Op_pump_att_729_sp)
                self.dds_729_radial_sp.set(self.Op_pump_freq_729_sp)
                self.dds_854_dp.set_att(att_854)
                self.dds_866_dp.set_att(att_866)
                delay(300*us)

            
            self.dds_854_dp.set_att(att_854)
            self.dds_866_dp.set_att(att_866)

            self.dds_729_radial_dp.set_att(att_729)


            # if i < self.SideBandCool_num_cycle/4:
            #     #continous red sideband cooling 
            #     self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq1)
            #     delay(200*us)

            #     self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq2)
            #     delay(200*us)
            # else:
            
            
            #continous red sideband cooling 
            self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq1)
            delay(200*us)

            self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq2)
            delay(200*us)
       

        delay(2*us)
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(False)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(2*us)
        
        #upper state clean up
        self.dds_729_dp.set(op_freq)
        self.dds_729_dp.set_att(self.Op_pump_att_729_dp)
        self.dds_729_sp.set_att(self.Op_pump_att_729_sp)
        self.dds_729_sp.set(self.Op_pump_freq_729_sp)

        self.OP_Sigma()

        for i in range(5):
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()

            self.dds_854_dp.set_att(self.Op_pump_att_854)
            self.dds_866_dp.set_att(self.Op_pump_att_866)
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



    @kernel
    def repump(self):
        
        self.dds_854_dp.set_att(15*dB)
        self.dds_866_dp.sw.on()
        self.dds_854_dp.sw.on()
        delay(10.0*us)
        self.dds_866_dp.sw.off()
        self.dds_854_dp.sw.off()

    @kernel
    def SideBandCooling_Pulse(
        self, 
        sbc_freq, 
        op_freq
        ):

        att_729 = self.sideband_att_729
        att_866 = self.sideband_att_866
        att_854 = self.sideband_att_854


        #set laser power & frequency
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)

        self.dds_854_dp.set_att(att_854)
        self.dds_866_dp.set_att(att_866)

        self.dds_729_radial_dp.set(op_freq)
        self.dds_729_radial_dp.set_att(att_729)

        self.dds_729_radial_sp.set_att(self.sideband_att_729_sp)
        self.dds_729_radial_sp.set(self.sideband_freq_729_sp)

        self.dds_397_sigma.set(self.frequency_397_resonance)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
        

        delay(5*us)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(True)
        self.dds_397_sigma.sw.off()

        pulse_length_max=40.0*us
        pulse_length_min = 40.0*us

        for i in range(self.SideBandCool_num_cycle):

            if self.optical_pumping=="397_op":
                self.dds_866_dp.sw.on()
                self.OP_Sigma()
                self.dds_866_dp.sw.off()
            else:

                ##GS pumping
                self.dds_729_radial_dp.set(op_freq)
                self.dds_729_radial_dp.set_att(self.Op_pump_att_729_dp)
                self.dds_729_radial_sp.set_att(self.Op_pump_att_729_sp)
                self.dds_729_radial_sp.set(self.Op_pump_freq_729_sp)
                self.dds_854_dp.set_att(att_854)
                self.dds_866_dp.set_att(att_866)
                delay(300*us)

            
            self.dds_729_radial_dp.set_att(att_729)




            for j in range(5):
                #continous red sideband cooling 
                self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq1)
                self.dds_729_radial_dp.sw.on()
                delay(pulse_length_min+(pulse_length_max-pulse_length_min)*i/self.SideBandCool_num_cycle)
                self.dds_729_radial_dp.sw.off()

                self.repump()

                #continous red sideband cooling 
                self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq2)
                self.dds_729_radial_dp.sw.on()
                delay(pulse_length_min+(pulse_length_max-pulse_length_min)*i/self.SideBandCool_num_cycle)
                self.dds_729_radial_dp.sw.off()

                self.repump()


        for j in range(10):
            #continous red sideband cooling 
            self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq1)
            self.dds_729_radial_dp.sw.on()
            delay(150*us)
            self.dds_729_radial_dp.sw.off()

            self.repump()

                #continous red sideband cooling 
            self.dds_729_radial_dp.set(sbc_freq+0.5*self.sideband_vib_freq2)
            self.dds_729_radial_dp.sw.on()
            delay(200*us)
            self.dds_729_radial_dp.sw.off()

            self.repump()

        delay(2*us)
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(False)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(2*us)
        
        #upper state clean up
        self.dds_729_dp.set(op_freq)
        self.dds_729_dp.set_att(self.Op_pump_att_729_dp)
        self.dds_729_sp.set_att(self.Op_pump_att_729_sp)
        self.dds_729_sp.set(self.Op_pump_freq_729_sp)

        self.OP_Sigma()

        for i in range(5):

            # ground state optical pumping

            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()

            self.dds_854_dp.set_att(self.Op_pump_att_854)
            self.dds_866_dp.set_att(self.Op_pump_att_866)
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
