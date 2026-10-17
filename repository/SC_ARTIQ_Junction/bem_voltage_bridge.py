"""Shared scan-value generation and BEM voltage-database lookup for the
beam_waist_{397,866,729,854} and e{x,y,z}_scan experiments.

DC solutions are looked up in (and, if missing, computed into) the BEM voltage
database through SC_Batch_BEM/voltage_database_manipulation.py. That code needs
the BEM conda environment (bem, pyvista, ...), which the ARTIQ Python does not
have, so this file plays two roles:

1. Imported by ARTIQ experiments (ARTIQ Python): scan-value generation,
   build_scan_voltage_sets() and the shared BEM user input below. The lookup
   runs this same file as a subprocess in the BEM Python.
2. Executed by the BEM conda Python (main() below):

       python bem_voltage_bridge.py <request.json> <result.json>

   The request JSON is written by fetch_voltage_dicts. The result JSON is
   {"entries": [{"key": [zl, ex, ey, ez, u1, u2, u3, u4, u5],
   "voltages": {"DC1": V, ...}}, ...]}.

Only stdlib imports at module level: ARTIQ imports every file in the repository
when scanning for experiments, and Windows multiprocessing (used by the BEM field
calculation) re-imports this file in each worker process. Keep it compatible with
both the ARTIQ Python (3.11) and the BEM Python (3.9).
"""

import json
import logging
import math
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

# =============================================================================
# USER INPUT - BEM voltage database (shared by every scan)
# =============================================================================
# Python of the conda env that can import bem_voltage_streamlined (bem, pyvista, ...).
BEM_PYTHON_EXE = r"C:\Users\artiq\.conda\envs\bem39\python.exe"
# Folder holding voltage_database_manipulation.py, BEM_Voltage_Cache/ and BEM_Field_Cache/.
BEM_CODE_DIR = Path(__file__).resolve().parent.parent / "SC_Batch_BEM"
BEM_SPECIALIZED_CLASS = "Gen3"  # Class name in bem_voltage_streamlined.py
BEM_TRAP_NAME = "gen3"
BEM_RESOLUTION = "LOW"  # "LOW" or "HIGH" (member of bem_voltage_streamlined.Resolution)
BEM_STL_FILENAME = "gen3_flattened.stl"  # Relative to BEM_CODE_DIR
BEM_MAX_VOLTAGE = 9.9 * 5
BEM_FREE_MULTIPOLES = ("U4", "U5")

# False: refuse to submit if any requested point is not already in the database.
# True: missing points are computed by BEM and appended to the database. A zl value
# without a field cache (BEM_Field_Cache/) takes minutes to compute.
ALLOW_BEM_COMPUTE = True
BEM_TIMEOUT_S = 2 * 3600

# Seed for SCAN_ORDERING == "random". None gives a different order on every submission.
RANDOM_SEED = None
# =============================================================================


# =============================================================================
# Internal constants (not user input)
# =============================================================================
# Same "temporary" scaling that pulse_dds.py applies to the DC dictionaries.
DC_SCALE_FACTOR = 1.0 / 5.0
DC_CLAMP_V = 9.9 * 5       # Same clamp as pulse_dds.py
NUM_DC_ELECTRODES = 21
NUM_DAC_CHANNELS = 32

# Key order of the voltage database: (zl, ex, ey, ez, u1, u2, u3, u4, u5).
BEM_PARAMETERS = ("zl", "ex", "ey", "ez", "u1", "u2", "u3", "u4", "u5")
# Any permutation of BEM_PARAMETERS is valid here because only one parameter varies.
BEM_SCAN_ORDER = ["zl", "u5", "u4", "u3", "u2", "u1", "ez", "ex", "ey"]
SCAN_ORDERINGS = ("linear", "outwards", "random")
# batch_bem_voltage rounds range values to 12 digits; database keys only match if we do too.
VALUE_ROUND_DIGITS = 12
BRIDGE_SCRIPT = Path(__file__).resolve()
# The BEM code calls IPython's clear_output, which prints terminal escape codes.
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

