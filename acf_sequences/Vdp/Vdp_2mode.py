from acf.sequence import Sequence
from artiq.experiment import *
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import stark_shift_kernel

class VdP2Mode(Sequence):

    def __init__(self):
        super().__init__()

         
    def build(self):
        super().build()

        #VdP Hamiltonian Mode 1 ######################################################################
        self.setattr_argument(
            "Vdp_mode1_freq_729_BSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP2mode/freq_BSB_mode1"), 
                        min=10*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Mode 1'
        )
        self.setattr_argument(
            "Vdp_mode1_freq_729_2RSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP2mode/freq_2RSB_mode1"), 
                        min=10*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Mode 1'
        )
        self.setattr_argument(
            "Vdp_mode1_drive_att_2RSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/att_729_mode1_2RSB"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian Mode 1'
        )
        self.setattr_argument(
            "Vdp_mode1_drive_att_BSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/att_729_mode1_BSB"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian Mode 1'
        )

        self.setattr_argument(
            "Vdp_mode1_drive_time_BSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/BSB_time_729_mode1"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for BSB VdP Hamiltonian",
            group='VdP Hamiltonian Mode 1'
        )
        self.setattr_argument(
            "Vdp_mode1_drive_time_2RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/2RSB_time_729_mode1"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB VdP Hamiltonian",
            group='VdP Hamiltonian Mode 1'
        )
        

        #VdP Hamiltonian Mode 2 ######################################################################
        self.setattr_argument(
            "Vdp_mode2_freq_729_BSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP2mode/freq_BSB_mode2"), 
                        min=10*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Mode 2'
        )
        self.setattr_argument(
            "Vdp_mode2_freq_729_2RSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP2mode/freq_2RSB_mode2"), 
                        min=10*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Mode 2'
        )
        self.setattr_argument(
            "Vdp_mode2_drive_att_2RSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/att_729_mode2_2RSB"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian Mode 2'
        )
        self.setattr_argument(
            "Vdp_mode2_drive_att_BSB_sp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/att_729_mode2_BSB"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian Mode 2'
        )

        self.setattr_argument(
            "Vdp_mode2_drive_time_BSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/BSB_time_729_mode2"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for BSB VdP Hamiltonian",
            group='VdP Hamiltonian Mode 2'
        )
        self.setattr_argument(
            "Vdp_mode2_drive_time_2RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/2RSB_time_729_mode2"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB VdP Hamiltonian",
            group='VdP Hamiltonian Mode 2'
        )


        ### Vdp sync part
        self.setattr_argument(
            "Sync_mode1_freq_729_RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP2mode/vib_freq1"), 
                        min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 single pass frequency",
            group='VdP Sync'
        )

        self.setattr_argument(
            "Sync_mode2_freq_729_RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/729_sp")+self.exp.parameter_manager.get_param("VdP2mode/vib_freq2"), 
                        min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 single pass frequency",
            group='VdP Sync'
        )

        self.setattr_argument(
            "Sync_mode1_amp_729_RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/amp_729_mode1_RSB"), min=0.0, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='VdP Sync'
        )
      
        self.setattr_argument(
            "Sync_mode2_amp_729_RSB",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/amp_729_mode2_RSB"), min=0.0, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='VdP Sync'
        )  

        self.setattr_argument(
            "Vdp_sync_phase_degree",
            NumberValue(default=0, min=-1000, max=1000, precision=6),
            tooltip="sync phase in degree",
            group='VdP Sync'
        )  

        ###Vdp Misc settings #####################################################################################################
        self.setattr_argument(
            "Vdp_att_729_dp",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/att_729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Misc'
        )
        self.setattr_argument(
            "Vdp_sync_time",
            NumberValue(default=self.exp.parameter_manager.get_param("VdP2mode/sync_time"), min=1.0*us, max=300*us, unit="us", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Misc'
        )
        ## repump part
        self.setattr_argument(
            "Vdp_drive_freq_854",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/854_dp"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Misc'
        )
        self.setattr_argument(
            "Vdp_drive_att_854",
            NumberValue(default=12*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
           group='VdP Hamiltonian Misc'
        )
        self.setattr_argument(
            "Vdp_drive_freq_866",
            NumberValue(default=self.exp.parameter_manager.get_param("frequency/866_cooling"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian Misc'
        )

        self.setattr_argument(
            "Vdp_drive_att_866",
            NumberValue(default=self.exp.parameter_manager.get_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian Misc'
        )
        self.setattr_argument(
            "Vdp_Repeat_Time_no_sync",
            NumberValue(default=self.exp.parameter_manager.get_param('VdP2mode/Repeat_time_no_sync'), min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group= self.group_name
        )
        self.setattr_argument(
            "Vdp_Repeat_Time_sync",
            NumberValue(default=self.exp.parameter_manager.get_param('VdP2mode/Repeat_time_sync'), min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group= self.group_name
        )
        self.Vdp_mode1_freq_729_BSB_sp_delta=0.0
        self.Vdp_mode1_freq_729_2RSB_sp_delta=0.0
        self.Vdp_mode2_freq_729_BSB_sp_delta=0.0
        self.Vdp_mode2_freq_729_2RSB_sp_delta=0.0


        ### tickle related
        self.tickle_time= self.exp.parameter_manager.get_float_param("VdP2mode/rf_drive_time")
        self.tickle_amp = self.exp.parameter_manager.get_float_param("VdP2mode/rf_drive_amp")
       

    @kernel
    def prepare(self):
        vib_freq1=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq1")
        vib_freq2=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq2")
        freq_729_sp=self.exp.parameter_manager.get_float_param("frequency/729_sp")

        self.Sync_mode1_freq_729_RSB=freq_729_sp+vib_freq1
        self.Sync_mode2_freq_729_RSB=freq_729_sp+vib_freq2

        # self.Vdp_mode1_freq_729_BSB_sp_delta=-stark_shift_kernel(
        #     qubit_Sm1_2_Dm5_2,
        #     qubit_Sm1_2_Dm1_2,
        #     qubit_Sm1_2_D3_2,
        #     qubit_Sm1_2_Dm5_2,
        #     freq_sp-Vdp_freq_729_vib1,
        # qubit_Sm1_2_D3_2=self.exp.parameter_manager.get_float_param("qubit/Sm1_2_D3_2")
        # freq_sp=self.exp.parameter_manager.get_float_param("frequency/729_sp")

        # Vdp_freq_729_vib1=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq1")
        # Vdp_freq_729_vib2=self.exp.parameter_manager.get_float_param("VdP2mode/vib_freq2")

        # self.Vdp_mode1_freq_729_BSB_sp_delta=-stark_shift_kernel(
        #         qubit_Sm1_2_Dm5_2,
        #         qubit_Sm1_2_Dm1_2,
        #         qubit_Sm1_2_D3_2,
        #         qubit_Sm1_2_Dm5_2,
        #         freq_sp-Vdp_freq_729_vib1,
        #         self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode1_BSB")
        #     )
        # self.Vdp_mode1_freq_729_2RSB_sp_delta=-stark_shift_kernel(
        #         qubit_Sm1_2_Dm5_2,
        #         qubit_Sm1_2_Dm1_2,
        #         qubit_Sm1_2_D3_2,
        #         qubit_Sm1_2_Dm5_2,
        #         freq_sp+Vdp_freq_729_vib1*2,
        #         self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode1_2RSB")
        #     )
        # self.Vdp_mode2_freq_729_BSB_sp_delta=-stark_shift_kernel(
        #         qubit_Sm1_2_Dm5_2,
        #         qubit_Sm1_2_Dm1_2,
        #         qubit_Sm1_2_D3_2,
        #         qubit_Sm1_2_Dm5_2,
        #         freq_sp-Vdp_freq_729_vib2,
        #         self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode2_BSB")
        #     )
        # self.Vdp_mode2_freq_729_2RSB_sp_delta=-stark_shift_kernel(
        #         qubit_Sm1_2_Dm5_2,
        #         qubit_Sm1_2_Dm1_2,
        #         qubit_Sm1_2_D3_2,
        #         qubit_Sm1_2_Dm5_2,
        #         freq_sp+Vdp_freq_729_vib2*2,
        #         self.exp.parameter_manager.get_float_param("VdP2mode/Rabi_Freq_mode2_2RSB")
        #     )

    @kernel
    def repump(self):
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(7*us)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()

    @kernel
    def run(self, detuning=0.0*MHz, enable_tickle=False):

        #stark shift corrected frequency
        Vdp_mode1_freq_729_BSB_sp=self.Vdp_mode1_freq_729_BSB_sp
        Vdp_mode1_freq_729_2RSB_sp=self.Vdp_mode1_freq_729_2RSB_sp

        Vdp_mode2_freq_729_BSB_sp=self.Vdp_mode2_freq_729_BSB_sp#+detuning
        Vdp_mode2_freq_729_2RSB_sp=self.Vdp_mode2_freq_729_2RSB_sp#+detuning*2

        #loss in the upper spin state
        self.dds_854_dp.set(self.Vdp_drive_freq_854)
        self.dds_866_dp.set(self.Vdp_drive_freq_866)
        self.dds_854_dp.set_att(self.Vdp_drive_att_854)
        self.dds_866_dp.set_att(self.Vdp_drive_att_866)


        #self.dds_729_dp.set(self.Vdp_freq_729_dp) # we shouldn't touch the 729 dp's frequency and phase here
        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_dp.set_att(self.Vdp_att_729_dp)
        self.dds_729_dp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_sp.sw.on()

        delay(2*us)
        for i in range(self.Vdp_Repeat_Time_no_sync+self.Vdp_Repeat_Time_sync):
            # generate random phase
            # Mode 1: 1 order blue sideband
            self.dds_729_sp.set(Vdp_mode1_freq_729_BSB_sp, phase=0.)
            self.dds_729_sp.set_att(self.Vdp_mode1_drive_att_BSB_sp)

            self.dds_729_dp.sw.on()
            delay(self.Vdp_mode1_drive_time_BSB)
            self.dds_729_dp.sw.off()

            self.repump()

            # Mode 1: 2 order red sideband
            self.dds_729_sp.set(Vdp_mode1_freq_729_2RSB_sp, phase=0.)
            self.dds_729_sp.set_att(self.Vdp_mode1_drive_att_2RSB_sp)

            self.dds_729_dp.sw.on()
            delay(self.Vdp_mode1_drive_time_2RSB)
            self.dds_729_dp.sw.off()

            self.repump()

            # Mode 2: 1 order blue sideband
            self.dds_729_sp.set(Vdp_mode2_freq_729_BSB_sp, phase=0.)
            self.dds_729_sp.set_att(self.Vdp_mode2_drive_att_BSB_sp)

            self.dds_729_dp.sw.on()
            delay(self.Vdp_mode2_drive_time_BSB)
            self.dds_729_dp.sw.off()

            self.repump()

            # Mode 2: 2 order red sideband
            self.dds_729_sp.set(Vdp_mode2_freq_729_2RSB_sp, phase=0.)
            self.dds_729_sp.set_att(self.Vdp_mode2_drive_att_2RSB_sp)

            self.dds_729_dp.sw.on()
            delay(self.Vdp_mode2_drive_time_2RSB)
            self.dds_729_dp.sw.off()
         
            self.repump()

            #for sync red sideband ##########################
            self.ttl_awg_trigger.pulse(1*us)
            self.ttl_rf_switch_AWG_729SP.on()
            self.dds_729_sp.sw.off()
            self.dds_729_sp_aux.sw.off()
            delay(2*us)

            if i>=self.Vdp_Repeat_Time_no_sync:

                #for _ in range(2):
                self.dds_729_dp.sw.on()
                delay(self.Vdp_sync_time)
                self.dds_729_dp.sw.off()

                self.repump()
            else:
              
                self.dds_729_dp.sw.on()
                delay(self.Vdp_sync_time)
                self.dds_729_dp.sw.off()
                self.repump()

            delay(1*us)
            self.ttl_awg_trigger.pulse(1*us)
            delay(1*us)
            self.dds_729_sp.sw.on()
            self.ttl_rf_switch_AWG_729SP.off()

            #########################################################################################   #tickle part

            if enable_tickle and i>=self.Vdp_Repeat_Time_no_sync:
                self.ttl_awg_trigger.pulse(1*us)
                delay(self.tickle_time)
                self.ttl_awg_trigger.pulse(1*us)
                delay(2*us)

            
            if (i+1) % 5==0:
                self.exp.seq.op_pump_sigma.run()


        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_729_dp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_sp.sw.off()
        self.ttl_rf_switch_AWG_729SP.off()
        delay(5*us)