from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz

from utils_func.stark_D import stark_shift

class VdP(Sequence):

    def __init__(self):
        super().__init__()

         
    def build(self):
        super().build()

        #VdP Hamiltonian (2nd red sideband + 1st blue sideband) ######################################################################
        # self.setattr_argument(
        #     "Vdp_freq_729_dp",
        #     NumberValue(default=self.exp.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=0*MHz, max=250*MHz, unit="MHz", precision=8),
        #     tooltip="729 double pass frequency for resonance",
        #     group= self.group_name
        # )      


        self.setattr_argument(
            "Vdp_att_729_dp",
            NumberValue(default=10*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )

        self.setattr_argument(
            "Vdp_freq_729_vib",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP1mode/vib_freq"), min=0*MHz, max=50*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )      

        self.setattr_argument(
            "Vdp_freq_729_BSB_sp_delta",
            NumberValue(default=-stark_shift(self.exp.parameter_manager, 
                                            self.exp.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), 
                                            self.exp.parameter_manager.get_param("frequency/729_sp")-self.exp.parameter_manager.get_param("VdP1mode/vib_freq"),
                                            self.exp.parameter_manager.get_param("VdP1mode/Rabi_Freq_BSB"))
                        , min=-50*MHz, max=50*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )   

        self.setattr_argument(
            "Vdp_freq_729_2RSB_sp_delta",
            NumberValue(default=-stark_shift(self.exp.parameter_manager, 
                                            self.exp.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), 
                                            self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP1mode/vib_freq")*2,
                                            self.exp.parameter_manager.get_param("VdP1mode/Rabi_Freq_2RSB"))
                        , min=-50*MHz, max=50*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )   

        self.setattr_argument(
            "Vdp_drive_time_2RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP1mode/Vdp_drive_time_2RSB"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB VdP Hamiltonian",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_time_BSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP1mode/Vdp_drive_time_BSB"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for BSB VdP Hamiltonian",
            group= self.group_name
        )

        self.setattr_argument(
            "Vdp_drive_att_2RSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP1mode/att_2RSB_sp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_att_BSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP1mode/att_BSB_sp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group= self.group_name
        )


        self.setattr_argument(
            "Vdp_drive_freq_854",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/854_dp"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_freq_866",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/866_cooling"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )

        self.setattr_argument(
            "Vdp_drive_att_854",
            NumberValue(default=16*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_att_866",
            NumberValue(default=self.exp.parameter_manager.get_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group= self.group_name
        )

        self.setattr_argument(
            "Repeat_Time",
            NumberValue(default=200, min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group= self.group_name
        )

        #stark shift corrected frequency
        self.Vdp_freq_729_BSB_sp=self.exp.parameter_manager.get_param("frequency/729_sp")-self.exp.parameter_manager.get_param("VdP1mode/vib_freq")#+self.Vdp_freq_729_BSB_sp_delta
        self.Vdp_freq_729_2RSB_sp=self.exp.parameter_manager.get_param("frequency/729_sp")+2*self.exp.parameter_manager.get_param("VdP1mode/vib_freq")#+self.Vdp_freq_729_2RSB_sp_delta

    
    @kernel
    def repump(self):
        delay(2*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(5*us)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()


    @kernel
    def run(self):
        
        #stark shift corrected frequency
        Vdp_freq_729_BSB_sp=self.Vdp_freq_729_BSB_sp+self.Vdp_freq_729_BSB_sp_delta
        Vdp_freq_729_2RSB_sp=self.Vdp_freq_729_2RSB_sp+self.Vdp_freq_729_2RSB_sp_delta
        

        #loss in the upper spin state
        self.dds_854_dp.set(self.Vdp_drive_freq_854)
        self.dds_866_dp.set(self.Vdp_drive_freq_866)
        self.dds_854_dp.set_att(self.Vdp_drive_att_854)
        self.dds_866_dp.set_att(self.Vdp_drive_att_866)


        # self.dds_729_dp.set(self.Vdp_freq_729_dp)
        self.dds_729_dp.set_att(self.Vdp_att_729_dp)
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.on() # keep single pass on 
        self.dds_729_sp_aux.sw.off()

        delay(2*us)

        for i in range(self.Repeat_Time):
            #generate random phase

            # 2 order red sideband
            self.dds_729_sp.set(Vdp_freq_729_2RSB_sp, phase=0.)
            self.dds_729_sp.set_att(self.Vdp_drive_att_2RSB_sp)
            
            self.dds_729_dp.sw.on()
            delay(self.Vdp_drive_time_2RSB)
            self.dds_729_dp.sw.off()

            self.repump()
            #self.exp.seq.op_pump_sigma.run()

            # 1 order blue sideband
            self.dds_729_sp.set(Vdp_freq_729_BSB_sp, phase=0.)
            self.dds_729_sp.set_att(self.Vdp_drive_att_BSB_sp)

            self.dds_729_dp.sw.on()
            delay(self.Vdp_drive_time_BSB)
            self.dds_729_dp.sw.off()
    
            self.repump()
            self.exp.seq.op_pump_sigma.run()
        
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        delay(2*us)