EXIT_USAGE = 2
EXIT_MISSING_ENTRIES = 3
REQUIRED_REQUEST_KEYS = (
    "bem_code_dir", "specialized_class", "trap_name", "resolution", "stl_filename",
    "max_voltage", "free_multipoles", "scan_order", "allow_compute", "parameter_values",
)


# =============================================================================
# Scan values
# =============================================================================
def _as_value(value: object, name: str) -> float:
    """Validate a user-supplied number and round it the same way the database keys are."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {value!r} ({type(value).__name__}).")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}.")
    # "+ 0.0" turns -0.0 into 0.0 so datasets and log messages never show "-0.0".
    return round(float(value), VALUE_ROUND_DIGITS) + 0.0


def make_linear_values(start: float, stop: float, step: float, name: str) -> list[float]:
    """Inclusive ascending range, identical to batch_bem_voltage.make_linear_range."""
    start = _as_value(start, f"{name} start")
    stop = _as_value(stop, f"{name} stop")
    step = _as_value(step, f"{name} step")
    if step <= 0:
        raise ValueError(f"{name} step must be positive, got {step}.")
    if stop < start:
        raise ValueError(f"{name} stop ({stop}) must be >= start ({start}).")

    step_count = (stop - start) / step
    n_steps = round(step_count)
    if not math.isclose(step_count, n_steps, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{name} step ({step}) must divide the range [{start}, {stop}] exactly.")
    return [_as_value(start + i * step, name) for i in range(n_steps + 1)]


def make_outward_values(values: Sequence[float]) -> list[float]:
    """Reorder ascending values to start at the middle of the range and alternate outwards.

    Same ordering as batch_bem_voltage.make_outward_range (e.g. zl = 650..710 starts at 680).
    """
    if len(values) == 0:
        return []
    mid_val = (values[0] + values[-1]) / 2.0
    mid_idx = min(range(len(values)), key=lambda i: abs(values[i] - mid_val))

    ordered = [values[mid_idx]]
    lo, hi = mid_idx - 1, mid_idx + 1
    while lo >= 0 or hi < len(values):
        if lo >= 0:
            ordered.append(values[lo])
            lo -= 1
        if hi < len(values):
            ordered.append(values[hi])
            hi += 1
    return ordered


def build_scan_values(
    name: str,
    scan_ordering: str,
    start: float,
    stop: float,
    step: float,
    random_seed: Optional[int] = None,
) -> list[float]:
    """Return the scanned values in the order they will be applied to the ion.

    name is only used in error messages (e.g. "ZL_*_UM").
    """
    if scan_ordering not in SCAN_ORDERINGS:
        raise ValueError(
            f"SCAN_ORDERING must be one of {list(SCAN_ORDERINGS)}, got {scan_ordering!r}."
        )

    values = make_linear_values(start, stop, step, name)
    if scan_ordering == "outwards":
        return make_outward_values(values)
    if scan_ordering == "random":
        random.Random(random_seed).shuffle(values)
    return values


# =============================================================================
# BEM voltage database lookup (ARTIQ side)
# =============================================================================
def _bem_subprocess_env() -> dict[str, str]:
    """Environment for the BEM conda Python, equivalent to activating the env."""
    env = os.environ.copy()
    # ARTIQ's (MSYS2) Python settings must not leak into the conda interpreter.
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "utf-8"

    env_root = Path(BEM_PYTHON_EXE).parent
    dll_dirs = [
        env_root,
        env_root / "Library" / "mingw-w64" / "bin",
        env_root / "Library" / "usr" / "bin",
        env_root / "Library" / "bin",
        env_root / "Scripts",
    ]
    env["PATH"] = os.pathsep.join([str(d) for d in dll_dirs] + [env.get("PATH", "")])
    return env


def fetch_voltage_dicts(
    scan_parameter: str,
    scan_values: Sequence[float],
    fixed_parameters: Mapping[str, float],
) -> list[dict[str, float]]:
    """Return one {"DC1": V, ..., "DC21": V} dict per scan value, in scan_values order.

    Runs this file's main() in the BEM conda env, which calls
    voltage_database_manipulation.search_and_fill. Points missing from the database
    are computed and appended (if ALLOW_BEM_COMPUTE).
    """
    if scan_parameter not in BEM_PARAMETERS:
        raise ValueError(f"scan_parameter must be one of {list(BEM_PARAMETERS)}, got {scan_parameter!r}.")
    if len(scan_values) == 0:
        raise ValueError("No scan values to look up.")

    expected_fixed = set(BEM_PARAMETERS) - {scan_parameter}
    if set(fixed_parameters) != expected_fixed:
        missing = sorted(expected_fixed - set(fixed_parameters))
        extra = sorted(set(fixed_parameters) - expected_fixed)
        raise ValueError(
            f"FIXED_PARAMETERS must contain exactly {sorted(expected_fixed)} "
            f"(the scanned {scan_parameter!r} is excluded). Missing: {missing}, extra: {extra}."
        )
    fixed = {p: _as_value(v, f"FIXED_PARAMETERS[{p!r}]") for p, v in fixed_parameters.items()}
    scan = [_as_value(v, scan_parameter) for v in scan_values]

    bem_python = Path(BEM_PYTHON_EXE)
    bem_dir = Path(BEM_CODE_DIR)
    if not bem_python.is_file():
        raise FileNotFoundError(f"BEM_PYTHON_EXE not found: {bem_python}")
    if not (bem_dir / "voltage_database_manipulation.py").is_file():
        raise FileNotFoundError(f"voltage_database_manipulation.py not found in BEM_CODE_DIR: {bem_dir}")

    parameter_values = {p: ([fixed[p]] if p != scan_parameter else scan) for p in BEM_PARAMETERS}
    request = {
        "bem_code_dir": str(bem_dir.resolve()),
        "specialized_class": BEM_SPECIALIZED_CLASS,
        "trap_name": BEM_TRAP_NAME,
        "resolution": BEM_RESOLUTION,
        "stl_filename": BEM_STL_FILENAME,
        "max_voltage": float(BEM_MAX_VOLTAGE),
        "free_multipoles": list(BEM_FREE_MULTIPOLES),
        "scan_order": BEM_SCAN_ORDER,
        "allow_compute": bool(ALLOW_BEM_COMPUTE),
        "parameter_values": parameter_values,
    }

    with tempfile.TemporaryDirectory(prefix="bem_voltage_request_") as tmp_dir:
        request_path = Path(tmp_dir) / "request.json"
        result_path = Path(tmp_dir) / "result.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")

        try:
            completed = subprocess.run(
                [str(bem_python), str(BRIDGE_SCRIPT), str(request_path), str(result_path)],
                cwd=str(bem_dir),
                env=_bem_subprocess_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=BEM_TIMEOUT_S,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"BEM voltage lookup timed out after {BEM_TIMEOUT_S} s (BEM_TIMEOUT_S)."
            ) from exc

        stdout = ANSI_ESCAPE.sub("", completed.stdout)
        stderr = ANSI_ESCAPE.sub("", completed.stderr)
        for line in stdout.splitlines():
            if line.strip():
                logger.info("[BEM] %s", line.strip())
        if completed.returncode != 0:
            raise RuntimeError(
                f"BEM voltage lookup failed (exit code {completed.returncode}):\n"
                f"{stderr.strip() or stdout.strip()}"
            )
        if not result_path.is_file():
            raise RuntimeError("BEM voltage lookup finished without writing a result file.")
        result = json.loads(result_path.read_text(encoding="utf-8"))

    lookup = {tuple(float(x) for x in entry["key"]): entry["voltages"] for entry in result["entries"]}
    voltage_dicts = []
    for value in scan:
        key = tuple(value if p == scan_parameter else fixed[p] for p in BEM_PARAMETERS)
        if key not in lookup:
            raise RuntimeError(f"BEM result is missing {dict(zip(BEM_PARAMETERS, key))}.")
        voltage_dicts.append({name: float(v) for name, v in lookup[key].items()})
    return voltage_dicts


# =============================================================================
# DAC voltage sets
# =============================================================================
def build_voltage_sets(
    voltage_dicts: Sequence[Mapping[str, float]],
    x_values: Sequence[float],
    x_name: str,
) -> tuple[list[list[float]], list[float]]:
    """Validate DC dicts and convert them into 32-channel Zotino lists.

    x_values is the scanned x-axis value for each DC solution; x_name is only
    used in error messages.

    Returns (voltage_sets, x_values_as_floats).
    """
    x_values = [float(x) for x in x_values]

    if len(voltage_dicts) == 0:
        raise ValueError("No DC solutions; provide at least one.")
    if len(x_values) == 0:
        raise ValueError(f"{x_name} is empty; provide one value per DC solution.")
    if len(voltage_dicts) != len(x_values):
        raise ValueError(
            f"Size mismatch: {len(voltage_dicts)} DC solutions but {len(x_values)} values "
            f"in {x_name}. Provide exactly one value per DC solution."
        )
    if len(set(x_values)) != len(x_values):
        raise ValueError(f"{x_name} contains duplicate values.")

    expected_keys = [f"DC{i}" for i in range(1, NUM_DC_ELECTRODES + 1)]
    voltage_sets = []
    for idx, voltage_dict in enumerate(voltage_dicts):
        if not isinstance(voltage_dict, Mapping):
            raise ValueError(f"DC solution {idx} is not a dict.")
        missing = [k for k in expected_keys if k not in voltage_dict]
        extra = [k for k in voltage_dict if k not in expected_keys]
        if missing:
            raise ValueError(f"DC solution {idx} is missing electrodes: {missing}")
        if extra:
            raise ValueError(f"DC solution {idx} has unknown electrodes: {extra}")

        voltages = []
        for key in expected_keys:
            v = voltage_dict[key] * DC_SCALE_FACTOR
            v = max(-DC_CLAMP_V, min(DC_CLAMP_V, v))
            voltages.append(round(v, 8))
        # Fixed channels, same as pulse_dds.py
        voltages.extend([1.0, 1.1, 0.0])
        voltages.extend([0.0] * (NUM_DAC_CHANNELS - len(voltages)))
        voltage_sets.append(voltages)
    return voltage_sets, x_values


def build_scan_voltage_sets(
    scan_parameter: str,
    scan_ordering: str,
    start: float,
    stop: float,
    step: float,
    fixed_parameters: Mapping[str, float],
    x_name: str,
) -> tuple[list[list[float]], list[float]]:
    """Scan values -> BEM database lookup -> 32-channel voltage sets.

    Call from prepare(), not build(): it starts the BEM env (several seconds, or
    minutes if points must be computed), and build() also runs on every
    repository scan.

    Returns (voltage_sets, scan_values) in scan order.
    """
    scan_values = build_scan_values(x_name, scan_ordering, start, stop, step, RANDOM_SEED)
    logger.info(
        "%s scan (%s ordering, %d points): %s", scan_parameter, scan_ordering, len(scan_values), scan_values
    )
    logger.info("Fixed parameters: %s", dict(fixed_parameters))
    voltage_dicts = fetch_voltage_dicts(scan_parameter, scan_values, fixed_parameters)
    return build_voltage_sets(voltage_dicts, scan_values, x_name)


# =============================================================================
# BEM side: runs under the BEM conda Python
# =============================================================================
def main(argv: list) -> int:
    """Look up (and if allowed, compute) the requested voltages; write them as JSON."""
    if len(argv) != 3:
        print(f"Usage: {Path(argv[0]).name} <request.json> <result.json>", file=sys.stderr)
        return EXIT_USAGE
    request_path, result_path = Path(argv[1]), Path(argv[2])
    request = json.loads(request_path.read_text(encoding="utf-8"))
    missing_keys = [k for k in REQUIRED_REQUEST_KEYS if k not in request]
    if missing_keys:
        print(f"Request is missing keys: {missing_keys}", file=sys.stderr)
        return EXIT_USAGE

    # The BEM code uses paths relative to its own folder (BEM_Voltage_Cache/, BEM_Field_Cache/).
    bem_dir = Path(request["bem_code_dir"]).resolve()
    if not bem_dir.is_dir():
        print(f"bem_code_dir does not exist: {bem_dir}", file=sys.stderr)
        return EXIT_USAGE
    os.chdir(str(bem_dir))
    sys.path.insert(0, str(bem_dir))

    import bem_voltage_streamlined
    from batch_bem_voltage import VALID_PARAMS, _ordered_keys, database_path, load_database
    from voltage_database_manipulation import search_and_fill

    try:
        resolution = bem_voltage_streamlined.Resolution[request["resolution"]]
    except KeyError:
        valid = [r.name for r in bem_voltage_streamlined.Resolution]
        print(f"Unknown resolution {request['resolution']!r}; valid: {valid}", file=sys.stderr)
        return EXIT_USAGE
    specialized_cls = getattr(bem_voltage_streamlined, request["specialized_class"], None)
    if specialized_cls is None:
        print(f"bem_voltage_streamlined has no class {request['specialized_class']!r}", file=sys.stderr)
        return EXIT_USAGE

    stl_path = bem_dir / request["stl_filename"]
    if not stl_path.is_file():
        print(f"STL file not found: {stl_path}", file=sys.stderr)
        return EXIT_USAGE

    parameter_values = request["parameter_values"]
    if set(parameter_values) != set(VALID_PARAMS):
        print(f"parameter_values must contain exactly {list(VALID_PARAMS)}", file=sys.stderr)
        return EXIT_USAGE
    values = {p: [float(v) for v in parameter_values[p]] for p in VALID_PARAMS}
    scan_order = list(request["scan_order"])
    trap_name = str(request["trap_name"])

    if not request["allow_compute"]:
        database = load_database(database_path(trap_name, resolution))
        missing = [k for k in _ordered_keys(scan_order, values) if k not in database]
        if missing:
            print(
                f"{len(missing)} requested point(s) are not in the voltage database and "
                "ALLOW_BEM_COMPUTE is False. Missing (zl, ex, ey, ez, u1, u2, u3, u4, u5):",
                file=sys.stderr,
            )
            for key in missing:
                print(f"  {key}", file=sys.stderr)
            return EXIT_MISSING_ENTRIES

    result = search_and_fill(
        specialized_cls=specialized_cls,
        stl_path=stl_path,
        resolution=resolution,
        zl_vals=values["zl"],
        ex_vals=values["ex"],
        ey_vals=values["ey"],
        ez_vals=values["ez"],
        u1_vals=values["u1"],
        u2_vals=values["u2"],
        u3_vals=values["u3"],
        u4_vals=values["u4"],
        u5_vals=values["u5"],
        max_voltage=float(request["max_voltage"]),
        free_multipoles=tuple(request["free_multipoles"]),
        scan_order=scan_order,
        trap_name=trap_name,
        verbose=1,
    )

    # Database voltages are numpy.float64; convert so the JSON holds plain floats.
    entries = [
        {"key": [float(x) for x in key], "voltages": {name: float(v) for name, v in voltages.items()}}
        for key, voltages in result.items()
    ]
    result_path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
