from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

try:
    from beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS
except ImportError:
    from .beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS


class BeamWaist854(_ACFExperiment):
    """854 Beam Waist Scan"""
    # """Scan DC solutions (ion z positions). At each z: shelve the ion with a
    # 729 pi pulse, apply a fixed-duration 854 (+866) pulse, then read out. Records
    # the quenching probability vs. z.

    # A quenched ion returns to S (bright): quench probability = fraction of
    # samples with PMT counts AT/ABOVE the threshold.

    # DC solutions / z locations are edited in beam_waist_common.py.
    # 854 intensity: 'att_854' (dB) argument below.
    # """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/866")

        # Shelving pi pulse
        self.setattr_argument(
            "PI_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/S1_2_D3_2"),
                        min=180*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for the shelving pi pulse",
            group="Pi pulse excitation"
        )
        self.setattr_argument(
            "PI_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"),
                        min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation for the pi pulse",
            group="Pi pulse excitation"
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=10*us, min=0*us, max=1000*us, unit="us", precision=8),
            tooltip="Drive time for the pi pulse",
            group="Pi pulse excitation"
        )

        # 854 quench pulse
        self.setattr_argument(
            "freq_854",
            NumberValue(default=self.parameter_manager.get_param("frequency/854_dp"),
                        min=20*MHz, max=300*MHz, unit="MHz", precision=5),
            tooltip="854 double pass frequency",
            group="854 pulse"
        )
        self.setattr_argument(
            "att_854",
            NumberValue(default=self.parameter_manager.get_param("attenuation/854_dp"),
                        min=2*dB, max=30*dB, unit="dB", precision=5),
            tooltip="854 attenuation (sets beam intensity)",
            group="854 pulse"
        )
        self.setattr_argument(
            "pulse_time_854",
            NumberValue(default=10*us, min=0*us, max=10000*us, unit="us", precision=8),
            tooltip="Fixed 854 pulse duration at every z",
            group="854 pulse"
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
            tooltip="Counts at/above this = ion bright (quenched)",
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
        self.experiment_data.set_list_dataset("quench_prob", num_points, broadcast=True)
        self.experiment_data.set_list_dataset("z_locations_um", num_points, broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            y_data_name="quench_prob",
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

            total_quenched = 0
            for sample_i in range(int(self.samples_per_point)):
                # Reset to S state and cool
                self.seq.repump_854.run()
                delay(5*us)
                self.seq.doppler_cool.run()
                delay(5*us)

                # Shelve with 729 pi pulse
                self.seq.rabi.run(
                    self.PI_drive_time, self.PI_freq_729_dp, self.PI_att_729_dp
                )
                delay(5*us)

                # Fixed-duration 854 quench (866 on to pump out of P3/2)
                self.dds_854_dp.set(self.freq_854)
                self.dds_854_dp.set_att(self.att_854)
                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_866_dp.set_att(self.attenuation_866)
                self.dds_854_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(self.pulse_time_854)
                self.dds_854_dp.sw.off()
                self.dds_866_dp.sw.off()
                delay(5*us)

                # State readout
                num_pmt_pulses = self.seq.readout_397.run()
                delay(5*us)

                self.experiment_data.insert_nd_dataset(
                    "pmt_counts", [z_i, sample_i], num_pmt_pulses
                )
                if num_pmt_pulses >= self.threshold_pmt_count:
                    total_quenched += 1

                # Return ion to S and protect it
                self.seq.repump_854.run()
                self.seq.ion_store.run()
                self.core.break_realtime()
                delay(2*ms)

            self.experiment_data.append_list_dataset(
                "quench_prob", float(total_quenched) / self.samples_per_point
            )
            self.experiment_data.append_list_dataset("z_locations_um", self.z_locations_um[z_i])

            self.core.break_realtime()
            delay(200*us)

        self.seq.ion_store.run()
