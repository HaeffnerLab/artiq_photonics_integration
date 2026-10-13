from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

try:
    from beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS
except ImportError:
    from .beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS


class BeamWaist397(_ACFExperiment):
    """397 Beam Waist Scan"""
    # """Scan a list of DC solutions (ion z positions) and record 397 fluorescence
    # vs. z. The result is shown live in the Experiment Monitor applet.

    # DC solutions / z locations are edited in beam_waist_common.py.
    # 397 intensity: 'attenuation/397' (dB), exposed in the GUI via readout_397.
    # """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_cooling")

        self.setattr_argument(
            "samples_per_point",
            NumberValue(default=5, precision=0, step=1, min=1),
            tooltip="Number of fluorescence samples per DC solution",
            group="Misc"
        )
        self.setattr_argument(
            "dc_settle_time",
            NumberValue(default=10*ms, unit="ms", min=0*ms, precision=3),
            tooltip="Wait after applying a DC solution before measuring",
            group="Misc"
        )
        self.setattr_argument("enable_diff_mode", BooleanValue(True))

        self.channels = [i for i in range(NUM_DAC_CHANNELS)]

    def prepare(self):
        # Done here rather than in build() so that the ARTIQ repository scan does
        # not start the BEM env; errors are raised on submission.
        self.voltage_sets, self.z_locations_um = build_zl_voltage_sets()

        num_points = len(self.z_locations_um)
        self.experiment_data.set_nd_dataset(
            "pmt_counts", [num_points, int(self.samples_per_point)], broadcast=True
        )
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_points, broadcast=True)
        self.experiment_data.set_list_dataset("z_locations_um", num_points, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="z_locations_um"
        )

    @kernel
    def run(self):
        self.core.break_realtime()
        delay(3.0*ms)
        self.setup_run()
        self.core.break_realtime()
        delay(3.0*ms)

        self.zotino0.init()
        delay(10*ms)

        for z_i in range(len(self.voltage_sets)):
            # Apply the DC solution for this z location and let it settle
            self.core.break_realtime()
            # set_dac issues 32 SPI writes; the CPU needs several ms of slack to queue them
            delay(10.0*ms)
            self.zotino0.set_dac(self.voltage_sets[z_i], self.channels)
            delay(self.dc_settle_time)

            total_pmt_counts = 0
            for sample_i in range(int(self.samples_per_point)):
                self.seq.doppler_cool.run()
                delay(20*us)

                num_pmt_pulses1 = self.seq.readout_397.run(
                    freq_397_dp=self.frequency_397_cooling
                )
                delay(10*us)

                if self.enable_diff_mode:
                    num_pmt_pulses2 = self.seq.readout_397.run(
                        freq_397_dp=self.frequency_397_cooling, turn_off_866=True
                    )
                    num_pmt_pulses = num_pmt_pulses1 - num_pmt_pulses2
                else:
                    num_pmt_pulses = num_pmt_pulses1

                # Protect ion
                self.seq.ion_store.run()
                delay(5*us)

                self.experiment_data.insert_nd_dataset(
                    "pmt_counts", [z_i, sample_i], num_pmt_pulses
                )
                total_pmt_counts += num_pmt_pulses
                self.core.break_realtime()
                delay(100*us)

            pmt_counts_avg = total_pmt_counts / self.samples_per_point

            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("z_locations_um", self.z_locations_um[z_i])

            self.core.break_realtime()
            delay(200*us)

        self.seq.ion_store.run()
