from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

try:
    from beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS
except ImportError:
    from .beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS


class BeamWaist729(_ACFExperiment):
    """729 Beam Waist Scan"""
    # """Scan DC solutions (ion z positions); at each z apply a fixed-duration 729
    # pulse and record the shelving probability vs. z.

    # Shelved ion (S -> D) is dark: shelving probability = fraction of samples with
    # PMT counts BELOW the threshold.

    # DC solutions / z locations are edited in beam_waist_common.py.
    # 729 intensity: 'att_729_dp' (dB) argument below.
    # """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/S1_2_D3_2"),
                        min=180*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="729 pulse"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"),
                        min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation (sets beam intensity)",
            group="729 pulse"
        )
        self.setattr_argument(
            "pulse_time",
            NumberValue(default=10*us, min=0*us, max=10000*us, unit="us", precision=8),
            tooltip="Fixed 729 pulse duration at every z",
            group="729 pulse"
        )

        self.setattr_argument(
            "samples_per_point",
            NumberValue(default=25, precision=0, step=1, min=1),
            tooltip="Number of shots per DC solution",
            group="Misc"
        )
        self.setattr_argument(
            "dc_settle_time",
            NumberValue(default=10*ms, unit="ms", min=0*ms, precision=3),
            tooltip="Wait after applying a DC solution before measuring",
            group="Misc"
        )
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Counts below this = ion dark (shelved)",
            group="Misc"
        )

        self.channels = [i for i in range(NUM_DAC_CHANNELS)]

    def prepare(self):
        # Done here rather than in build() so that the ARTIQ repository scan does
        # not start the BEM env; errors are raised on submission.
        self.voltage_sets, self.z_locations_um = build_zl_voltage_sets()

        num_points = len(self.z_locations_um)
        self.experiment_data.set_nd_dataset(
            "pmt_counts", [num_points, int(self.samples_per_point)], broadcast=True
        )
        self.experiment_data.set_list_dataset("shelving_prob", num_points, broadcast=True)
        self.experiment_data.set_list_dataset("z_locations_um", num_points, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="shelving_prob",
            x_data_name="z_locations_um",
            pen=False
        )

    @kernel
    def run(self):
        self.core.break_realtime()
        delay(3.0*ms)
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()
        delay(3.0*ms)

        self.zotino0.init()
        delay(10*ms)

        for z_i in range(len(self.voltage_sets)):
            self.core.break_realtime()
            # set_dac issues 32 SPI writes; the CPU needs several ms of slack to queue them
            delay(10.0*ms)
            self.zotino0.set_dac(self.voltage_sets[z_i], self.channels)
            delay(self.dc_settle_time)

            total_shelved = 0
            for sample_i in range(int(self.samples_per_point)):
                # Reset to S state and cool
                self.seq.repump_854.run()
                delay(5*us)
                self.seq.doppler_cool.run()
                delay(5*us)

                # Fixed-duration 729 pulse
                self.seq.rabi.run(self.pulse_time, self.freq_729_dp, self.att_729_dp)

                # State readout
                num_pmt_pulses = self.seq.readout_397.run()
                delay(5*us)

                self.experiment_data.insert_nd_dataset(
                    "pmt_counts", [z_i, sample_i], num_pmt_pulses
                )
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_shelved += 1

                # Return ion to S and protect it
                self.seq.repump_854.run()
                self.seq.ion_store.run()
                self.core.break_realtime()
                delay(2*ms)

            self.experiment_data.append_list_dataset(
                "shelving_prob", float(total_shelved) / self.samples_per_point
            )
            self.experiment_data.append_list_dataset("z_locations_um", self.z_locations_um[z_i])

            self.core.break_realtime()
            delay(200*us)

        self.seq.ion_store.run()
