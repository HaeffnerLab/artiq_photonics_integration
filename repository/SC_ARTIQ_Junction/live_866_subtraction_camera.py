import json
import subprocess
import sys
import threading
from pathlib import Path

from artiq.experiment import *
from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences


WINDOW_NAME = "866 On - 866 Off (Ion Only)"
DEFAULT_CAMERA_PYTHON = r"C:\Users\artiq\.conda\envs\camera_env\python.exe"
DEFAULT_CAMERA_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent / "SC_Camera_Scripts"
)


CAMERA_WORKER_CODE = r"""
import json
import sys
import traceback


def send_response(payload):
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def send_ok(**payload):
    payload["status"] = "ok"
    send_response(payload)


def send_error(error):
    send_response(
        {
            "status": "error",
            "error": str(error),
            "traceback": traceback.format_exc(),
        }
    )


class Live866CameraWorker:
    def __init__(self):
        self.cv2 = None
        self.np = None
        self.frames = None
        self.popup_options = None
        self.dark_average = None
        self.settle_frames = 0
        self.frames_per_state = 1
        self.display_gain = 1.0
        self.show_intermediate_frames = False

    def start(self, config):
        camera_scripts_dir = config["camera_scripts_dir"]
        if camera_scripts_dir not in sys.path:
            sys.path.insert(0, camera_scripts_dir)

        import cv2
        import numpy as np
        from live_spinnaker_camera import (
            CameraAcquisitionOptions,
            LivePopupOptions,
            acquire_camera_frames,
            is_live_popup_closed,
            prepare_live_popup_frame,
            process_live_popup_events,
        )
        from background_subtracted_spinnaker_camera import draw_status_text

        self.cv2 = cv2
        self.np = np
        self.is_live_popup_closed = is_live_popup_closed
        self.prepare_live_popup_frame = prepare_live_popup_frame
        self.process_live_popup_events = process_live_popup_events
        self.draw_status_text = draw_status_text
        self.settle_frames = int(config["settle_frames"])
        self.frames_per_state = int(config["frames_per_state"])
        self.display_gain = float(config["display_gain"])
        self.show_intermediate_frames = bool(config["show_intermediate_frames"])

        acquisition_options = CameraAcquisitionOptions(
            camera_index=int(config["camera_index"]),
            timeout_ms=int(config["timeout_ms"]),
            exposure_time_us=float(config["exposure_time_us"]),
            gain_db=float(config["gain_db"]),
        )
        self.popup_options = LivePopupOptions(
            window_name=config["window_name"],
            show_center_crosshair=False,
            zoom_factor=float(config["zoom_factor"]),
        )
        self.frames = acquire_camera_frames(acquisition_options)
        self.cv2.namedWindow(config["window_name"], self.cv2.WINDOW_NORMAL)
        send_ok()

    def frame_to_gray_float(self, frame):
        if frame.ndim == 3:
            frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        return frame.astype(self.np.float32)

    def is_closed(self):
        return self.is_live_popup_closed(self.popup_options.window_name)

    def grab_average(self, label):
        total = self.settle_frames + self.frames_per_state
        accum = None
        kept = 0

        for frame_index in range(total):
            frame = next(self.frames)
            if self.is_closed():
                return None, True

            if frame_index < self.settle_frames:
                # Only draw raw (non-subtracted) frames if requested; otherwise
                # keep the last subtracted image on screen.
                if self.show_intermediate_frames:
                    display_frame = self.prepare_live_popup_frame(
                        frame, self.popup_options
                    )
                    display_frame = self.draw_status_text(
                        display_frame,
                        "{}: settling...".format(label),
                    )
                    self.cv2.imshow(self.popup_options.window_name, display_frame)
                # Always pump GUI events so the window stays responsive/closable.
                self.process_live_popup_events()
                continue

            gray_frame = self.frame_to_gray_float(frame)
            accum = gray_frame if accum is None else accum + gray_frame
            kept += 1

        if kept == 0:
            raise RuntimeError("No camera frames were kept for averaging.")

        return accum / self.np.float32(kept), False

    def grab_dark(self):
        self.dark_average, closed = self.grab_average("866 OFF")
        send_ok(closed=closed)

    def grab_bright_and_show(self):
        if self.dark_average is None:
            raise RuntimeError("Cannot display subtraction before grabbing a dark frame.")

        bright_average, closed = self.grab_average("866 ON")
        if closed:
            send_ok(closed=True)
            return

        difference = self.np.clip(
            (bright_average - self.dark_average) * self.display_gain,
            0.0,
            255.0,
        )
        display = self.cv2.cvtColor(
            difference.astype(self.np.uint8),
            self.cv2.COLOR_GRAY2BGR,
        )
        display = self.prepare_live_popup_frame(display, self.popup_options)
        self.cv2.imshow(self.popup_options.window_name, display)
        self.process_live_popup_events()
        send_ok(closed=self.is_closed())

    def close(self):
        if self.frames is not None:
            self.frames.close()
            self.frames = None
        if self.cv2 is not None and self.popup_options is not None:
            try:
                self.cv2.destroyWindow(self.popup_options.window_name)
            except self.cv2.error:
                pass
        send_ok()


def main():
    worker = Live866CameraWorker()
    handlers = {
        "start": worker.start,
        "grab_dark": lambda _config: worker.grab_dark(),
        "grab_bright_and_show": lambda _config: worker.grab_bright_and_show(),
        "close": lambda _config: worker.close(),
    }

    for line in sys.stdin:
        try:
            request = json.loads(line)
            command = request["command"]
            if command not in handlers:
                raise ValueError("Unknown camera worker command: {}".format(command))
            handlers[command](request.get("config", {}))
        except Exception as error:
            send_error(error)


if __name__ == "__main__":
    main()
"""


