from __future__ import annotations

import argparse
import binascii
import csv
import json
import math
import subprocess
import struct
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np


LIMITATION_TEXT = (
    "This stimulus is not a recovery of the original raw analog ECG. The source "
    "record is already digitized ECG data. This tool reconstructs the physical "
    "voltage represented by the WFDB/CSV samples, then applies a DAC replay "
    "reconstruction model to create an analog-equivalent XMODEL input stimulus."
)

DAC_MODES = ("zoh", "linear", "pchip", "cubic", "bandlimited")
UNIT_ALIASES = {
    "v": "V",
    "volt": "V",
    "volts": "V",
    "mv": "mV",
    "millivolt": "mV",
    "millivolts": "mV",
    "uv": "uV",
    "microv": "uV",
    "microvolt": "uV",
    "microvolts": "uV",
    "microvolt(s)": "uV",
    "": "mV",
}
UNIT_SCALE_TO_V = {"V": 1.0, "mV": 1.0e-3, "uV": 1.0e-6}


@dataclass
class WarningRecord:
    code: str
    message: str
    severity: str = "warning"

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass
class InputSignal:
    path: Path
    input_kind: str
    time_s: np.ndarray
    values: np.ndarray
    source_fs_hz: float
    units: list[str]
    channel_names: list[str]
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class StimulusResult:
    out_dir: Path
    stimulus_csv: Path
    stimulus_pwl: Path
    metadata_json: Path
    qa_plot: Path
    readme: Path
    metadata: dict[str, object]


def normalize_unit(unit: str | None) -> str:
    if unit is None:
        return "mV"
    cleaned = unit.strip().replace("micro", "u").replace("\u00b5", "u")
    return UNIT_ALIASES.get(cleaned.lower(), cleaned)


def unit_scale_to_volts(unit: str) -> float:
    normalized = normalize_unit(unit)
    if normalized not in UNIT_SCALE_TO_V:
        raise ValueError(f"unsupported unit {unit!r}; expected V, mV, or uV")
    return UNIT_SCALE_TO_V[normalized]


def add_warning(warnings: list[WarningRecord], code: str, message: str, severity: str = "warning") -> None:
    record = WarningRecord(code=code, message=message, severity=severity)
    warnings.append(record)
    print(f"[{severity}] {code}: {message}", file=sys.stderr)


def parse_col_selector(selector: str | None, headers: Sequence[str], default: int | None = None) -> int | None:
    if selector is None:
        return default
    stripped = selector.strip()
    if stripped == "":
        return default
    if stripped.lstrip("+-").isdigit():
        idx = int(stripped)
        if idx < 0:
            idx += len(headers)
        if idx < 0 or idx >= len(headers):
            raise ValueError(f"column index {selector!r} is outside 0..{len(headers) - 1}")
        return idx
    lowered = [h.strip().lower() for h in headers]
    key = stripped.lower()
    if key not in lowered:
        raise ValueError(f"column {selector!r} not found; available columns: {', '.join(headers)}")
    return lowered.index(key)


def infer_csv_unit(column_name: str, requested_units: str, warnings: list[WarningRecord]) -> str:
    requested = normalize_unit(requested_units)
    if requested != "auto":
        return requested

    lowered = column_name.lower()
    if lowered.endswith("_v") or lowered in {"v", "volt", "voltage_v", "vin_v"} or "(v)" in lowered:
        return "V"
    if "uv" in lowered or "microv" in lowered or "microvolt" in lowered:
        return "uV"
    if "mv" in lowered or "millivolt" in lowered:
        return "mV"

    add_warning(
        warnings,
        "CSV_UNITS_ASSUMED_MV",
        f"CSV units were not explicit for column {column_name!r}; assuming mV. Pass --input-units to override.",
    )
    return "mV"


def looks_like_header(row: Sequence[str]) -> bool:
    for value in row:
        try:
            float(value)
        except ValueError:
            return True
    return False


def load_csv_signal(path: Path, args: argparse.Namespace, warnings: list[WarningRecord]) -> InputSignal:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise ValueError(f"CSV file is empty: {path}")

    has_header = looks_like_header(rows[0])
    if has_header:
        headers = [h.strip() or f"col_{idx}" for idx, h in enumerate(rows[0])]
        data_rows = rows[1:]
    else:
        headers = [f"col_{idx}" for idx in range(len(rows[0]))]
        data_rows = rows

    if not data_rows:
        raise ValueError(f"CSV file has no data rows: {path}")

    width = len(headers)
    matrix: list[list[float]] = []
    for line_no, row in enumerate(data_rows, start=2 if has_header else 1):
        if len(row) != width:
            raise ValueError(f"CSV row {line_no} has {len(row)} fields, expected {width}")
        parsed: list[float] = []
        for value in row:
            stripped = value.strip()
            if stripped == "":
                parsed.append(float("nan"))
            else:
                try:
                    parsed.append(float(stripped))
                except ValueError:
                    parsed.append(float("nan"))
        matrix.append(parsed)

    arr = np.asarray(matrix, dtype=float)

    time_idx = parse_col_selector(args.time_col, headers)
    if time_idx is None:
        time_candidates = [i for i, h in enumerate(headers) if h.lower() in {"time", "time_s", "t", "seconds", "sec"}]
        time_idx = time_candidates[0] if time_candidates else None

    if time_idx is not None:
        time_s = arr[:, time_idx].astype(float)
        finite_time = np.isfinite(time_s)
        if not finite_time.all():
            raise ValueError("CSV time column contains blank, NaN, or non-numeric values")
        dt = np.diff(time_s)
        if len(dt) == 0 or np.any(dt <= 0):
            raise ValueError("CSV time column must be strictly increasing")
        median_dt = float(np.median(dt))
        if median_dt <= 0:
            raise ValueError("CSV time column has invalid spacing")
        source_fs_hz = 1.0 / median_dt
        if np.max(np.abs(dt - median_dt)) / median_dt > 1.0e-3:
            add_warning(
                warnings,
                "IRREGULAR_CSV_TIME",
                "CSV time spacing is not uniform; interpolation will use the supplied timestamps.",
            )
    else:
        if args.fs is None:
            raise ValueError("CSV input without --time-col requires --fs")
        source_fs_hz = float(args.fs)
        if source_fs_hz <= 0:
            raise ValueError("--fs must be positive")
        time_s = np.arange(arr.shape[0], dtype=float) / source_fs_hz

    numeric_indices = [i for i in range(width) if i != time_idx]
    value_idx = parse_col_selector(args.value_col, headers)
    if value_idx is not None and value_idx == time_idx:
        raise ValueError("--value-col cannot be the same as --time-col")

    if value_idx is not None:
        selected_indices = [value_idx]
    else:
        selected_indices = numeric_indices

    if not selected_indices:
        raise ValueError("CSV input has no numeric value columns")
    channel_names = [headers[i] for i in selected_indices]
    units = [infer_csv_unit(name, args.input_units, warnings) for name in channel_names]
    values = arr[:, selected_indices].astype(float)

    return InputSignal(
        path=path,
        input_kind="csv",
        time_s=time_s,
        values=values,
        source_fs_hz=source_fs_hz,
        units=units,
        channel_names=channel_names,
        metadata={
            "csv_has_header": has_header,
            "csv_time_column": headers[time_idx] if time_idx is not None else None,
            "csv_value_column": headers[value_idx] if value_idx is not None else None,
        },
    )


