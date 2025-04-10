from artiq.experiment import *
from artiq.language.core import  kernel, TerminationRequested

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class PulseDDS(_ACFExperiment):       

    def build(self):
        self.setattr_device("core")
        self.setup(sequences)

        self.setattr_argument(
            "if_pulse",
            BooleanValue(default=True),
            tooltip="Is pulsing effect on"
        )

        self.setattr_argument(
            "on_secs",
            NumberValue(default=5*s, unit="s", min=0*s),
            tooltip="Seconds on"
        )

        self.setattr_argument(
            "off_secs",
            NumberValue(default=1*s, unit="s", min=0*s),
            tooltip="Seconds off"
        )

        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("frequency/397_far_detuned")
        
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("attenuation/397_far_detuned")


    @kernel
    def run(self):
            # self.core.break_realtime()
        self.setup_run()

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_dp.set_att(self.attenuation_397)


        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        

        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)

        # self.dds_854_dp.set(self.frequency_854_dp)
        # self.dds_854_dp.set_att(self.attenuation_854_dp)

        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        # self.dds_854_dp.sw.on()

        if self.if_pulse:
            while True:
                self.dds_866_dp.set_att(self.attenuation_866)
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                self.dds_397_far_detuned.sw.on()
                # self.dds_854_dp.sw.on()
                delay(self.on_secs)

                self.dds_397_dp.sw.on()
                # self.dds_866_dp.sw.on()
                # self.dds_866_dp.set_att(self.attenuation_866 * 1.3)
                self.dds_866_dp.set_att(self.attenuation_866 * 2.0)

                self.dds_397_far_detuned.sw.on()
                # self.dds_854_dp.sw.off()
                delay(self.off_secs)



