from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences

try:
    from beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS
except ImportError:
    from .beam_waist_common import build_zl_voltage_sets, NUM_DAC_CHANNELS


class BeamWaist866(_ACFExperiment):
    """866 Beam Waist Scan"""
    # """Scan DC solutions (ion z positions) and record fluorescence vs. z while
    # probing the 866 beam (397 held at the cooling frequency/attenuation).

    # DC solutions / z locations are edited in beam_waist_common.py.
    # 866 intensity: 'attenuation/866' (dB) argument below.
    # """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("readout/pmt_sampling_time")

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
            self.core.break_realtime()
            # set_dac issues 32 SPI writes; the CPU needs several ms of slack to queue them
            delay(10.0*ms)
            self.zotino0.set_dac(self.voltage_sets[z_i], self.channels)
            delay(self.dc_settle_time)

            total_pmt_counts = 0
            for sample_i in range(int(self.samples_per_point)):
                self.seq.doppler_cool.run()
                delay(20*us)

                # Explicit readout so the 866 frequency/attenuation used here
                # are exactly the arguments above.
                self.core.break_realtime()
                delay(10*us)
                self.dds_397_dp.set(self.frequency_397_cooling)
                self.dds_397_dp.set_att(self.attenuation_397)
                delay(10*us)
                self.dds_866_dp.set(self.frequency_866_cooling)
                self.dds_866_dp.set_att(self.attenuation_866)
                delay(10*us)

                self.dds_729_dp.sw.off()
                self.dds_397_far_detuned.sw.off()
                self.dds_397_dp.sw.on()
                self.dds_866_dp.sw.on()
                delay(50*us)

                num_pmt_pulses1 = self.ttl_pmt_input.count(
                    self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                )
                delay(10*us)

                num_pmt_pulses = num_pmt_pulses1
                if self.enable_diff_mode:
                    # Background: same 397, 866 off
                    self.dds_866_dp.sw.off()
                    delay(10*us)
                    num_pmt_pulses2 = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                    )
                    delay(10*us)
                    num_pmt_pulses = num_pmt_pulses1 - num_pmt_pulses2

                self.dds_397_dp.sw.off()
                self.dds_866_dp.sw.off()
                delay(20*us)

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
