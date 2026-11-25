"""Apply the DC solution for one user-chosen set of multipole parameters.

zl, ex, ey, ez and u1..u5 are entered in the dashboard argument menu. On
submission, the matching DC solution is looked up in (or, if ALLOW_BEM_COMPUTE,
computed into) the BEM voltage database via bem_voltage_bridge.py, then written
to the Zotino once. The DAC holds the voltages after the experiment ends.
"""

import logging

from artiq.experiment import *

try:
    from bem_voltage_bridge import (
        BEM_FREE_MULTIPOLES, BEM_MAX_VOLTAGE, BEM_PARAMETERS, NUM_DAC_CHANNELS,
        build_voltage_sets, fetch_voltage_dicts,
    )
except ImportError:
    from .bem_voltage_bridge import (
        BEM_FREE_MULTIPOLES, BEM_MAX_VOLTAGE, BEM_PARAMETERS, NUM_DAC_CHANNELS,
        build_voltage_sets, fetch_voltage_dicts,
    )

logger = logging.getLogger(__name__)

# =============================================================================
# USER INPUT - dashboard defaults (the dashboard remembers the last submitted values)
# =============================================================================
# name: (default, unit, step, GUI group). zl in um, ex/ey/ez in V/mm, u1..u5 in V/mm^2, max_voltage in V.
MULTIPOLE_ARGUMENTS = {
    "zl": (680.0, "um", 2.0, "Position"),
    "ex": (0.0, "V/mm", 0.1, "Fields"),
    "ey": (3.0, "V/mm", 0.1, "Fields"),
    "ez": (0.0, "V/mm", 0.1, "Fields"),
    "u1": (0.0, "V/mm^2", 0.1, "Curvatures"),
    "u2": (6.0, "V/mm^2", 0.1, "Curvatures"),
    "u3": (2.0, "V/mm^2", 0.1, "Curvatures"),  # (1/3) * u2
    "u4": (0.0, "V/mm^2", 0.1, "Curvatures"),
    "u5": (0.0, "V/mm^2", 0.1, "Curvatures"),
    "max_voltage": (49.5, "V", 0.5, "Solver"),
}
# =============================================================================

# The solver clips every electrode to +-max_voltage; an electrode at that limit
# means the requested multipoles were (very likely) not reached.
SATURATION_TOLERANCE = 1e-6


class ApplyGeneralMultipoles(EnvExperiment):
    """Apply General Multipoles"""

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")

        free_multipoles_default = {m.lower() for m in BEM_FREE_MULTIPOLES}
        for name, (default, unit, step, group) in MULTIPOLE_ARGUMENTS.items():
            tooltip = f"{name} ({unit})"
            if name in free_multipoles_default:
                tooltip += " - ignored by the solver while listed in free_multipoles"
            # scale=1.0: the value reaches the experiment in the displayed unit, as the database expects.
            self.setattr_argument(
                name,
                NumberValue(default=default, unit=unit, scale=1.0, step=step, precision=4),
                tooltip=tooltip,
                group=group,
            )

        self.setattr_argument(
            "free_multipoles",
            StringValue(default=", ".join(BEM_FREE_MULTIPOLES)),
            tooltip="Comma-separated free multipoles, e.g. 'U4, U5'",
            group="Solver",
        )
        self.setattr_argument(
            "trap_name",
            StringValue(default="gen3"),
            tooltip="Trap model name, e.g. 'gen3'",
            group="Trap",
        )
        self.setattr_argument(
            "resolution",
            StringValue(default="LOW"),
            tooltip="Mesh resolution: 'LOW', 'MEDIUM', or 'HIGH'",
            group="Trap",
        )

        self.channels = [i for i in range(NUM_DAC_CHANNELS)]

    def prepare(self):
        # Done here rather than in build() so that the ARTIQ repository scan does
        # not start the BEM env; errors are raised on submission.
        free_m = tuple(m.strip() for m in self.free_multipoles.split(",") if m.strip())
        self.multipoles = {
            "zl": float(self.zl),
            "ex": float(self.ex),
            "ey": float(self.ey),
            "ez": float(self.ez),
            "u1": float(self.u1),
            "u2": float(self.u2),
            "u3": float(self.u3),
            "u4": float(self.u4),
            "u5": float(self.u5),
            "max_voltage": float(self.max_voltage),
            "free_multipoles": free_m,
            "trap_name": str(self.trap_name).strip(),
            "resolution": str(self.resolution).strip().upper(),
        }
        logger.info("Requested parameters: %s", self.multipoles)

        for name in self.multipoles["free_multipoles"]:
            param_key = name.lower()
            if param_key in self.multipoles and self.multipoles[param_key] != 0.0:
                logger.warning(
                    "%s = %s is ignored by the solver (free_multipoles=%s).",
                    param_key, self.multipoles[param_key], self.multipoles["free_multipoles"],
                )

        # The bridge looks up "scans"; a single point is a one-value scan of any parameter.
        point_parameter = "zl"
        point_value = self.multipoles[point_parameter]
        fixed_parameters = {p: v for p, v in self.multipoles.items() if p != point_parameter}
        voltage_dicts = fetch_voltage_dicts(point_parameter, [point_value], fixed_parameters)
        self.dc_voltages = voltage_dicts[0]
        voltage_sets, _ = build_voltage_sets(voltage_dicts, [point_value], point_parameter)
        self.voltages = voltage_sets[0]

        max_v = self.multipoles["max_voltage"]
        saturated = {
            electrode: v for electrode, v in voltage_dicts[0].items()
            if abs(v) >= max_v - SATURATION_TOLERANCE
        }
        if saturated:
            raise ValueError(
                f"Electrodes {saturated} are at the +-{max_v} V solver limit (max_voltage), "
                "so the requested multipoles are most likely not reached. Nothing was applied."
            )
        logger.info("Electrode voltages (BEM, before DAC scaling): %s", voltage_dicts[0])
        logger.info("DAC voltages (channel 0..%d): %s", NUM_DAC_CHANNELS - 1, self.voltages)

    @kernel
    def apply_voltages(self):
        self.core.reset()
        self.zotino0.init()
        # set_dac issues 32 SPI writes; the CPU needs several ms of slack to queue them
        delay(10*ms)
        self.zotino0.set_dac(self.voltages, self.channels)
        # Do not return before the DAC has updated: the next experiment's core.reset()
        # would discard writes still queued in the RTIO FIFO.
        self.core.wait_until_mu(now_mu())

    def run(self):
        dc_voltage_text = ", ".join(
            f"{electrode}: {voltage:.8g} V"
            for electrode, voltage in self.dc_voltages.items()
        )
        logger.info("Applying DC voltages: {%s}", dc_voltage_text)
        self.apply_voltages()
        for name, value in self.multipoles.items():
            if isinstance(value, (int, float, bool, str)):
                self.set_dataset(f"applied_{name}", value)
            else:
                self.set_dataset(f"applied_{name}", str(value))
        self.set_dataset("applied_dac_voltages", self.voltages)
        logger.info("Applied DC solution for %s", self.multipoles)
