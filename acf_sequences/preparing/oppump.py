from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms


class Op_pump(Sequence):

    def __init__(self):
        super().__init__()

        self.add_parameter("attenuation/854_dp")
        self.add_parameter("frequency/854_dp")
        
        self.add_parameter("attenuation/866")
        self.add_parameter("frequency/866_cooling")


        self.add_argument_from_parameter("Op_pump_freq_729_dp", "qubit/S1_2_Dm3_2")
        self.add_argument_from_parameter("Op_pump_att_729_dp", "optical_pumping/att_729_dp")
        # self.add_argument_from_parameter("Op_pump_freq_729_sp", "frequency/729_sp")
        # self.add_argument_from_parameter("Op_pump_att_729_sp", "optical_pumping/att_729_sp")
        self.add_argument_from_parameter("Op_pump_att_729", "optical_pumping/att_729_dp")


        self.add_argument("Op_pump_cycle", NumberValue(default=40, min=0, max=1000, precision=0, step=1))

    @kernel
    def run(self, freq_diff_dp=0.0*MHz):

            
        self.dds_729_dp.set(self.Op_pump_freq_729_dp+7.0*freq_diff_dp/5.0)
        self.dds_729_dp.set_att(self.Op_pump_att_729_dp)

        # self.dds_729_sp.set(self.Op_pump_freq_729_sp)
        # self.dds_729_sp.set_att(self.Op_pump_att_729_sp)

        self.dds_854_dp.set_att(self.attenuation_854_dp)
        self.dds_866_dp.set_att(self.attenuation_866)

        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)

        delay(5*us)

        for i in range(self.Op_pump_cycle):
            # ground state optical pumping
            self.dds_729_dp.sw.on()
            # self.dds_729_sp.sw.on()
            delay(10*us)
            self.dds_729_dp.sw.off()

            self.dds_854_dp.sw.on()
            self.dds_866_dp.sw.on()
            delay(10*us)
            self.dds_854_dp.sw.off()
            self.dds_866_dp.sw.off()
        
        delay(5*us)

