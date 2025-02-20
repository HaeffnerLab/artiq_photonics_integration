from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms

from utils_func.stark_D import stark_shift_kernel

class VdP1mode(Sequence):

    def __init__(self):
        super().__init__()
    

    @kernel
    def prepare(self, vib_mode="mode1"):
        qubit_Sm1_2_Dm5_2=self.exp.parameter_manager.get_float_param("qubit/Sm1_2_Dm5_2")
        qubit_Sm1_2_Dm1_2=self.exp.parameter_manager.get_float_param("qubit/Sm1_2_Dm1_2")
        qubit_Sm1_2_D3_2=self.exp.parameter_manager.get_float_param("qubit/Sm1_2_D3_2")
        freq_sp=self.exp.parameter_manager.get_float_param("frequency/729_sp")
        
        if vib_mode=="mode1":
            self.Vdp_freq_729_vib=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq1")
            self.Vdp_freq_729_BSB_sp_delta=-stark_shift_kernel(
                qubit_Sm1_2_Dm5_2,
                qubit_Sm1_2_Dm1_2,
                qubit_Sm1_2_D3_2,
                qubit_Sm1_2_Dm5_2,
                freq_sp-self.Vdp_freq_729_vib,
                self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode1_BSB")
            )
            self.Vdp_freq_729_2RSB_sp_delta=-stark_shift_kernel(
                qubit_Sm1_2_Dm5_2,
                qubit_Sm1_2_Dm1_2,
                qubit_Sm1_2_D3_2,
                qubit_Sm1_2_Dm5_2,
                freq_sp+self.Vdp_freq_729_vib*2,
                self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode1_2RSB")
            )
            self.Vdp_drive_time_2RSB=self.exp.parameter_manager.get_float_param("VdP2mode/2RSB_time_729_mode1")
            self.Vdp_drive_time_BSB=self.exp.parameter_manager.get_float_param("VdP2mode/BSB_time_729_mode1")

            self.Vdp_drive_att_2RSB_sp=self.exp.parameter_manager.get_float_param("VdP2mode/att_729_mode1_2RSB")
            self.Vdp_drive_att_BSB_sp=self.exp.parameter_manager.get_float_param("VdP2mode/att_729_mode1_BSB")
            #stark shift corrected frequency
            self.Vdp_freq_729_BSB_sp=freq_sp-self.Vdp_freq_729_vib#+self.Vdp_freq_729_BSB_sp_delta
            self.Vdp_freq_729_2RSB_sp=freq_sp+self.exp.parameter_manager.get_float_param("VdP2mode/freq_2RSB_mode1")

        elif vib_mode=="mode2":
            self.Vdp_freq_729_vib=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq2")
            
            self.Vdp_freq_729_BSB_sp_delta=-stark_shift_kernel(
                qubit_Sm1_2_Dm5_2,
                qubit_Sm1_2_Dm1_2,
                qubit_Sm1_2_D3_2,
                qubit_Sm1_2_Dm5_2,
                freq_sp-self.Vdp_freq_729_vib,
                self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode2_BSB")
            )
            self.Vdp_freq_729_2RSB_sp_delta=-stark_shift_kernel(
                qubit_Sm1_2_Dm5_2,
                qubit_Sm1_2_Dm1_2,
                qubit_Sm1_2_D3_2,
                qubit_Sm1_2_Dm5_2,
                freq_sp+self.Vdp_freq_729_vib*2,
                self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode2_2RSB")
            )

            self.Vdp_drive_time_2RSB=self.exp.parameter_manager.get_float_param("VdP2mode/2RSB_time_729_mode2")
            self.Vdp_drive_time_BSB=self.exp.parameter_manager.get_float_param("VdP2mode/BSB_time_729_mode2")

            self.Vdp_drive_att_2RSB_sp=self.exp.parameter_manager.get_float_param("VdP2mode/att_729_mode2_2RSB")
            self.Vdp_drive_att_BSB_sp=self.exp.parameter_manager.get_float_param("VdP2mode/att_729_mode2_BSB")
            #stark shift corrected frequency
            self.Vdp_freq_729_BSB_sp=freq_sp-self.Vdp_freq_729_vib#+self.Vdp_freq_729_BSB_sp_delta
            self.Vdp_freq_729_2RSB_sp=freq_sp+self.exp.parameter_manager.get_float_param("VdP2mode/freq_2RSB_mode2")
        else:
            self.Vdp_freq_729_vib=self.exp.parameter_manager.get_float_param("VdP1mode/vib_freq")

            self.Vdp_freq_729_BSB_sp_delta= -stark_shift_kernel(
                qubit_Sm1_2_Dm5_2,
                qubit_Sm1_2_Dm1_2,
                qubit_Sm1_2_D3_2,
                qubit_Sm1_2_Dm5_2,
                freq_sp-self.Vdp_freq_729_vib,
                self.exp.parameter_manager.get_float_param("VdP1mode/Rabi_Freq_BSB")
            )
            self.Vdp_freq_729_2RSB_sp_delta=-stark_shift_kernel(
                qubit_Sm1_2_Dm5_2,
                qubit_Sm1_2_Dm1_2,
                qubit_Sm1_2_D3_2,
                qubit_Sm1_2_Dm5_2,
                freq_sp+self.Vdp_freq_729_vib*2,
                self.exp.parameter_manager.get_float_param("VdP1mode/Rabi_Freq_2RSB")
            )

            self.Vdp_drive_time_2RSB=self.exp.parameter_manager.get_float_param("VdP1mode/Vdp_drive_time_2RSB")
            self.Vdp_drive_time_BSB=self.exp.parameter_manager.get_float_param("VdP1mode/Vdp_drive_time_BSB")

            self.Vdp_drive_att_2RSB_sp=self.exp.parameter_manager.get_float_param("VdP1mode/att_2RSB_sp")
            self.Vdp_drive_att_BSB_sp=self.exp.parameter_manager.get_float_param("VdP1mode/att_BSB_sp")
            #stark shift corrected frequency
            self.Vdp_freq_729_BSB_sp=freq_sp-self.Vdp_freq_729_vib#+self.Vdp_freq_729_BSB_sp_delta
            self.Vdp_freq_729_2RSB_sp=freq_sp+2*self.Vdp_freq_729_vib#+self.Vdp_freq_729_2RSB_sp_delta
         
    def build(self):
        super().build()
        self.setattr_argument(
            "Vdp_att_729_dp",
            NumberValue(default=10*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_freq_854",
            NumberValue(default=self.exp.parameter_manager.get_float_param("frequency/854_dp"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_freq_866",
            NumberValue(default=self.exp.parameter_manager.get_float_param("frequency/866_cooling"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group= self.group_name
        )

        self.setattr_argument(
            "Vdp_drive_att_854",
            NumberValue(default=12*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_drive_att_866",
            NumberValue(default=self.exp.parameter_manager.get_float_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group= self.group_name
        )

        self.setattr_argument(
            "Repeat_Time",
            NumberValue(default=self.exp.parameter_manager.get_param('VdP2mode/Repeat_time'), min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group= self.group_name
        )

        self.Vdp_freq_729_vib=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq1")
        self.Vdp_freq_729_BSB_sp_delta=0.0*MHz
        self.Vdp_freq_729_2RSB_sp_delta=0.0*MHz
        self.Vdp_drive_time_2RSB=self.exp.parameter_manager.get_float_param("VdP2mode/2RSB_time_729_mode1")
        self.Vdp_drive_time_BSB=self.exp.parameter_manager.get_float_param("VdP2mode/BSB_time_729_mode1")

        self.Vdp_drive_att_2RSB_sp=self.exp.parameter_manager.get_float_param("VdP2mode/att_729_mode1_2RSB")
        self.Vdp_drive_att_BSB_sp=self.exp.parameter_manager.get_float_param("VdP2mode/att_729_mode1_BSB")
        #stark shift corrected frequency
        self.Vdp_freq_729_BSB_sp=self.exp.parameter_manager.get_float_param("frequency/729_sp")-self.Vdp_freq_729_vib#+self.Vdp_freq_729_BSB_sp_delta
        self.Vdp_freq_729_2RSB_sp=self.exp.parameter_manager.get_float_param("frequency/729_sp")+2*self.Vdp_freq_729_vib#+self.Vdp_freq_729_2RSB_sp_delta

    
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
        Vdp_freq_729_2RSB_sp=self.Vdp_freq_729_2RSB_sp#+self.Vdp_freq_729_2RSB_sp_delta

        

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