@dataclass
class WfdbSignalInfo:
    file_name: str
    fmt: str
    samples_per_frame: int
    skew: int
    byte_offset: int
    gain: float
    baseline: int | None
    adc_zero: int
    units: str
    description: str
    gain_assumed: bool = False


def parse_wfdb_gain_units(token: str) -> tuple[float, int | None, str]:
    gain_part = token
    units = "mV"
    if "/" in gain_part:
        gain_part, units = gain_part.split("/", 1)
    baseline: int | None = None
    if "(" in gain_part and ")" in gain_part:
        before, after = gain_part.split("(", 1)
        baseline_text = after.split(")", 1)[0].strip()
        gain_part = before
        if baseline_text:
            baseline = int(float(baseline_text))
    gain = float(gain_part) if gain_part else 200.0
    return gain, baseline, normalize_unit(units)


def parse_wfdb_format_token(token: str) -> tuple[str, int, int, int]:
    main = token
    byte_offset = 0
    skew = 0
    samples_per_frame = 1

    if "+" in main:
        main, offset_text = main.split("+", 1)
        byte_offset = int(offset_text) if offset_text else 0
    if ":" in main:
        main, skew_text = main.split(":", 1)
        skew = int(skew_text) if skew_text else 0
    if "x" in main.lower():
        fmt_text, spf_text = main.lower().split("x", 1)
        main = fmt_text
        samples_per_frame = int(spf_text) if spf_text else 1
    return main, samples_per_frame, skew, byte_offset


