from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, EnumerationValue

import numpy as np

class SideBandCool2Mode(Sequence):
    def __init__(self):
        super().__init__()

        ### cool two modes simultaneously (double pass full power)
        self.add_argument_from_parameter("sideband2mode_freq_729_dp", "qubit/Sm1_2_Dm5_2")
        self.add_parameter("sideband2mode/att_729_dp")
        self.add_parameter("sideband2mode/vib_freq1")
        self.add_parameter("sideband2mode/vib_freq2")


        ### sideband cooling
        self.add_parameter("sideband2mode/att_854")
        self.add_parameter("sideband2mode/att_866")

        self.add_argument("SideBandCool_num_cycle", NumberValue(default=20, min=0, max=1000, precision=0, step=1))
        self.add_argument("SideBandCool_Cooling_Type", EnumerationValue(["cw", "pulse"], default="cw"))

        #sigma minus 397 light 
        self.add_argument("optical_pumping", EnumerationValue(["397_op", "729_op"], default="397_op"))
        self.add_parameter("optical_pumping/pump_time_sigma")
        self.add_parameter("optical_pumping/att_397_sigma")
        self.add_argument_from_parameter("optical_pumping_freq_397_sigma", "frequency/397_resonance")


        #optical pumping
        self.add_argument_from_parameter("optical_pumping_freq_729_dp", "qubit/S1_2_Dm3_2") 
        self.add_argument_from_parameter("optical_pumping_att_729_dp", "attenuation/729_dp")
        self.add_argument_from_parameter("optical_pumping_freq_866", "frequency/866_cooling")
        self.add_argument_from_parameter("optical_pumping_att_866", "attenuation/866")
        self.add_argument_from_parameter("optical_pumping_freq_854", "frequency/854_dp")
        self.add_argument_from_parameter("optical_pumping_att_854", "attenuation/854_dp")
    

      

    @kernel
    def run(self, 
            att_854_here=-1.0*dB, 
            att_729_here=-1.0*dB, 
            att_866_here=-1.0*dB,
            # sideband2mode_freq_729_dp_here=-1.0*MHz,
            # optical_pumping_freq_729_dp_here=-1.0*MHz
            freq_diff_dp=0.0*MHz
            ):

        
        if self.SideBandCool_Cooling_Type == "cw":

            #mainly for outside scan
            if (att_854_here/dB)>0.0:
                self.sideband2mode_att_854=att_854_here
            if (att_729_here/dB)>0.0:
                self.sideband2mode_att_729_dp=att_729_here
            if (att_866_here/dB)>0.0:
                self.sideband2mode_att_866=att_866_here

            self.sideband2mode_freq_729_dp+=freq_diff_dp
            self.optical_pumping_freq_729_dp+=freq_diff_dp/5.0*7.0

            self.SideBandCoolingCW2mode()

            self.sideband2mode_freq_729_dp-=freq_diff_dp
            self.optical_pumping_freq_729_dp-=freq_diff_dp/5.0*7.0
          
        delay(5*us)

    @kernel 
    def set_OP(self):
        self.dds_729_dp.set(self.optical_pumping_freq_729_dp)
        self.dds_729_dp.set_att(self.optical_pumping_att_729_dp)
        
        self.dds_854_dp.set_att(self.optical_pumping_att_854)
        self.dds_866_dp.set_att(self.optical_pumping_att_866)
        self.dds_866_dp.set(self.optical_pumping_freq_866)
        self.dds_854_dp.set(self.optical_pumping_freq_854)

    @kernel
    def OP_Sigma(self):
        self.dds_397_sigma.set(self.optical_pumping_freq_397_sigma)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
       
        self.dds_397_sigma.sw.on()
        delay(self.optical_pumping_pump_time_sigma)
        self.dds_397_sigma.sw.off()
    
    @kernel
    def repump_854(self):
        self.dds_854_dp.set_att(16*dB)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(5*us)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off() 

    @kernel
    def SideBandCoolingPulse2mode(self):

        #switch to artiq sp_aux
        self.ttl_rf_switch_DDS_729SP.on()
        self.ttl_rf_switch_AWG_729SP.off()

        ##############################################################################################################################
        #set laser power & frequency
        self.set_OP()
        self.dds_397_far_detuned.sw.off()
        self.dds_397_dp.sw.off()

        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(2*us)
        ##############################################################################################################################       
        self.dds_729_dp.set(self.sideband2mode_freq_729_dp)
        self.dds_729_dp.set_att(15*dB)

        for i in range(int(self.SideBandCool_num_cycle/5)):
            ########################################################################################################################### 
            for j in range(5):
                self.dds_729_dp.sw.on()
                delay(21*us)
                self.dds_729_dp.sw.off()
                self.repump_854()
                
                self.dds_729_dp.sw.on()
                delay(20*us)
                self.dds_729_dp.sw.off()

                self.repump_854() 


                self.dds_729_dp.sw.on()
                delay(21*us)
                self.dds_729_dp.sw.off()

                self.repump_854()

            self.OP_Sigma()

        ##############################################################################################################################       
        self.dds_729_dp.set(self.sideband2mode_freq_729_dp)
        self.dds_729_dp.set_att(25*dB)
        for i in range(self.SideBandCool_num_cycle):
            ########################################################################################################################### 
            for j in range(5):
                self.dds_729_dp.sw.on()
                delay(20*us)
                self.dds_729_dp.sw.off()


                self.repump_854()

                self.dds_729_dp.sw.on()
                delay(30*us)
                self.dds_729_dp.sw.off()

                self.repump_854()


                self.dds_729_dp.sw.on()
                delay(20*us)
                self.dds_729_dp.sw.off()


                self.repump_854()
            self.OP_Sigma()


        # #upper state clean up
        self.set_OP()

        for i in range(5):

            # ground state optical pumping
            self.dds_729_dp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()

            self.repump_854()
        
        delay(5*us)
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()


        self.ttl_rf_switch_DDS_729SP.off()
        self.ttl_rf_switch_AWG_729SP.on()
   

    @kernel
    def SideBandCoolingCW2mode(self):

        #switch to artiq sp_aux
        # self.ttl_rf_switch_DDS_729SP.on()
        # self.ttl_rf_switch_AWG_729SP.off()

        ##############################################################################################################################
        #set laser power & frequency
        self.set_OP()

        delay(5*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_729_dp.sw.on()
        ##############################################################################################################################       
        for i in range(self.SideBandCool_num_cycle):
            
            ########################################################################################################################### 
            if self.optical_pumping=="397_op": #and i < self.SideBandCool_num_cycle/5*4:
                self.dds_729_dp.sw.off()
                self.OP_Sigma()
                self.dds_729_dp.sw.on()

            else:

                ##GS pumping
                self.set_OP()
                delay(300*us)

            ###########################################################################################################################
            self.dds_854_dp.set_att(self.sideband2mode_att_854-1.0*dB)
            self.dds_866_dp.set_att(self.sideband2mode_att_866)
            self.dds_729_dp.set(self.sideband2mode_freq_729_dp)

            self.dds_729_dp.set_att(self.sideband2mode_att_729_dp-1.0*dB) 

            
            self.dds_729_dp.set_att(self.sideband2mode_att_729_dp)
            self.dds_854_dp.set_att(self.sideband2mode_att_854)


        #################################


        #GS pumping

        #upper state clean up
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(3*us)
        self.set_OP()
        delay(3*us)
        self.OP_Sigma()
        delay(3*us)

        for i in range(5):

            # ground state optical pumping
            self.dds_729_dp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()

            self.dds_854_dp.sw.on()
            self.dds_866_dp.sw.on()
            delay(10*us)
            self.dds_854_dp.sw.off()
            self.dds_866_dp.sw.off()
        
        delay(2*us)
        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()

        #################################
        

        # self.dds_397_sigma.set(self.optical_pumping_freq_397_sigma)
        # self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
        # self.dds_729_dp.sw.off()
        # self.dds_397_sigma.sw.on()
        # delay(self.optical_pumping_pump_time_sigma)
        # self.dds_397_sigma.sw.off()
        # self.dds_729_dp.sw.on()

        # self.dds_729_dp.sw.off()
        # self.dds_854_dp.sw.off()
        # self.dds_866_dp.sw.off()
        #################################

        # self.ttl_rf_switch_DDS_729SP.off()
        # self.ttl_rf_switch_AWG_729SP.on()

