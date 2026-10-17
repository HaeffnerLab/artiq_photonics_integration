"""zl scan user input shared by beam_waist_{397,866,729,854}.py.

Scan-value generation, the BEM voltage-database lookup and the shared BEM settings
(BEM_PYTHON_EXE, ALLOW_BEM_COMPUTE, RANDOM_SEED, ...) live in bem_voltage_bridge.py,
which is also used by e{x,y,z}_scan.py. Keep both files in the same ARTIQ
repository folder.
"""

try:
    from bem_voltage_bridge import NUM_DAC_CHANNELS, build_scan_voltage_sets
except ImportError:
    from .bem_voltage_bridge import NUM_DAC_CHANNELS, build_scan_voltage_sets

# =============================================================================
# USER INPUT - zl scan used by beam_waist_{397,866,729,854}.py
# =============================================================================
# "linear"   : ZL_START_UM -> ZL_STOP_UM in ascending ZL_STEP_UM increments
# "outwards" : same values, starting at the middle of the range and alternating outwards
# "random"   : same values, shuffled (RANDOM_SEED in bem_voltage_bridge.py)
SCAN_ORDERING = "linear"

# Ion axial position zl (um). Inclusive on both ends; step must divide the range.
ZL_START_UM = 670.0
ZL_STOP_UM = 690.0
ZL_STEP_UM = 2.0

# Fixed parameters, held constant during the zl scan. ex/ey/ez in V/mm, u1..u5 in V/mm^2.
FIXED_PARAMETERS = {
    "ex": 0.0,
    "ey": 3.0,
    "ez": 0.0,
    "u1": 0.0,
    "u2": 6.0,
    "u3": 2.0,  # (1/3) * u2
    "u4": 0.0,
    "u5": 0.0,
}
# =============================================================================


def build_zl_voltage_sets() -> tuple[list[list[float]], list[float]]:
    """build_scan_voltage_sets for the zl USER INPUT above."""
    return build_scan_voltage_sets(
        "zl", SCAN_ORDERING, ZL_START_UM, ZL_STOP_UM, ZL_STEP_UM,
        FIXED_PARAMETERS, x_name="ZL_*_UM",
    )