def parse_wfdb_header(path: Path, warnings: list[WarningRecord]) -> tuple[float, int | None, list[WfdbSignalInfo]]:
    header_path = path if path.suffix.lower() == ".hea" else path.with_suffix(".hea")
    lines = [
        line.strip()
        for line in header_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        raise ValueError(f"empty WFDB header: {header_path}")
    first = lines[0].split()
    if len(first) < 3:
        raise ValueError(f"invalid WFDB record line in {header_path}")
    try:
        nsig = int(first[1])
        fs = float(first[2].split("/")[0])
        nsamp = int(first[3]) if len(first) >= 4 and first[3].isdigit() else None
    except ValueError as exc:
        raise ValueError(f"invalid WFDB record metadata in {header_path}") from exc
    if len(lines) < 1 + nsig:
        raise ValueError(f"WFDB header has {len(lines) - 1} signal lines, expected {nsig}")

    signals: list[WfdbSignalInfo] = []
    for idx, line in enumerate(lines[1 : 1 + nsig]):
        fields = line.split()
        if len(fields) < 2:
            raise ValueError(f"invalid WFDB signal line {idx + 2}: {line}")
        file_name = fields[0]
        fmt, samples_per_frame, skew, byte_offset = parse_wfdb_format_token(fields[1])
        gain = 200.0
        baseline = None
        units = "mV"
        gain_assumed = False
        if len(fields) >= 3:
            try:
                gain, baseline, units = parse_wfdb_gain_units(fields[2])
            except ValueError:
                gain_assumed = True
                add_warning(
                    warnings,
                    "WFDB_GAIN_ASSUMED",
                    f"Could not parse gain/units token {fields[2]!r}; assuming 200 ADC units per mV.",
                )
        else:
            gain_assumed = True
            add_warning(
                warnings,
                "WFDB_GAIN_ASSUMED",
                "WFDB ADC gain is missing; signal amplitude is uncalibrated. Assuming 200 ADC units per mV.",
                severity="strong-warning",
            )
        if gain == 0:
            gain_assumed = True
            add_warning(warnings, "WFDB_GAIN_ASSUMED", "WFDB gain was zero; assuming 200 ADC units per mV.")
            gain = 200.0
        adc_zero = int(float(fields[4])) if len(fields) >= 5 else 0
        description = " ".join(fields[8:]) if len(fields) >= 9 else f"signal_{idx}"
        signals.append(
            WfdbSignalInfo(
                file_name=file_name,
                fmt=fmt,
                samples_per_frame=samples_per_frame,
                skew=skew,
                byte_offset=byte_offset,
                gain=gain,
                baseline=baseline,
                adc_zero=adc_zero,
                units=units,
                description=description,
                gain_assumed=gain_assumed,
            )
        )
    return fs, nsamp, signals


def read_format16(path: Path, nsig: int, nsamp: int | None) -> np.ndarray:
    raw = np.frombuffer(path.read_bytes(), dtype="<i2")
    usable = (raw.size // nsig) * nsig
    raw = raw[:usable]
    data = raw.reshape((-1, nsig))
    if nsamp is not None:
        data = data[:nsamp]
    return data.astype(float)


def read_format212(path: Path, nsig: int, nsamp: int | None) -> np.ndarray:
    raw = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    usable = (raw.size // 3) * 3
    raw = raw[:usable].reshape((-1, 3))
    s0 = raw[:, 0].astype(np.int16) | ((raw[:, 1].astype(np.int16) & 0x0F) << 8)
    s1 = raw[:, 2].astype(np.int16) | ((raw[:, 1].astype(np.int16) & 0xF0) << 4)
    samples = np.empty(raw.shape[0] * 2, dtype=np.int16)
    samples[0::2] = s0
    samples[1::2] = s1
    samples = np.where(samples >= 2048, samples - 4096, samples).astype(float)
    usable_samples = (samples.size // nsig) * nsig
    data = samples[:usable_samples].reshape((-1, nsig))
    if nsamp is not None:
        data = data[:nsamp]
    return data


def wfdb_record_base(path: Path) -> str:
    if path.suffix.lower() in {".hea", ".dat"}:
        return str(path.with_suffix(""))
    return str(path)


def load_wfdb_with_package(path: Path, args: argparse.Namespace) -> InputSignal | None:
    try:
        import wfdb  # type: ignore
    except ImportError:
        return None

    record_name = wfdb_record_base(path)
    header = wfdb.rdheader(record_name)
    signals, fields = wfdb.rdsamp(record_name)
    values = np.asarray(signals, dtype=float)
    fs = float(fields.get("fs", header.fs))
    units = fields.get("units", ["mV"])
    sig_name = fields.get("sig_name", getattr(header, "sig_name", []))
    time_s = np.arange(values.shape[0], dtype=float) / fs
    return InputSignal(
        path=path,
        input_kind="wfdb",
        time_s=time_s,
        values=values,
        source_fs_hz=fs,
        units=[normalize_unit(unit) for unit in units] if units else ["mV"] * values.shape[1],
        channel_names=list(sig_name) if sig_name else [f"channel_{idx}" for idx in range(values.shape[1])],
        metadata={"wfdb_reader": "python_wfdb", "record_name": record_name},
    )


def load_wfdb_internal(path: Path, args: argparse.Namespace, warnings: list[WarningRecord]) -> InputSignal:
    fs, nsamp, signals = parse_wfdb_header(path, warnings)
    if not signals:
        raise ValueError("WFDB header contains no signals")
    dat_names = {sig.file_name for sig in signals}
    fmts = {sig.fmt for sig in signals}
    if len(dat_names) != 1 or len(fmts) != 1:
        raise ValueError("internal WFDB reader only supports one shared .dat file and one format")
    unsupported = [
        sig
        for sig in signals
        if sig.samples_per_frame != 1 or sig.skew != 0 or sig.byte_offset != 0
    ]
    if unsupported:
        raise ValueError(
            "internal WFDB reader does not support samples-per-frame, skew, or byte offset modifiers; "
            "install the wfdb package for full WFDB support"
        )
    fmt = next(iter(fmts))
    if fmt not in {"16", "212"}:
        raise ValueError(f"internal WFDB reader supports formats 16 and 212 only; got format {fmt}")

    dat_path = path.parent / next(iter(dat_names))
    if not dat_path.exists():
        raise FileNotFoundError(dat_path)
    if fmt == "16":
        digital = read_format16(dat_path, len(signals), nsamp)
    else:
        digital = read_format212(dat_path, len(signals), nsamp)

    physical = np.empty_like(digital, dtype=float)
    units: list[str] = []
    names: list[str] = []
    wfdb_meta: list[dict[str, object]] = []
    for idx, sig in enumerate(signals):
        zero = sig.baseline if sig.baseline is not None else sig.adc_zero
        physical[:, idx] = (digital[:, idx] - zero) / sig.gain
        units.append(normalize_unit(sig.units))
        names.append(sig.description or f"channel_{idx}")
        wfdb_meta.append(
            {
                "file": sig.file_name,
                "format": sig.fmt,
                "gain_adc_units_per_physical_unit": sig.gain,
                "baseline": sig.baseline,
                "adc_zero": sig.adc_zero,
                "units": sig.units,
                "description": sig.description,
                "gain_assumed": sig.gain_assumed,
                "samples_per_frame": sig.samples_per_frame,
                "skew": sig.skew,
                "byte_offset": sig.byte_offset,
            }
        )
    time_s = np.arange(physical.shape[0], dtype=float) / fs
    add_warning(
        warnings,
        "WFDB_INTERNAL_LIMITED",
        "wfdb package is not installed; using limited internal WFDB reader for formats 16/212 only.",
    )
    return InputSignal(
        path=path,
        input_kind="wfdb",
        time_s=time_s,
        values=physical,
        source_fs_hz=fs,
        units=units,
        channel_names=names,
        metadata={
            "wfdb_reader": "internal_limited",
            "wfdb_limitations": [
                "single-segment only",
                "formats 16 and 212 only",
                "no skew, byte offset, FLAC, or multi-segment support",
            ],
            "wfdb_signals": wfdb_meta,
        },
    )


def load_wfdb_signal(path: Path, args: argparse.Namespace, warnings: list[WarningRecord]) -> InputSignal:
    package_loaded = load_wfdb_with_package(path, args)
    if package_loaded is not None:
        return package_loaded
    return load_wfdb_internal(path, args, warnings)


def load_input_signal(path: Path, args: argparse.Namespace, warnings: list[WarningRecord]) -> InputSignal:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv_signal(path, args, warnings)
    if suffix in {".hea", ".dat"} or path.with_suffix(".hea").exists():
        return load_wfdb_signal(path, args, warnings)
    raise ValueError(f"unsupported input type {suffix!r}; expected CSV or WFDB .hea/.dat record")


def select_channel(signal: InputSignal, channel: str | int) -> int:
    if isinstance(channel, int) or str(channel).lstrip("+-").isdigit():
        idx = int(channel)
        if idx < 0:
            idx += signal.values.shape[1]
        if idx < 0 or idx >= signal.values.shape[1]:
            raise ValueError(f"channel index {channel!r} outside 0..{signal.values.shape[1] - 1}")
        return idx
    lowered = [name.lower() for name in signal.channel_names]
    key = str(channel).lower()
    if key not in lowered:
        raise ValueError(f"channel {channel!r} not found; available channels: {', '.join(signal.channel_names)}")
    return lowered.index(key)


def sanitize_nan(
    time_s: np.ndarray,
    values: np.ndarray,
    policy: str,
    source_fs_hz: float,
    warnings: list[WarningRecord],
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    mask = np.isfinite(values)
    nan_count = int((~mask).sum())
    stats: dict[str, object] = {
        "nan_count": nan_count,
        "nan_fraction": float(nan_count / values.size) if values.size else 0.0,
        "nan_policy": policy,
        "nan_max_run_samples": 0,
    }
    if nan_count == 0:
        return time_s, values, stats

    max_run = 0
    current = 0
    for ok in mask:
        if ok:
            max_run = max(max_run, current)
            current = 0
        else:
            current += 1
    max_run = max(max_run, current)
    stats["nan_max_run_samples"] = int(max_run)

    if policy == "error":
        raise ValueError(f"input contains {nan_count} NaN/blank samples")
    if not mask.any():
        raise ValueError("input channel contains only NaN/blank samples")
    if policy == "drop":
        add_warning(warnings, "NAN_DROPPED", f"Dropped {nan_count} NaN/blank samples.")
        return time_s[mask], values[mask], stats
    if policy == "zero":
        add_warning(warnings, "NAN_ZERO_FILLED", f"Replaced {nan_count} NaN/blank samples with 0 V.")
        return time_s, np.where(mask, values, 0.0), stats
    if policy != "interpolate":
        raise ValueError(f"unsupported NaN policy: {policy}")

    if max_run / source_fs_hz > 0.5:
        add_warning(
            warnings,
            "NAN_LONG_GAP_INTERPOLATED",
            f"Interpolated a NaN gap of {max_run} samples ({max_run / source_fs_hz:.3f} s).",
        )
    else:
        add_warning(warnings, "NAN_INTERPOLATED", f"Interpolated {nan_count} NaN/blank samples.")
    repaired = values.copy()
    repaired[~mask] = np.interp(time_s[~mask], time_s[mask], values[mask])
    return time_s, repaired, stats


def crop_window(
    time_s: np.ndarray,
    start_sec: float,
    duration_sec: float | None,
    warnings: list[WarningRecord],
) -> tuple[float, float]:
    if len(time_s) < 1:
        raise ValueError("input signal is empty")
    first = float(time_s[0])
    last = float(time_s[-1])
    effective_start = start_sec
    if start_sec < first:
        add_warning(warnings, "START_CLIPPED", f"Requested start {start_sec:g}s is before data; using {first:g}s.")
        effective_start = first
    if effective_start > last:
        raise ValueError(f"requested start {start_sec:g}s is beyond input end {last:g}s")
    if duration_sec is None:
        duration = last - effective_start
    else:
        duration = float(duration_sec)
        if duration < 0:
            raise ValueError("--duration-sec must be non-negative")
    if effective_start + duration > last:
        new_duration = last - effective_start
        add_warning(
            warnings,
            "DURATION_CLIPPED",
            f"Requested window ends at {effective_start + duration:g}s beyond data end {last:g}s; using duration {new_duration:g}s.",
        )
        duration = new_duration
    return float(effective_start), float(duration)


def output_time_grid(duration_sec: float, stim_fs_hz: float, max_output_points: int, truncate: bool, warnings: list[WarningRecord]) -> np.ndarray:
    if stim_fs_hz <= 0:
        raise ValueError("--stim-fs must be positive")
    if max_output_points < 1:
        raise ValueError("--max-output-points must be at least 1")
    n_points = int(math.floor(duration_sec * stim_fs_hz + 1.0e-12)) + 1
    if n_points > max_output_points:
        if not truncate:
            raise ValueError(
                f"requested output has {n_points} points, above --max-output-points={max_output_points}; "
                "reduce --duration-sec/--stim-fs or raise --max-output-points"
            )
        n_points = max_output_points
        duration_sec = (n_points - 1) / stim_fs_hz
        add_warning(
            warnings,
            "OUTPUT_TRUNCATED",
            f"Output was truncated to {n_points} points ({duration_sec:g}s).",
        )
    return np.arange(n_points, dtype=float) / stim_fs_hz


def reconstruct_zoh(source_t: np.ndarray, source_v: np.ndarray, target_t: np.ndarray) -> np.ndarray:
    idx = np.searchsorted(source_t, target_t, side="right") - 1
    idx = np.clip(idx, 0, len(source_v) - 1)
    return source_v[idx]


def reconstruct_linear(source_t: np.ndarray, source_v: np.ndarray, target_t: np.ndarray) -> np.ndarray:
    return np.interp(target_t, source_t, source_v)


def _pchip_endpoint(h0: float, h1: float, d0: float, d1: float) -> float:
    if h0 <= 0 or h1 <= 0:
        return d0
    m = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if np.sign(m) != np.sign(d0):
        return 0.0
    if np.sign(d0) != np.sign(d1) and abs(m) > abs(3.0 * d0):
        return 3.0 * d0
    return m


def _pchip_slopes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = len(x)
    if n == 2:
        return np.array([(y[1] - y[0]) / (x[1] - x[0])] * 2, dtype=float)
    h = np.diff(x)
    d = np.diff(y) / h
    m = np.zeros(n, dtype=float)
    m[0] = _pchip_endpoint(h[0], h[1], d[0], d[1])
    m[-1] = _pchip_endpoint(h[-1], h[-2], d[-1], d[-2])
    for k in range(1, n - 1):
        if d[k - 1] == 0.0 or d[k] == 0.0 or np.sign(d[k - 1]) != np.sign(d[k]):
            m[k] = 0.0
        else:
            w1 = 2.0 * h[k] + h[k - 1]
            w2 = h[k] + 2.0 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])
    return m


def reconstruct_pchip(source_t: np.ndarray, source_v: np.ndarray, target_t: np.ndarray) -> np.ndarray:
    if len(source_t) < 2:
        return np.full_like(target_t, source_v[0], dtype=float)
    if len(source_t) == 2:
        return reconstruct_linear(source_t, source_v, target_t)
    slopes = _pchip_slopes(source_t, source_v)
    idx = np.searchsorted(source_t, target_t, side="right") - 1
    idx = np.clip(idx, 0, len(source_t) - 2)
    h = source_t[idx + 1] - source_t[idx]
    s = (target_t - source_t[idx]) / h
    h00 = (2.0 * s**3) - (3.0 * s**2) + 1.0
    h10 = (s**3) - (2.0 * s**2) + s
    h01 = (-2.0 * s**3) + (3.0 * s**2)
    h11 = (s**3) - (s**2)
    return h00 * source_v[idx] + h10 * h * slopes[idx] + h01 * source_v[idx + 1] + h11 * h * slopes[idx + 1]


def reconstruct_bandlimited(
    source_t: np.ndarray,
    source_v: np.ndarray,
    target_t: np.ndarray,
    source_fs_hz: float,
    warnings: list[WarningRecord],
    radius: int = 16,
) -> np.ndarray:
    dt = np.diff(source_t)
    if len(dt) == 0:
        return np.full_like(target_t, source_v[0], dtype=float)
    median_dt = float(np.median(dt))
    if median_dt <= 0 or np.max(np.abs(dt - median_dt)) / median_dt > 1.0e-3:
        add_warning(
            warnings,
            "BANDLIMITED_FALLBACK_LINEAR",
            "Bandlimited mode needs nearly uniform source samples; using linear interpolation.",
        )
        return reconstruct_linear(source_t, source_v, target_t)

    add_warning(
        warnings,
        "BANDLIMITED_ASSUMPTION",
        "Bandlimited reconstruction assumes the digitized ECG adequately represents a bandlimited signal.",
    )
    out = np.empty_like(target_t, dtype=float)
    chunk = 16384
    start_t = float(source_t[0])
    for start in range(0, len(target_t), chunk):
        stop = min(start + chunk, len(target_t))
        pos = (target_t[start:stop] - start_t) * source_fs_hz
        center = np.floor(pos).astype(int)
        local = np.zeros(stop - start, dtype=float)
        weight_sum = np.zeros(stop - start, dtype=float)
        for offset in range(-radius + 1, radius + 1):
            idx = np.clip(center + offset, 0, len(source_v) - 1)
            x = pos - idx
            window_arg = (offset + radius - 1) / max(1, (2 * radius - 1))
            window = 0.54 - 0.46 * math.cos(2.0 * math.pi * window_arg)
            weights = np.sinc(x) * window
            local += weights * source_v[idx]
            weight_sum += weights
        near_zero = np.abs(weight_sum) < 1.0e-12
        local[~near_zero] /= weight_sum[~near_zero]
        if near_zero.any():
            local[near_zero] = reconstruct_linear(source_t, source_v, target_t[start:stop][near_zero])
        out[start:stop] = local
    return out


def reconstruct_dac(
    source_t_abs: np.ndarray,
    source_v: np.ndarray,
    target_t_rel: np.ndarray,
    start_sec: float,
    source_fs_hz: float,
    mode: str,
    warnings: list[WarningRecord],
) -> np.ndarray:
    target_t_abs = start_sec + target_t_rel
    left = max(0, np.searchsorted(source_t_abs, target_t_abs[0], side="right") - 2)
    right = min(len(source_t_abs), np.searchsorted(source_t_abs, target_t_abs[-1], side="left") + 3)
    st = source_t_abs[left:right]
    sv = source_v[left:right]
    if len(st) == 0:
        raise ValueError("selected time window has no source samples")
    if len(st) == 1:
        add_warning(warnings, "ONE_SOURCE_SAMPLE", "Selected window contains one source sample; output is constant.")
        return np.full_like(target_t_abs, sv[0], dtype=float)

    if mode == "zoh":
        return reconstruct_zoh(st, sv, target_t_abs)
    if mode == "linear":
        return reconstruct_linear(st, sv, target_t_abs)
    if mode == "cubic":
        add_warning(warnings, "CUBIC_USES_PCHIP", "cubic mode is implemented as shape-preserving PCHIP.")
        return reconstruct_pchip(st, sv, target_t_abs)
    if mode == "pchip":
        return reconstruct_pchip(st, sv, target_t_abs)
    if mode == "bandlimited":
        return reconstruct_bandlimited(st, sv, target_t_abs, source_fs_hz, warnings)
    raise ValueError(f"unsupported DAC mode: {mode}")


def validate_signal_stats(vin_v: np.ndarray, source_fs_hz: float, args: argparse.Namespace, warnings: list[WarningRecord]) -> dict[str, float]:
    stats = {
        "min_v": float(np.min(vin_v)),
        "max_v": float(np.max(vin_v)),
        "mean_v": float(np.mean(vin_v)),
        "rms_v": float(math.sqrt(float(np.mean(vin_v**2)))),
        "peak_abs_v": float(np.max(np.abs(vin_v))),
    }
    if source_fs_hz < args.low_source_fs_warn_hz:
        add_warning(
            warnings,
            "LOW_SOURCE_FS",
            f"Source fs {source_fs_hz:g} Hz is below warning threshold {args.low_source_fs_warn_hz:g} Hz.",
        )
    if stats["peak_abs_v"] > args.amplitude_warn_v:
        add_warning(
            warnings,
            "ABNORMAL_ECG_AMPLITUDE",
            f"Peak absolute voltage {stats['peak_abs_v']:.6g} V exceeds ECG warning threshold {args.amplitude_warn_v:g} V.",
        )
    if stats["peak_abs_v"] > 1.0:
        add_warning(
            warnings,
            "POSSIBLE_UNIT_ERROR",
            "Peak voltage exceeds 1 V; check whether mV/uV input was interpreted as V.",
            severity="strong-warning",
        )
    return stats


def write_stimulus_csv(path: Path, time_s: np.ndarray, vin_v: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "vin_v"])
        for t, v in zip(time_s, vin_v):
            writer.writerow([f"{float(t):.12g}", f"{float(v):.12g}"])


def estimate_pwl_points(time_s: np.ndarray, vin_v: np.ndarray, dac_mode: str, stim_fs_hz: float) -> int:
    if dac_mode != "zoh" or len(time_s) <= 1:
        return int(len(time_s))
    eps = min(1.0e-12, 0.001 / max(1.0, stim_fs_hz))
    points = 1
    for i in range(len(time_s) - 1):
        if vin_v[i + 1] != vin_v[i] and max(float(time_s[i]), float(time_s[i + 1]) - eps) > float(time_s[i]):
            points += 1
        points += 1
    return points


def write_pwl(path: Path, time_s: np.ndarray, vin_v: np.ndarray, dac_mode: str, stim_fs_hz: float) -> dict[str, object]:
    point_count = 0
    metadata: dict[str, object] = {
        "semantics": "piecewise-linear sampled waveform",
        "points": 0,
        "zoh_epsilon_s": None,
    }
    with path.open("w", encoding="utf-8", newline="\n") as f:
        if dac_mode == "zoh" and len(time_s) > 1:
            eps = min(1.0e-12, 0.001 / max(1.0, stim_fs_hz))
            metadata["semantics"] = "mode-aware staircase for zoh"
            metadata["zoh_epsilon_s"] = eps
            for i in range(len(time_s) - 1):
                f.write(f"{float(time_s[i]):.12g} {float(vin_v[i]):.12g}\n")
                point_count += 1
                if vin_v[i + 1] != vin_v[i]:
                    step_t = max(float(time_s[i]), float(time_s[i + 1]) - eps)
                    if step_t > float(time_s[i]):
                        f.write(f"{step_t:.12g} {float(vin_v[i]):.12g}\n")
                        point_count += 1
            f.write(f"{float(time_s[-1]):.12g} {float(vin_v[-1]):.12g}\n")
            point_count += 1
        else:
            for t, v in zip(time_s, vin_v):
                f.write(f"{float(t):.12g} {float(v):.12g}\n")
                point_count += 1
    metadata["points"] = point_count
    return metadata


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", binascii.crc32(chunk_type + data) & 0xFFFFFFFF)


def write_png_rgb(path: Path, width: int, height: int, pixels: bytearray) -> None:
    scanlines = bytearray()
    row_bytes = width * 3
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(pixels[y * row_bytes : (y + 1) * row_bytes])
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(_png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    png.extend(_png_chunk(b"IDAT", zlib.compress(bytes(scanlines), level=6)))
    png.extend(_png_chunk(b"IEND", b""))
    path.write_bytes(bytes(png))


def draw_line(pixels: bytearray, width: int, height: int, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        if 0 <= x < width and 0 <= y < height:
            idx = (y * width + x) * 3
            pixels[idx : idx + 3] = bytes(color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def write_qa_plot(path: Path, time_s: np.ndarray, vin_v: np.ndarray) -> None:
    width, height = 1000, 420
    pixels = bytearray([255] * width * height * 3)
    margin_l, margin_r, margin_t, margin_b = 64, 24, 24, 48
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    axis_color = (90, 90, 90)
    line_color = (0, 92, 175)
    grid_color = (225, 225, 225)

    for frac in np.linspace(0.0, 1.0, 6):
        x = int(margin_l + frac * plot_w)
        draw_line(pixels, width, height, x, margin_t, x, margin_t + plot_h, grid_color)
    for frac in np.linspace(0.0, 1.0, 5):
        y = int(margin_t + frac * plot_h)
        draw_line(pixels, width, height, margin_l, y, margin_l + plot_w, y, grid_color)
    draw_line(pixels, width, height, margin_l, margin_t, margin_l, margin_t + plot_h, axis_color)
    draw_line(pixels, width, height, margin_l, margin_t + plot_h, margin_l + plot_w, margin_t + plot_h, axis_color)

    if len(time_s) == 0:
        write_png_rgb(path, width, height, pixels)
        return
    max_preview = min(len(time_s), 5000)
    if len(time_s) > max_preview:
        indices = np.linspace(0, len(time_s) - 1, max_preview).astype(int)
        t = time_s[indices]
        v = vin_v[indices]
    else:
        t = time_s
        v = vin_v
    t0, t1 = float(t[0]), float(t[-1])
    if t1 <= t0:
        t1 = t0 + 1.0
    vmax = float(np.max(np.abs(v))) if len(v) else 1.0
    if vmax <= 0:
        vmax = 1.0

    xs = np.round(margin_l + (t - t0) / (t1 - t0) * plot_w).astype(int)
    ys = np.round(margin_t + (0.5 - 0.45 * (v / vmax)) * plot_h).astype(int)
    for i in range(1, len(xs)):
        draw_line(pixels, width, height, int(xs[i - 1]), int(ys[i - 1]), int(xs[i]), int(ys[i]), line_color)
    write_png_rgb(path, width, height, pixels)


def write_readme(path: Path, metadata: dict[str, object], command_line: str) -> None:
    warnings = metadata.get("warnings", [])
    warning_lines = "\n".join(
        f"- `{w.get('code', 'WARNING')}`: {w.get('message', '')}" for w in warnings if isinstance(w, dict)
    )
    if not warning_lines:
        warning_lines = "- None."
    text = f"""# XMODEL ECG Stimulus

## Scope and limitation

{LIMITATION_TEXT}

The output voltage column is always `vin_v` in volts. The generated
`stimulus_xmodel.csv` is intended as a direct scalar voltage input stimulus for
an AFE+ADC XMODEL testbench.

## Files

- `stimulus_xmodel.csv`: CSV waveform with columns `time_s,vin_v`.
- `stimulus_pwl.txt`: whitespace-separated PWL-style waveform, `time_s vin_v`.
- `metadata.json`: source, unit conversion, DAC mode, safety warnings, and assumptions.
- `qa_plot.png`: quick visual preview of the replay waveform.
- `README_stimulus.md`: this file.

## Reconstruction settings

- Source path: `{metadata.get('source_path')}`
- Input type: `{metadata.get('input_kind')}`
- Channel: `{metadata.get('channel_name')}` (`{metadata.get('channel_index')}`)
- Source fs: `{metadata.get('source_fs_hz')}` Hz
- Stimulus fs: `{metadata.get('stim_fs_hz')}` Hz
- DAC mode: `{metadata.get('dac_mode')}`
- Start: `{metadata.get('start_sec')}` s
- Duration: `{metadata.get('duration_sec')}` s
- Output points: `{metadata.get('output_points')}`

## Warnings

{warning_lines}

## Command used

```powershell
{command_line}
```

## PowerShell examples

Single WFDB/CSV conversion:

```powershell
python tools\\ecg_to_xmodel_stimulus.py `
  --input \"C:\\path\\to\\record.hea\" `
  --out-dir build\\xmodel_stimulus\\single `
  --channel 0 `
  --start-sec 0 `
  --duration-sec 10 `
  --stim-fs 10000 `
  --dac-mode linear
```

CSV with explicit units:

```powershell
python tools\\ecg_to_xmodel_stimulus.py `
  --input .\\ecg.csv `
  --out-dir build\\xmodel_stimulus\\csv_case `
  --fs 250 `
  --value-col ecg_mV `
  --input-units mV `
  --duration-sec 5 `
  --dac-mode pchip
```

Batch generation:

```powershell
python tools\\batch_make_xmodel_stimulus.py `
  --input-root \"C:\\path\\to\\ECG Data Real\" `
  --output-root build\\xmodel_stimulus `
  --duration-sec 10 `
  --stim-fs 10000 `
  --dac-mode linear
```
"""
    path.write_text(text, encoding="utf-8", newline="\n")


def command_line_for_metadata(argv: Sequence[str] | None) -> str:
    if argv is None:
        return subprocess.list2cmdline([Path(sys.executable).name, *sys.argv])
    return subprocess.list2cmdline(["python", "tools\\ecg_to_xmodel_stimulus.py", *argv])


def convert_file(args: argparse.Namespace, argv: Sequence[str] | None = None) -> StimulusResult:
    warnings: list[WarningRecord] = []
    input_path = Path(args.input).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    if not input_path.exists() and not input_path.with_suffix(".hea").exists():
        raise FileNotFoundError(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    signal = load_input_signal(input_path, args, warnings)
    channel_selector = "0" if signal.metadata.get("csv_value_column") else args.channel
    channel_index = select_channel(signal, channel_selector)
    source_unit = signal.units[channel_index] if channel_index < len(signal.units) else "mV"
    source_v = signal.values[:, channel_index].astype(float) * unit_scale_to_volts(source_unit)
    source_t = signal.time_s.astype(float)

    start_sec = float(args.start_sec)
    requested_start_sec = start_sec
    start_sec, duration = crop_window(source_t, start_sec, args.duration_sec, warnings)
    end_sec = start_sec + duration
    lo = max(0, np.searchsorted(source_t, start_sec, side="right") - 2)
    hi = min(len(source_t), np.searchsorted(source_t, end_sec, side="left") + 3)
    source_t_win = source_t[lo:hi]
    source_v_win = source_v[lo:hi]
    if args.nan_policy == "error":
        finite = np.isfinite(source_v_win)
        inside = (source_t_win >= start_sec) & (source_t_win <= end_sec)
        if (~finite & inside).any():
            raise ValueError(f"selected input window contains {int((~finite & inside).sum())} NaN/blank samples")
        if (~finite).any():
            source_t_win, source_v_win, nan_stats = sanitize_nan(
                source_t_win,
                source_v_win,
                "interpolate",
                signal.source_fs_hz,
                warnings,
            )
        else:
            source_t_win, source_v_win, nan_stats = sanitize_nan(
                source_t_win,
                source_v_win,
                args.nan_policy,
                signal.source_fs_hz,
                warnings,
            )
    else:
        source_t_win, source_v_win, nan_stats = sanitize_nan(
            source_t_win,
            source_v_win,
            args.nan_policy,
            signal.source_fs_hz,
            warnings,
        )
    stim_time = output_time_grid(duration, float(args.stim_fs), int(args.max_output_points), bool(args.truncate_to_max), warnings)
    if len(stim_time) == 0:
        raise ValueError("output time grid is empty")
    actual_duration = float(stim_time[-1]) if len(stim_time) else 0.0
    vin_v = reconstruct_dac(source_t_win, source_v_win, stim_time, start_sec, signal.source_fs_hz, args.dac_mode, warnings)
    estimated_pwl_points = estimate_pwl_points(stim_time, vin_v, args.dac_mode, float(args.stim_fs))
    if estimated_pwl_points > int(args.max_output_points):
        raise ValueError(
            f"requested PWL output has {estimated_pwl_points} points after {args.dac_mode} expansion, above "
            f"--max-output-points={args.max_output_points}; reduce --duration-sec/--stim-fs or raise the limit"
        )
    stats = validate_signal_stats(vin_v, signal.source_fs_hz, args, warnings)

    stimulus_csv = out_dir / "stimulus_xmodel.csv"
    stimulus_pwl = out_dir / "stimulus_pwl.txt"
    metadata_json = out_dir / "metadata.json"
    qa_plot = out_dir / "qa_plot.png"
    readme = out_dir / "README_stimulus.md"

    write_stimulus_csv(stimulus_csv, stim_time, vin_v)
    pwl_metadata = write_pwl(stimulus_pwl, stim_time, vin_v, args.dac_mode, float(args.stim_fs))
    write_qa_plot(qa_plot, stim_time, vin_v)

    metadata: dict[str, object] = {
        "tool": "ecg_to_xmodel_stimulus.py",
        "limitation": LIMITATION_TEXT,
        "source_path": str(input_path),
        "input_kind": signal.input_kind,
        "source_fs_hz": signal.source_fs_hz,
        "source_units": source_unit,
        "output_units": "V",
        "channel_index": channel_index,
        "channel_name": signal.channel_names[channel_index] if channel_index < len(signal.channel_names) else f"channel_{channel_index}",
        "requested_start_sec": requested_start_sec,
        "start_sec": start_sec,
        "duration_sec": actual_duration,
        "stim_fs_hz": float(args.stim_fs),
        "dac_mode": args.dac_mode,
        "output_points": int(len(stim_time)),
        "nan": nan_stats,
        "voltage_stats": stats,
        "pwl": pwl_metadata,
        "warnings": [w.as_dict() for w in warnings],
        "outputs": {
            "stimulus_xmodel_csv": str(stimulus_csv),
            "stimulus_pwl_txt": str(stimulus_pwl),
            "metadata_json": str(metadata_json),
            "qa_plot_png": str(qa_plot),
            "readme_stimulus_md": str(readme),
        },
        "input_metadata": signal.metadata,
        "command_line": command_line_for_metadata(argv),
    }
    metadata_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_readme(readme, metadata, str(metadata["command_line"]))

    return StimulusResult(
        out_dir=out_dir,
        stimulus_csv=stimulus_csv,
        stimulus_pwl=stimulus_pwl,
        metadata_json=metadata_json,
        qa_plot=qa_plot,
        readme=readme,
        metadata=metadata,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate analog-equivalent AFE+ADC XMODEL ECG stimulus from WFDB or CSV data."
    )
    parser.add_argument("--input", required=True, help="Input CSV, WFDB .hea, .dat, or WFDB record path.")
    parser.add_argument("--out-dir", required=True, help="Output directory for stimulus artifacts.")
    parser.add_argument("--channel", default="0", help="Channel index or name. Default: 0.")
    parser.add_argument("--value-col", default=None, help="CSV value column name or index. Overrides --channel for CSV.")
    parser.add_argument("--time-col", default=None, help="CSV time column name or index. If omitted, --fs is required.")
    parser.add_argument("--fs", type=float, default=None, help="Source sampling rate for CSV without a time column.")
    parser.add_argument("--start-sec", type=float, default=0.0, help="Start time in source seconds. Default: 0.")
    parser.add_argument("--duration-sec", type=float, default=None, help="Duration in seconds. Default: until input end.")
    parser.add_argument("--input-units", default="auto", help="CSV input units: auto, V, mV, or uV. Default: auto.")
    parser.add_argument("--stim-fs", type=float, default=10000.0, help="Stimulus output sample rate in Hz. Default: 10000.")
    parser.add_argument("--dac-mode", choices=DAC_MODES, default="linear", help="DAC replay mode.")
    parser.add_argument(
        "--nan-policy",
        choices=("error", "interpolate", "drop", "zero"),
        default="interpolate",
        help="NaN/blank sample handling. Default: interpolate.",
    )
    parser.add_argument(
        "--max-output-points",
        type=int,
        default=2_000_000,
        help="Safety limit for stimulus_xmodel.csv rows. Default: 2000000.",
    )
    parser.add_argument(
        "--truncate-to-max",
        action="store_true",
        help="Shorten duration instead of failing when --max-output-points is exceeded.",
    )
    parser.add_argument(
        "--low-source-fs-warn-hz",
        type=float,
        default=300.0,
        help="Warn when source fs is below this Hz. Default: 300.",
    )
    parser.add_argument(
        "--amplitude-warn-v",
        type=float,
        default=0.020,
        help="Warn when peak absolute output voltage exceeds this value. Default: 0.020 V.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> StimulusResult:
    parser = build_parser()
    args = parser.parse_args(argv)
    return convert_file(args, argv)


if __name__ == "__main__":
    main()