class CameraWorkerProcess:
    """Small JSON-line bridge to the Python 3.10 camera environment."""

    def __init__(self, python_executable, config):
        self.python_executable = Path(python_executable)
        self.config = dict(config)
        self.process = None
        self.stderr_thread = None

    def start(self):
        if not self.python_executable.exists():
            raise RuntimeError(
                "Camera Python was not found: {}".format(self.python_executable)
            )

        self.process = subprocess.Popen(
            [str(self.python_executable), "-u", "-c", CAMERA_WORKER_CODE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stderr_thread = threading.Thread(
            target=self._forward_stderr,
            daemon=True,
        )
        self.stderr_thread.start()
        self._request("start", self.config)

    def _forward_stderr(self):
        for line in self.process.stderr:
            sys.stderr.write("[camera worker] {}".format(line))

    def _request(self, command, config=None):
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("Camera worker process is not running.")

        request = {"command": command, "config": config or {}}
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        return self._read_response(command)

    def _read_response(self, command):
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("Camera worker process is not running.")

        line = self.process.stdout.readline()
        if line == "":
            raise RuntimeError(
                "Camera worker exited while handling '{}'.".format(command)
            )

        response = json.loads(line)
        if response.get("status") == "error":
            raise RuntimeError(
                "Camera worker failed during '{}': {}\n{}".format(
                    command,
                    response.get("error", "unknown error"),
                    response.get("traceback", ""),
                )
            )
        return response

    def grab_dark(self):
        return bool(self._request("grab_dark").get("closed", False))

    def grab_bright_and_show(self):
        return bool(self._request("grab_bright_and_show").get("closed", False))

    def close(self):
        if self.process is None:
            return

        try:
            if self.process.poll() is None:
                self._request("close")
        except Exception as error:
            print("Warning: failed to close camera worker cleanly: {}".format(error))
        finally:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self.process = None


class Live866SubtractionCameraEnv(_ACFExperiment):
    """Live 866 subtraction"""
    #"""Live 866 subtraction using PySpin in a separate Python 3.10 process."""

    def build(self):
        self.setattr_device("core")
        self.setup(sequences)

        self.seq.ion_store.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("attenuation/866")

        self.setattr_argument(
            "camera_python",
            StringValue(default=DEFAULT_CAMERA_PYTHON),
            tooltip="Python executable that can import cv2 and PySpin",
            group="Camera",
        )
        self.setattr_argument(
            "camera_scripts_dir",
            StringValue(default=DEFAULT_CAMERA_SCRIPTS_DIR),
            tooltip="Folder containing live_spinnaker_camera.py",
            group="Camera",
        )
        self.setattr_argument(
            "exposure_time_us",
            NumberValue(default=300000, precision=0, step=1000, min=1),
            tooltip="Camera exposure time (us, integer)",
            group="Camera",
        )
        self.setattr_argument(
            "gain_db",
            NumberValue(default=45.0, precision=1, step=1.0, min=0.0),
            tooltip="Camera gain (dB)",
            group="Camera",
        )
        self.setattr_argument(
            "camera_index",
            NumberValue(default=0, precision=0, step=1, min=0),
            group="Camera",
        )
        self.setattr_argument(
            "settle_frames",
            NumberValue(default=2, precision=0, step=1, min=0),
            tooltip="Frames discarded after each 866 switch",
            group="Subtraction",
        )
        self.setattr_argument(
            "frames_per_state",
            NumberValue(default=1, precision=0, step=1, min=1),
            tooltip="Frames averaged for each 866-off / 866-on image",
            group="Subtraction",
        )
        self.setattr_argument(
            "display_gain",
            NumberValue(default=1.0, precision=2, step=0.5, min=0.01),
            tooltip="Multiplier applied to the difference image for display",
            group="Display",
        )
        self.setattr_argument(
            "show_intermediate_frames",
            BooleanValue(default=False),
            tooltip="Show raw (non-subtracted) frames while settling. "
            "Off: only the subtracted image is displayed.",
            group="Display",
        )
        self.setattr_argument(
            "zoom_factor",
            NumberValue(default=4.0, precision=1, step=0.5, min=1.0),
            group="Display",
        )
        self.setattr_argument(
            "off_frame_866_freq_hz",
            NumberValue(default=5000, precision=0, step=100, min=1),
            tooltip="Frequency (Hz) of the 866 square-wave pulse during the dark (866 OFF) exposure",
            group="Subtraction",
        )
        self.setattr_argument(
            "off_frame_866_duty_cycle",
            NumberValue(default=5.0, precision=1, step=1.0, min=0.1, max=99.9),
            tooltip="Duty cycle (%) of the 866 pulse during the dark (866 OFF) exposure",
            group="Subtraction",
        )

    @kernel
    def init_lasers(self):
        """397 on at cooling settings, 866 on so the ion starts bright."""
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
    def set_866(self, on: TBool):
        self.core.break_realtime()
        if on:
            self.dds_866_dp.sw.on()
        else:
            self.dds_866_dp.sw.off()
        delay(10 * us)

    @kernel
    def pulse_866_off_frame(self, n_periods: TInt32, on_mu: TInt64, off_mu: TInt64):
        """Pulse the 866 as a square wave during a dark (866 OFF) camera exposure.

        All float math is done on the host (see run()); the kernel only uses
        integer machine units, because soft-float on the core CPU is too slow
        for short pulses and causes RTIOUnderflow.
        """
        self.core.break_realtime()
        # Extra slack so the first edge is never in the past.
        delay(1.0 * ms)
        for _ in range(n_periods):
            self.dds_866_dp.sw.on()
            delay_mu(on_mu)
            self.dds_866_dp.sw.off()
            delay_mu(off_mu)
        # Leave the 866 off at the end of the dark frame.
        self.dds_866_dp.sw.off()
        delay(10 * us)

    @kernel
    def shutdown_lasers(self):
        self.core.break_realtime()
        self.dds_397_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(20 * us)
        self.seq.ion_store.run()
        delay(5 * us)

    def make_camera_config(self):
        return {
            "camera_scripts_dir": str(self.camera_scripts_dir),
            "camera_index": int(self.camera_index),
            "timeout_ms": int(max(5000, 3 * float(self.exposure_time_us) / 1000)),
            "exposure_time_us": float(self.exposure_time_us),
            "gain_db": float(self.gain_db),
            "window_name": WINDOW_NAME,
            "settle_frames": int(self.settle_frames),
            "frames_per_state": int(self.frames_per_state),
            "display_gain": float(self.display_gain),
            "show_intermediate_frames": bool(self.show_intermediate_frames),
            "zoom_factor": float(self.zoom_factor),
        }

    def run(self):
        camera_worker = CameraWorkerProcess(
            self.camera_python,
            self.make_camera_config(),
        )
        lasers_initialized = False

        # Total dark-frame duration in seconds: settle + capture frames,
        # each lasting one exposure period.
        frames_per_dark = int(self.settle_frames) + int(self.frames_per_state)
        dark_duration_s = frames_per_dark * float(self.exposure_time_us) * 1e-6

        # Precompute the pulse train on the host (integer machine units).
        period_s = 1.0 / float(self.off_frame_866_freq_hz)
        on_mu = self.core.seconds_to_mu(
            period_s * float(self.off_frame_866_duty_cycle) / 100.0
        )
        period_mu = self.core.seconds_to_mu(period_s)
        off_mu = max(period_mu - on_mu, 1)
        n_periods = max(int(dark_duration_s / period_s), 1)

        camera_worker.start()
        try:
            self.init_lasers()
            lasers_initialized = True

            while True:
                # --- Dark (866 OFF) frame -------------------------------------------
                # Launch the 866 square-wave pulser on the kernel in a background
                # thread so it runs concurrently with the blocking camera grab.
                pulse_thread = threading.Thread(
                    target=self.pulse_866_off_frame,
                    args=(n_periods, on_mu, off_mu),
                    daemon=True,
                )
                pulse_thread.start()
                closed = camera_worker.grab_dark()
                pulse_thread.join()  # ensure pulsing stops before we continue
                if closed:
                    break

                # --- Bright (866 ON) frame ------------------------------------------
                self.set_866(True)
                if camera_worker.grab_bright_and_show():
                    break
        finally:
            camera_worker.close()
            if lasers_initialized:
                self.shutdown_lasers()
