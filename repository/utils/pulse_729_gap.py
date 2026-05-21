from artiq.experiment import *
from artiq.language.core import TerminationRequested

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences


class Pulse729Gap(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        # Match parameter-loading style in default_experiment.py
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("attenuation/729_dp")

        self.setattr_argument(
            "gap_secs",
            NumberValue(default=0.02 * s, unit="s", min=0 * s, precision=8),
            tooltip="Gap between 729 on/off transitions",
        )

    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)

    @kernel
    def run(self):
        self.setup_run()
        self.core.break_realtime()

        # Protect ion with the standard sequence before pulsing 729
        self.seq.ion_store.run()
        delay(5 * us)

        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_dp.sw.off()

        try:
            while True:
                self.dds_729_dp.sw.on()
                delay(self.gap_secs)
                self.dds_729_dp.sw.off()
                delay(self.gap_secs)
        except TerminationRequested:
            pass
