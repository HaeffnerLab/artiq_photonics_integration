from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class SetDDS(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        # self.argument_manager = argument_manager
        # self.argument_manager.initialize(self)
        # self.argument_manager.set_arguments([
        #     "attenuation_397",
        #     "freq_397_far_detuned",
        #     "attenuation_397_far_detuned",
        #     "attenuation_866",
        #     "freq_866_addressing",
        #     "attenuation_866_addressing",
        #     "freq_854_dp",
        #     "attenuation_854_dp",
        #     "freq_729_sp",
        #     "freq_729_sp_aux",
        #     "attenuation_729_dp",
        #     "attenuation_729_sp",
        #     "attenuation_729_sp_aux",
        #     "phase_729_sp",
        #     "phase_729_sp_aux",
        #     "freq_rf_g_qubit",
        #     "attenuation_rf_g_qubit"
        # ])

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/866_cooling")
    #     self.add_arg_from_param("frequency/866_addressing")
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
       # self.add_arg_from_param("frequency/729_sp_aux")
        self.add_arg_from_param("frequency/854_dp")

        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
    #     self.add_arg_from_param("attenuation/866_addressing")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
     #   self.add_arg_from_param("attenuation/729_sp_aux")
        self.add_arg_from_param("attenuation/854_dp")
    #     #self.add_arg_from_param("misc/pmt_sampling_time")

        self.add_arg_from_param("attenuation/RF")
        self.add_arg_from_param("frequency/RF")


        # self.setattr_argument(
        #     "freq_397",
        #     NumberValue(
        #         default=self.parameter_manager.get_param("frequency/397_resonance"),
        #         unit="MHz",
        #         min=180*MHz,
        #         max=240*MHz
        #     ),
        # )
        # self.setattr_argument(
        #     "freq_866",
        #     NumberValue(
        #         default=self.parameter_manager.get_param("frequency/866_resonance"),
        #         unit="MHz",
        #         min=70*MHz,
        #         max=125*MHz
        #     ),
        # )

        # self.setattr_argument(
        #     "freq_729_dp",
        #     NumberValue(
        #         default=210*MHz,
        #         unit="MHz",
        #         min=180*MHz,
        #         max=240*MHz
        #     ),
        # )

    @kernel
    def run(self):

        # set attenuation
        self.core.break_realtime()

        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        self.dds_866_dp.set_att(self.attenuation_866)
        self.dds_854_dp.set_att(self.attenuation_854_dp)
        #self.dds_866_addressing.set_att(self.attenuation_866_addressing)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        #self.dds_729_sp_aux.set_att(self.attenuation_729_sp_aux)

        self.dds_rf_g_qubit.set_att(self.attenuation_RF)


        # set frequency and phase

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_854_dp.set(self.frequency_854_dp)
        #self.dds_866_addressing.set(self.freq_866_addressing)
        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_sp.set(self.frequency_729_sp, 0.0)#self.phase_729_sp)
        #self.dds_729_sp_aux.set(self.freq_729_sp_aux,phase = self.phase_729_sp_aux)
        #self.dds_rf_g_qubit.set(self.freq_rf_g_qubit)

        self.dds_rf_g_qubit.set(self.frequency_RF)

        # set phase

        #self.dds_729_sp.set_phase(self.phase_729_sp)
        #self.dds_729_sp_aux.set_phase(self.phase_729_sp_aux)


        # turn devices on
        self.dds_397_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        self.dds_866_dp.sw.off()
        self.dds_854_dp.sw.on()
        delay(2*ms)
        #self.dds_866_addressing.sw.on()
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        delay(2*ms)
        self.dds_729_sp_aux.sw.off()
        self.dds_rf_g_qubit.sw.off()
        

        while True:
            pass
