from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

try:
    from bem_voltage_bridge import NUM_DAC_CHANNELS, build_scan_voltage_sets
except ImportError:
    from .bem_voltage_bridge import NUM_DAC_CHANNELS, build_scan_voltage_sets


# =============================================================================
# USER INPUT
# =============================================================================
# DC solutions are looked up in / computed into the BEM voltage database
# (settings in bem_voltage_bridge.py).
#
# "linear"   : EX_START -> EX_STOP in ascending EX_STEP increments
# "outwards" : same values, starting at the middle of the range and alternating outwards
# "random"   : same values, shuffled (RANDOM_SEED in bem_voltage_bridge.py)
SCAN_ORDERING = "linear"

# ex (V/mm). Inclusive on both ends; step must divide the range.
EX_START_V_PER_MM = -0.5
EX_STOP_V_PER_MM = 0.5
EX_STEP_V_PER_MM = 0.1

# Fixed parameters, held constant during the ex scan. zl in um, ey/ez in V/mm, u1..u5 in V/mm^2.
FIXED_PARAMETERS = {
    "zl": 680.0,
    "ey": 3.0,
    "ez": 0.0,
    "u1": 0.0,
    "u2": 6.0,
    "u3": 2.0,  # (1/3) * u2
    "u4": 0.0,
    "u5": 0.0,
}
# =============================================================================


class ExScan(_ACFExperiment):
    """Ex Scan"""
    #"""Ex Field Scan (397 fluorescence vs. ex)"""

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
        self.voltage_sets, self.ex_values_v_per_mm = build_scan_voltage_sets(
            "ex", SCAN_ORDERING, EX_START_V_PER_MM, EX_STOP_V_PER_MM, EX_STEP_V_PER_MM,
            FIXED_PARAMETERS, x_name="EX_*_V_PER_MM",
        )

        num_points = len(self.ex_values_v_per_mm)
        self.experiment_data.set_nd_dataset(
            "pmt_counts", [num_points, int(self.samples_per_point)], broadcast=True
        )
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_points, broadcast=True)
        self.experiment_data.set_list_dataset("ex_v_per_mm", num_points, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg",
            x_data_name="ex_v_per_mm"
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

        for point_i in range(len(self.voltage_sets)):
            # Apply the DC solution for this ex value and let it settle
            self.core.break_realtime()
            # set_dac issues 32 SPI writes; the CPU needs several ms of slack to queue them
            delay(10.0*ms)
            self.zotino0.set_dac(self.voltage_sets[point_i], self.channels)
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
                    "pmt_counts", [point_i, sample_i], num_pmt_pulses
                )
                total_pmt_counts += num_pmt_pulses
                self.core.break_realtime()
                delay(100*us)

            pmt_counts_avg = total_pmt_counts / self.samples_per_point

            self.experiment_data.append_list_dataset("pmt_counts_avg", pmt_counts_avg)
            self.experiment_data.append_list_dataset("ex_v_per_mm", self.ex_values_v_per_mm[point_i])

            self.core.break_realtime()
            delay(200*us)

        self.seq.ion_store.run()
