"""Live Differential Ion-Only PMT Photon Count Monitor.

Implements real-time continuous differential PMT readout for PMT alignment as
specified in handoff.md, incorporating the duty cycle and 866 pulse frequency
features from live_866_subtraction_camera.py.

Broadcasts real-time readings to 'PMT_count' and elapsed sample times to
'PMT_count_time' for the fixed-window pmt_sliding_plot.py applet. PMT_count is
also compatible with:
  - acf/applets/pmt_plot_monitor.py (live scrolling chart)
  - acf/applets/pmt_monitor.py (numerical display)
"""

import sys
import time
from collections import deque
from pathlib import Path
import numpy as np

# Ensure acf and acf_sequences are on sys.path regardless of execution root
_current_dir = Path(__file__).resolve().parent
for _candidate in [_current_dir, _current_dir / "(Reference) artiq_photonics_integration"]:
    if (_candidate / "acf").exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from artiq.experiment import *
from artiq.language.core import TerminationRequested
from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences


class Live866SubtractionPMT(_ACFExperiment):
    """Live 866 subtraction PMT"""

    def build(self):
        self.setattr_device("core")
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        # Laser frequencies & attenuations
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/866")

        # PMT Readout timing
        self.setattr_argument(
            "gate_time_ms",
            NumberValue(default=10.0, min=0.1, step=1.0),
            tooltip="PMT sampling time in milliseconds for each ON and OFF measurement window (1000 = 1 s)",
            group="Readout",
        )
        self.setattr_argument(
            "loop_delay",
            NumberValue(default=20 * ms, unit="ms", min=1 * ms, max=1000 * ms),
            tooltip="Cooling delay between consecutive differential measurement cycles",
            group="Readout",
        )

        # 866 Subtraction & Modulation features (incorporated from live_866_subtraction_camera.py)
        self.setattr_argument(
            "off_frame_866_freq_hz",
            NumberValue(default=5000, precision=0, step=100, min=1),
            tooltip="Frequency (Hz) of the 866 square-wave pulse during the dark (866 OFF) measurement",
            group="Subtraction",
        )
        self.setattr_argument(
            "off_frame_866_duty_cycle",
            NumberValue(default=5.0, precision=1, step=1.0, min=0.0, max=99.9),
            tooltip="Duty cycle (%) of 866 pulse during dark (866 OFF) measurement (0.0% = held completely OFF)",
            group="Subtraction",
        )
        self.setattr_argument(
            "enable_diff_mode",
            BooleanValue(default=True),
            tooltip="Enable differential mode (866 ON - 866 OFF). If disabled, outputs raw 866 ON counts.",
            group="Subtraction",
        )
        self.setattr_argument(
            "normalize_duty_cycle",
            BooleanValue(default=False),
            tooltip="Compensate for non-zero 866 duty cycle during OFF measurement by scaling N_diff / (1 - duty_cycle)",
            group="Subtraction",
        )

        # Display and Applet options
        self.setattr_argument(
            "display_gain",
            NumberValue(default=1.0, precision=2, step=0.1, min=0.01),
            tooltip="Multiplier applied to the difference signal",
            group="Display",
        )
        self.setattr_argument(
            "display_as_cps",
            BooleanValue(default=False),
            tooltip="Convert and broadcast counts in counts per second (cps) instead of raw counts per gate",
            group="Display",
        )
        self.setattr_argument(
            "clip_negative_to_zero",
            BooleanValue(default=False),
            tooltip="Clip negative differential counts (due to Poissonian noise) to zero",
            group="Display",
        )
        self.setattr_argument(
            "save_diagnostic_datasets",
            BooleanValue(default=True),
            tooltip="Also broadcast raw datasets (PMT_count_on, PMT_count_off, PMT_count_raw_diff)",
            group="Display",
        )
        self.setattr_argument(
            "plot_window",
            NumberValue(default=10 * s, unit="s", min=1 * s, max=60 * s),
            tooltip="PMT dataset history retained (at least 10 seconds for the sliding applet)",
            group="Display",
        )

    def prepare(self):
        # Set list dataset for PMT_count to integrate with pmt_plot_monitor and pmt_monitor
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
        self.experiment_data.set_list_dataset("PMT_count_time", 1, broadcast=True)
        self.plot_window_s = max(float(self.plot_window), 10.0)
        self.pmt_time_origin = time.monotonic()
        self.pmt_history = deque()

        if self.save_diagnostic_datasets:
            self.set_dataset("PMT_count_on", 0, broadcast=True)
            self.set_dataset("PMT_count_off", 0, broadcast=True)
            self.set_dataset("PMT_count_raw_diff", 0, broadcast=True)

        # Precompute timing parameters in machine units on the host
        # Soft-float on the ARTIQ core CPU is too slow and causes RTIOUnderflow
        self.gate_time_s = float(self.gate_time_ms) * ms
        self.gate_time_mu = np.int64(self.core.seconds_to_mu(self.gate_time_s))
        # Keep future 866 edges queued while draining the PMT input FIFO.
        self.count_slack_mu = np.int64(self.core.seconds_to_mu(200 * us))

        duty_fraction = float(self.off_frame_866_duty_cycle) / 100.0
        if duty_fraction <= 0.0 or not self.enable_diff_mode:
            self.pulsing_enabled = False
            self.on_mu = np.int64(0)
            self.off_mu = np.int64(0)
        else:
            period_s = 1.0 / float(self.off_frame_866_freq_hz)
            on_s = period_s * duty_fraction
            off_s = period_s - on_s
            self.on_mu = np.int64(self.core.seconds_to_mu(on_s))
            period_mu = np.int64(self.core.seconds_to_mu(period_s))
            self.off_mu = np.int64(max(period_mu - self.on_mu, 1))

            self.pulsing_enabled = True if self.on_mu > 0 else False

        if self.normalize_duty_cycle and duty_fraction < 1.0:
            self.duty_norm_factor = 1.0 - duty_fraction
        else:
            self.duty_norm_factor = 1.0

    @rpc(flags={"async"})
    def update_pmt_dataset(self, num_on: TInt32, num_off: TInt32):
        """Asynchronously process counts and broadcast to ARTIQ applets on the host."""
        timestamp = time.monotonic() - self.pmt_time_origin
        if self.enable_diff_mode:
            raw_diff = num_on - num_off
            val = float(raw_diff)
            if self.normalize_duty_cycle and self.duty_norm_factor > 0.0:
                val = val / self.duty_norm_factor
        else:
            raw_diff = num_on
            val = float(num_on)

        val = val * float(self.display_gain)

        if self.display_as_cps and self.gate_time_s > 0.0:
            val = val / self.gate_time_s

        if self.clip_negative_to_zero and val < 0.0:
            val = 0.0

        self.pmt_history.append((timestamp, val))
        cutoff = timestamp - self.plot_window_s
        while self.pmt_history and self.pmt_history[0][0] < cutoff:
            self.pmt_history.popleft()
        self.set_dataset(
            "PMT_count",
            [sample[1] for sample in self.pmt_history],
            broadcast=True,
        )
        self.set_dataset(
            "PMT_count_time",
            [sample[0] for sample in self.pmt_history],
            broadcast=True,
        )

        if self.save_diagnostic_datasets:
            self.set_dataset("PMT_count_on", num_on, broadcast=True)
            self.set_dataset("PMT_count_off", num_off, broadcast=True)
            self.set_dataset("PMT_count_raw_diff", raw_diff, broadcast=True)

    @kernel
    def init_lasers(self):
        """Initialize 397 and 866 cooling lasers and ensure other beams are off."""
        self.core.reset()
        self.core.break_realtime()
        delay(3.0 * ms)
        self.setup_run()
        self.core.break_realtime()
        delay(3.0 * ms)

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_dp.set_att(self.attenuation_397)
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)
        delay(10 * us)

        self.dds_729_dp.sw.off()
        self.dds_397_far_detuned.sw.off()
        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(50 * us)

    @kernel
    def shutdown_lasers(self):
        """Safely restore standard ion storage state upon termination."""
        self.core.break_realtime()
        self.dds_397_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(20 * us)
        self.seq.ion_store.run()
        delay(5 * us)

    @kernel
    def run(self):
        self.init_lasers()
        try:
            while True:
                if self.scheduler.check_pause():
                    break

                self.core.break_realtime()

                # --- 1. Signal + Background (866 ON, 397 ON) ---
                self.dds_866_dp.sw.on()
                delay(30 * us)
                gate_end_on = self.ttl_pmt_input.gate_rising_mu(self.gate_time_mu)
                num_on = self.ttl_pmt_input.count(gate_end_on)
                delay(30 * us)

                # --- 2. Background only (866 OFF / Pulsed, 397 ON) ---
                num_off = 0
                if self.enable_diff_mode:
                    if not self.pulsing_enabled:
                        # 866 held completely OFF during background gate
                        self.dds_866_dp.sw.off()
                        delay(30 * us)
                        gate_end_off = self.ttl_pmt_input.gate_rising_mu(self.gate_time_mu)
                        num_off = self.ttl_pmt_input.count(gate_end_off)
                    else:
                        # 866 pulsed with frequency & duty cycle during background gate
                        self.dds_866_dp.sw.off()
                        delay(30 * us)
                        t_gate_start = now_mu()
                        gate_end_off = self.ttl_pmt_input.gate_rising_mu(self.gate_time_mu)
                        at_mu(t_gate_start)
                        while now_mu() < gate_end_off:
                            self.dds_866_dp.sw.on()
                            delay_mu(min(self.on_mu, gate_end_off - now_mu()))
                            self.dds_866_dp.sw.off()
                            delay_mu(min(self.off_mu, gate_end_off - now_mu()))
                            # count() drains while waiting. Stop behind the
                            # queued waveform so the next pulse stays in the
                            # future; waiting to gate_end_off here would leave
                            # the rest of the waveform unscheduled.
                            num_off += self.ttl_pmt_input.count(
                                now_mu() - self.count_slack_mu
                            )
                        at_mu(gate_end_off)
                        num_off += self.ttl_pmt_input.count(gate_end_off)

                    # Immediately turn 866 back on to resume Doppler cooling
                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    delay(30 * us)

                # --- 3. Compute Differential & Update Dataset ---
                self.update_pmt_dataset(num_on, num_off)

                # Delay between measurements provides cooling steady-state time
                delay(self.loop_delay)

        except TerminationRequested:
            pass
        finally:
            self.shutdown_lasers()
