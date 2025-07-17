from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, ms, NumberValue, MHz, EnumerationValue

import numpy as np

class SideBandCool(Sequence):
    def __init__(self):
        super().__init__()

        #self.add_argument_from_parameter("sideband_729_dp_offset", "qubit/vib_freq")

        self.add_argument_from_parameter("sideband_freq_729_sp", "frequency/729_sp")
        self.add_argument_from_parameter("sideband_att_729_sp", "attenuation/729_sp")

        self.add_argument_from_parameter("SideBandCool_729_dp_sideband", "qubit/Sm1_2_Dm5_2")

        self.add_parameter("frequency/866_cooling")
        self.add_parameter("frequency/854_dp")

        self.add_parameter("sideband/vib_freq")

        self.add_parameter("sideband/att_729")
        self.add_parameter("sideband/att_854")
        self.add_parameter("sideband/att_866")

        self.add_argument("SideBandCool_num_cycle", NumberValue(default=20, min=0, max=60, precision=0, step=1))
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
            freq_offset=-0.1*MHz, 
            att_854_here=-1.0*dB, 
            att_729_here=-1.0*dB, 
            att_866_here=-1.0*dB, 
            att_397_sigma_here=-1.0*dB,
            freq_diff_dp=0.0*MHz):      
        if self.SideBandCool_Cooling_Type == "cw":

            #mainly for outside scan
            if (att_854_here/dB)>0.0:
                self.sideband_att_854=att_854_here
            if (freq_offset/MHz)>0.0:
                self.sideband_vib_freq=freq_offset
            if (att_729_here/dB)>0.0:
                self.sideband_att_729=att_729_here
            if (att_866_here/dB)>0.0:
                self.sideband_att_866=att_866_here
            if (att_397_sigma_here/dB)>0.0:
                self.optical_pumping_att_397_sigma=att_397_sigma_here
            
            self.SideBandCoolingCW(self.SideBandCool_729_dp_sideband+freq_diff_dp, self.Op_pump_freq_729_dp+freq_diff_dp*7.0/5.0,  self.sideband_vib_freq)

        else:
            pass
            #self.SideBandCooling(self.SideBandCool_729_dp_sideband, self.sideband_freq_729_red_detune, self.SideBandCool_729_dp_opt,self.SideBandCool_num_cycle)
        delay(5*us)
        # 729 dp optical pumping : S(-1/2) --> D(3/2)
        # 729 dp offset : the sideband frequency difference
    '''
    @kernel
    def SideBandCooling(
        self, 
        sbc_freq, 
        freq_offset, # Half motional freq
        op_freq, 
        Op_cycle):

        #the pulse time should be around the pi time

        att_freq_729 = 15*dB
       
        self.dds_729_dp.set(op_freq)
        self.dds_729_dp.set_att(att_freq_729)
        self.dds_854_dp.set_att(15*dB)
        
        #state prep S 1/2,1/2->D 5/2,-3/2 + repump
        for OP_num in range(Op_cycle):
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(5*us)
            self.dds_729_dp.sw.off()
            self.dds_854_dp.sw.on()
            self.dds_866_dp.sw.on()
            delay(4*us)
            self.dds_854_dp.sw.off()
            self.dds_866_dp.sw.off()

        for Iterate in range(5):
            
            # 2nd red sideband
            self.dds_729_dp.set((sbc_freq+2*freq_offset))  # drive sideband cooling
            self.dds_729_dp.set_att(15*dB)
            for GSC in range(Op_cycle):
               
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(4*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()
            
            # OP on resonant
            self.dds_729_dp.set(op_freq)
            self.dds_729_dp.set_att(att_freq_729)

            for OP_num in range(Op_cycle):
        
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(5*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(4*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()    

        for Iterate in range(25):
            
            #red sideband
            self.dds_729_dp.set((sbc_freq+freq_offset))  # drive sideband cooling
            self.dds_729_dp.set_att(att_freq_729)
            for GSC in range(Op_cycle):
               
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(4*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()
            
            # OP on resonant
            self.dds_729_dp.set(op_freq)
            self.dds_729_dp.set_att(att_freq_729)

            for OP_num in range(Op_cycle):
        
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(4*us)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()

        self.dds_729_dp.set(op_freq)
        self.dds_729_dp.set_att(att_freq_729)
        for OP_num in range(Op_cycle):
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(5*us)
            self.dds_729_dp.sw.off()
            self.dds_854_dp.sw.on()
            self.dds_866_dp.sw.on()
            delay(4*us)
            self.dds_854_dp.sw.off()
            self.dds_866_dp.sw.off()


    # a newer version to test 
    @kernel
    def SideBandCooling2(
        self, 
        sbc_freq, 
        freq_offset, # Half motional freq
        op_freq, 
        Op_cycle):

        att_freq_729 = 15*dB
       
        self.dds_729_dp.set(op_freq)
        self.dds_729_dp.set_att(att_freq_729)
        self.dds_854_dp.set_att(15*dB)

        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        
        #state prep S 1/2,1/2->D 5/2,-3/2 + repump
        for OP_num in range(Op_cycle):
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(5*us)
            self.dds_729_dp.sw.off()
            delay(4*us)

        for Iterate in range(5):
            
            # 2nd red sideband
            self.dds_729_dp.set((sbc_freq+2*freq_offset))  # drive sideband cooling
            self.dds_729_dp.set_att(12*dB)
            for GSC in range(Op_cycle):
               
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                delay(4*us)
            
            # OP on resonant
            self.dds_729_dp.set(op_freq)
            self.dds_729_dp.set_att(att_freq_729)

            for OP_num in range(Op_cycle):
        
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                delay(4*us)

        for Iterate in range(20):
            
            #red sideband
            self.dds_729_dp.set((sbc_freq+freq_offset))  # drive sideband cooling
            self.dds_729_dp.set_att(att_freq_729)
            for GSC in range(Op_cycle):
               
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(40*us)
                self.dds_729_dp.sw.off()
                delay(4*us)
            
            # OP on resonant
            self.dds_729_dp.set(op_freq)
            self.dds_729_dp.set_att(att_freq_729)

            for OP_num in range(Op_cycle):
        
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                delay(10*us)
                self.dds_729_dp.sw.off()
                delay(4*us)

        #optical pumping
        self.dds_729_dp.set(op_freq)
        self.dds_729_dp.set_att(att_freq_729)
        for OP_num in range(Op_cycle):
            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()
            delay(4*us)
        

        self.dds_729_dp.sw.off()
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()

'''

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
        op_freq,
        freq_offset # Half motional freq
        ):

        # print("continuous cooling WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWww", sbc_freq+freq_offset*0.5)
        # self.core.break_realtime()

        att_729 = self.sideband_att_729
        att_866 = self.sideband_att_866
        att_854 = self.sideband_att_854
        

        #set laser power & frequency
        self.dds_729_dp.set(op_freq)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)

        self.dds_729_dp.set_att(att_729)
        self.dds_854_dp.set_att(att_854)
        self.dds_866_dp.set_att(att_866)

        self.dds_729_sp.set_att(self.sideband_att_729_sp)
        self.dds_729_sp.set(self.sideband_freq_729_sp)

        self.dds_397_sigma.set(self.frequency_397_resonance)
        self.dds_397_sigma.set_att(self.optical_pumping_att_397_sigma)
        

        delay(5*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()
        self.dds_397_sigma.sw.off()
        self.ttl_rf_switch_AWG_729SP.off()
        delay(5*us)

        for i in range(self.SideBandCool_num_cycle):

            if self.optical_pumping=="397_op": # and i < self.SideBandCool_num_cycle/5*4:
                
                self.dds_729_dp.sw.off()
                delay(1.0*us)
                self.OP_Sigma()
                self.dds_729_dp.sw.on()

            else:

                ##GS pumping
                self.dds_729_dp.set(op_freq)
                self.dds_729_dp.set_att(self.Op_pump_att_729_dp)
                self.dds_729_sp.set_att(self.Op_pump_att_729_sp)
                self.dds_729_sp.set(self.Op_pump_freq_729_sp)
                self.dds_854_dp.set_att(att_854)
                self.dds_866_dp.set_att(att_866)
                delay(300*us)

            
            self.dds_854_dp.set_att(att_854)
            self.dds_866_dp.set_att(att_866)
            self.dds_729_dp.set_att(att_729)
            #continous 2nd red sideband cooling 
            if i < self.SideBandCool_num_cycle/5:
                self.dds_729_dp.set(sbc_freq+freq_offset)
                delay(200*us)
            else:
                #continous red sideband cooling 
                self.dds_729_dp.set(sbc_freq+0.5*freq_offset)
                delay(200*us)
        


        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_397_sigma.sw.off()

        # for i in range(10):
        #     #self.dds_729_dp.set(sbc_freq+freq_offset*0.5)
        #     self.dds_729_dp.set(243.033*MHz)
        #     self.dds_729_dp.set_att(20.0*dB)
        #     self.dds_729_sp.set_att(13.0*dB)
        #     self.dds_729_dp.sw.on()
        #     self.dds_729_sp.sw.on()
        #     delay(60*us)
        #     self.dds_729_dp.sw.off()

        #     self.dds_854_dp.sw.on()
        #     self.dds_866_dp.sw.on()
        #     delay(15*us)
        #     self.dds_866_dp.sw.off()
        #     self.dds_854_dp.sw.off()

  

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



        # delay(5*us)
        # self.dds_729_dp.set(242.76*MHz)
        # self.dds_729_dp.set_att(20.0*dB)
        # self.dds_729_sp.set_att(13.0*dB)
        # self.dds_729_dp.sw.on()
        # self.dds_729_sp.sw.on()
        # delay(7.98*us)
        # self.dds_729_dp.sw.off()
        # self.dds_729_sp.sw.off()

        # self.dds_729_dp.set(231.785*MHz)
        # self.dds_729_dp.set_att(20.0*dB)
        # self.dds_729_sp.set_att(13.0*dB)
        # self.dds_729_dp.sw.on()
        # self.dds_729_sp.sw.on()
        # delay(20*us)
        # self.dds_729_dp.sw.off()
        # self.dds_729_sp.sw.off()

        # delay(5*us)
        # self.dds_729_dp.set(242.76*MHz)
        # self.dds_729_dp.set_att(20.0*dB)
        # self.dds_729_sp.set_att(13.0*dB)
        # self.dds_729_dp.sw.on()
        # self.dds_729_sp.sw.on()
        # delay(7.98*us)
        # self.dds_729_dp.sw.off()
        # self.dds_729_sp.sw.off()
