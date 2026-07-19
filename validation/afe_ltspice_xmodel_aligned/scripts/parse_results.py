#!/usr/bin/env python3
"""Parse LTspice ASCII raw evidence and generate quantitative CSV/SVG artifacts."""

from __future__ import annotations

import csv
import gc
import html
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
TABLES = ROOT / "tables"
PLOTS = ROOT / "plots"
NOMINAL = ROOT / "results" / "nominal"
LSB = 3.3 / 4095.0
COMMON_FIELDS = [
    "test_id", "variant", "source_schematic", "simulation_type", "metric",
    "target", "measured", "unit", "deviation", "status", "evidence_path", "notes",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_number(token: str, complex_mode: bool):
    token = token.strip().split()[-1]
    if complex_mode:
        a, b = token.split(",")
        return float(a) + 1j * float(b)
    return float(token)


def read_ascii_raw(path: Path, wanted: set[str] | None = None) -> dict[str, np.ndarray]:
    """Streaming parser for LTspice -ascii raw files."""
    with path.open("r", encoding="utf-8", errors="replace") as f:
        nvars = npoints = None
        offset = 0.0
        complex_mode = False
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"Missing Variables section: {path}")
            if line.startswith("Flags:"):
                complex_mode = "complex" in line.lower()
            elif line.startswith("No. Variables:"):
                nvars = int(line.split(":", 1)[1])
            elif line.startswith("No. Points:"):
                npoints = int(line.split(":", 1)[1])
            elif line.startswith("Offset:"):
                offset = float(line.split(":", 1)[1])
            elif line.rstrip("\r\n") == "Variables:":
                break
        assert nvars is not None and npoints is not None
        names = []
        for _ in range(nvars):
            names.append(f.readline().split()[1].lower())
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"Missing Values section: {path}")
            if line.rstrip("\r\n") == "Values:":
                break
        if wanted is None:
            selected = list(range(nvars))
        else:
            selected = [i for i, name in enumerate(names) if name in wanted]
        dtype = np.complex128 if complex_mode else np.float64
        arrays = {names[i]: np.empty(npoints, dtype=dtype) for i in selected}
        actual = 0
        for point in range(npoints):
            first = f.readline()
            if not first:
                break
            values = [first]
            for _ in range(nvars - 1):
                values.append(f.readline())
            for i in selected:
                arrays[names[i]][point] = parse_number(values[i], complex_mode)
            actual += 1
        if actual != npoints:
            arrays = {k: v[:actual] for k, v in arrays.items()}
        if "time" in arrays and offset:
            arrays["time"] += offset
        return arrays


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def row(test_id, variant, source, sim, metric, measured, unit, evidence,
        target="", deviation="", status="MEASURED", notes=""):
    return dict(test_id=test_id, variant=variant, source_schematic=source,
                simulation_type=sim, metric=metric, target=target,
                measured=fmt(measured), unit=unit, deviation=fmt(deviation),
                status=status, evidence_path=evidence, notes=notes)


def fmt(value):
    if value == "" or value is None:
        return ""
    if isinstance(value, (bool, np.bool_)):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.12g}"


def dev(measured, target):
    return 100.0 * (measured - target) / target


def interp(x, y, xp):
    return np.interp(xp, x, y)


def interp_complex_log(x, y, xp):
    lx = np.log10(x)
    q = math.log10(xp)
    return np.interp(q, lx, y.real) + 1j * np.interp(q, lx, y.imag)


def crossing_frequency(f, mag, target, rising=True, lo=None, hi=None):
    mask = np.ones_like(f, dtype=bool)
    if lo is not None:
        mask &= f >= lo
    if hi is not None:
        mask &= f <= hi
    ff, yy = f[mask], mag[mask]
    cond = (yy[:-1] <= target) & (yy[1:] >= target) if rising else (yy[:-1] >= target) & (yy[1:] <= target)
    ids = np.flatnonzero(cond)
    if not len(ids):
        return float("nan")
    i = ids[0]
    if yy[i + 1] == yy[i]:
        return float(ff[i])
    frac = (target - yy[i]) / (yy[i + 1] - yy[i])
    return float(10 ** (math.log10(ff[i]) + frac * (math.log10(ff[i + 1]) - math.log10(ff[i]))))


def db20(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-300))


def svg_line_plot(path: Path, title: str, x: np.ndarray, series: dict[str, np.ndarray],
                  x_label: str, y_label: str, log_x=False, xlim=None, ylim=None,
                  verticals: list[float] | None = None) -> None:
    width, height = 1100, 620
    ml, mr, mt, mb = 90, 30, 55, 75
    xx = np.log10(x) if log_x else x
    if xlim:
        xlo, xhi = (math.log10(xlim[0]), math.log10(xlim[1])) if log_x else xlim
    else:
        xlo, xhi = float(np.nanmin(xx)), float(np.nanmax(xx))
    vals = np.concatenate([np.asarray(v)[np.isfinite(v)] for v in series.values()])
    ylo, yhi = ylim if ylim else (float(vals.min()), float(vals.max()))
    pad = 0.06 * (yhi - ylo if yhi > ylo else 1.0)
    ylo -= pad; yhi += pad
    def X(v): return ml + (v - xlo) / (xhi - xlo) * (width - ml - mr)
    def Y(v): return mt + (yhi - v) / (yhi - ylo) * (height - mt - mb)
    colors = ["#1565c0", "#d84315", "#2e7d32", "#6a1b9a", "#00838f", "#ad1457"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{html.escape(title)}</text>']
    for k in range(6):
        yv = ylo + k * (yhi - ylo) / 5
        py = Y(yv)
        parts.append(f'<line x1="{ml}" y1="{py:.2f}" x2="{width-mr}" y2="{py:.2f}" stroke="#dddddd"/>')
        parts.append(f'<text x="{ml-10}" y="{py+4:.2f}" text-anchor="end" font-family="Arial" font-size="12">{yv:.3g}</text>')
    if log_x:
        e0, e1 = math.ceil(xlo), math.floor(xhi)
        ticks = [10.0 ** e for e in range(e0, e1 + 1)]
    else:
        ticks = np.linspace(xlo, xhi, 6)
    for tv in ticks:
        q = math.log10(tv) if log_x else float(tv)
        px = X(q)
        label = f"{tv:g}"
        parts.append(f'<line x1="{px:.2f}" y1="{mt}" x2="{px:.2f}" y2="{height-mb}" stroke="#eeeeee"/>')
        parts.append(f'<text x="{px:.2f}" y="{height-mb+22}" text-anchor="middle" font-family="Arial" font-size="12">{label}</text>')
    if verticals:
        for v in verticals:
            q = math.log10(v) if log_x else v
            if xlo <= q <= xhi:
                px = X(q)
                parts.append(f'<line x1="{px:.2f}" y1="{mt}" x2="{px:.2f}" y2="{height-mb}" stroke="#777" stroke-dasharray="4 4"/>')
    for idx, (label, yy) in enumerate(series.items()):
        mask = np.isfinite(yy) & (xx >= xlo) & (xx <= xhi)
        ids = np.flatnonzero(mask)
        if len(ids) > 6000:
            ids = ids[np.linspace(0, len(ids)-1, 6000).astype(int)]
        points = " ".join(f"{X(xx[i]):.2f},{Y(float(yy[i])):.2f}" for i in ids)
        color = colors[idx % len(colors)]
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.6"/>')
        lx = ml + 15 + idx * 175
        parts.append(f'<line x1="{lx}" y1="{height-20}" x2="{lx+24}" y2="{height-20}" stroke="{color}" stroke-width="2.5"/>')
        parts.append(f'<text x="{lx+30}" y="{height-16}" font-family="Arial" font-size="12">{html.escape(label)}</text>')
    parts += [f'<line x1="{ml}" y1="{height-mb}" x2="{width-mr}" y2="{height-mb}" stroke="#222"/>',
              f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{height-mb}" stroke="#222"/>',
              f'<text x="{(ml+width-mr)/2}" y="{height-42}" text-anchor="middle" font-family="Arial" font-size="14">{html.escape(x_label)}</text>',
              f'<text transform="translate(24 {(mt+height-mb)/2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="14">{html.escape(y_label)}</text>', '</svg>']
    path.write_text("\n".join(parts), encoding="utf-8")


def time_rms(t, y):
    if len(t) < 2:
        return float("nan")
    return float(math.sqrt(np.trapezoid(y * y, t) / (t[-1] - t[0])))


def ac_metrics():
    rows = []
    cache = {}
    for variant in ("as_implemented", "intent_aligned"):
        source = f"schematics/ac_testbenches/ac_afe_{variant}.cir"
        raw_path = RAW / f"ac_afe_{variant}.raw"
        d = read_ascii_raw(raw_path)
        f = d["frequency"].real
        vin = d["v(inp_raw)"] - d["v(inn_raw)"]
        hpf = (d["v(hpf_p)"] - d["v(hpf_n)"]) / vin
        ia = d["v(ia_out)"] / (d["v(hpf_p)"] - d["v(hpf_n)"])
        notch = d["v(notch_out)"] / d["v(ia_out)"]
        lpf = d["v(afe_out)"] / d["v(notch_out)"]
        full = d["v(afe_out)"] / vin
        cache[variant] = (f, hpf, ia, notch, lpf, full)
        fine = read_ascii_raw(RAW / f"notch_fine_{variant}.raw")
        fine_f = fine["frequency"].real
        fine_h = fine["v(notch_out)"] / fine["v(ia_out)"]
        mi = int(np.argmin(np.abs(fine_h)))
        hp_ref = float(np.median(np.abs(hpf[(f >= 10) & (f <= 100)])))
        hp_fc = crossing_frequency(f, np.abs(hpf), hp_ref / math.sqrt(2), True, .02, 5)
        lpf_ref = float(np.median(np.abs(lpf[(f >= 1) & (f <= 10)])))
        lpf_fc = crossing_frequency(f, np.abs(lpf), lpf_ref / math.sqrt(2), False, 20, 1000)
        evidence = rel(raw_path)
        add = lambda tid, metric, measured, unit, target="", notes="": rows.append(
            row(tid, variant, source, "AC", metric, measured, unit, evidence,
                target, dev(measured, target) if target != "" else "", "MEASURED", notes))
        add("AC_HPF", "passband_gain", hp_ref, "V/V")
        add("AC_HPF", "cutoff_minus_3dB", hp_fc, "Hz", 0.4823, "Reference is median 10-100 Hz HPF gain; log-frequency interpolation.")
        for hz in (1, 10):
            add("AC_HPF", f"magnitude_{hz}Hz", abs(interp_complex_log(f, hpf, hz)), "V/V")
        gain10 = abs(interp_complex_log(f, ia, 10))
        add("AC_IA", "gain_10Hz", gain10, "V/V", 201)
        add("AC_IA", "gain_10Hz", 20*math.log10(gain10), "dB", 20*math.log10(201))
        h60 = fine_h[int(np.argmin(abs(fine_f - 60)))]
        add("AC_NOTCH", "attenuation_60Hz", 20*math.log10(abs(h60)), "dB", notes="Fine linear sweep, 0.0005 Hz resolution.")
        add("AC_NOTCH", "minimum_frequency", fine_f[mi], "Hz", 60, "Search window 55-65 Hz; 0.0005 Hz spacing.")
        add("AC_NOTCH", "minimum_attenuation", 20*math.log10(abs(fine_h[mi])), "dB", notes="Search window 55-65 Hz.")
        near = (f >= 20) & (f <= 120)
        add("AC_NOTCH", "maximum_magnitude_20to120Hz", float(np.max(db20(notch[near]))), "dB")
        add("AC_LPF", "cutoff_minus_3dB", lpf_fc, "Hz", 150.15, "Reference is median 1-10 Hz LPF gain.")
        for hz in (10, 60, 150, 1000):
            add("AC_LPF", f"magnitude_{hz}Hz", abs(interp_complex_log(f, lpf, hz)), "V/V")
        g10 = abs(interp_complex_log(f, full, 10))
        add("AC_FULL", "gain_10Hz", g10, "V/V")
        add("AC_FULL", "gain_10Hz", 20*math.log10(g10), "dB")
        for hz, label in ((.1, "baseline_0p1Hz_relative_to_10Hz"), (60, "60Hz_relative_to_10Hz"), (1000, "1kHz_relative_to_10Hz")):
            add("AC_FULL", label, 20*math.log10(abs(interp_complex_log(f, full, hz))/g10), "dB")
        response_rows = []
        for i in range(len(f)):
            response_rows.append({"frequency_hz": fmt(f[i]), "hpf_db": fmt(db20(hpf[i])),
                                  "ia_db": fmt(db20(ia[i])), "notch_db": fmt(db20(notch[i])),
                                  "lpf_db": fmt(db20(lpf[i])), "full_afe_db": fmt(db20(full[i]))})
        write_csv(NOMINAL / f"ac_response_{variant}.csv", response_rows,
                  ["frequency_hz", "hpf_db", "ia_db", "notch_db", "lpf_db", "full_afe_db"])
    write_csv(TABLES / "nominal_ac_metrics.csv", rows, COMMON_FIELDS)
    f, hpf, ia, notch, lpf, full = cache["intent_aligned"]
    fa, _, _, notcha, _, fulla = cache["as_implemented"]
    svg_line_plot(PLOTS/"hpf_response.svg", "Differential HPF response", f, {"intent-aligned": db20(hpf)}, "Frequency (Hz)", "Magnitude (dB)", True, (.01, 100))
    svg_line_plot(PLOTS/"ia_response.svg", "Instrumentation-amplifier differential gain", f, {"intent-aligned": db20(ia)}, "Frequency (Hz)", "Gain (dB)", True, (.1, 10000))
    svg_line_plot(PLOTS/"notch_response.svg", "Twin-T notch: source topology versus intent-aligned", f, {"as-implemented": db20(notcha), "intent-aligned": db20(notch)}, "Frequency (Hz)", "Magnitude (dB)", True, (10, 300), (-90, 5), [60])
    svg_line_plot(PLOTS/"lpf_response.svg", "150 Hz LPF response", f, {"intent-aligned": db20(lpf)}, "Frequency (Hz)", "Magnitude (dB)", True, (1, 10000))
    svg_line_plot(PLOTS/"full_afe_response.svg", "Full AFE response", f, {"as-implemented": db20(fulla), "intent-aligned": db20(full)}, "Frequency (Hz)", "Gain (dB)", True, (.01, 10000))


TRANSIENT_WANTED = {"time", "v(inp_raw)", "v(inn_raw)", "v(hpf_p)", "v(hpf_n)",
                    "v(u1_out)", "v(u2_out)", "v(ia_out)", "v(notch_sense)",
                    "v(notch_out)", "v(k_div)", "v(vk)", "v(lpf_node)",
                    "v(afe_out)", "v(clk)", "v(adc_hold)", "v(adc_clip)",
                    "v(adc_code)", "v(adc_signed)"}


def export_samples(d, variant, source, raw_path):
    t = d["time"]
    sample_t = np.arange(10000, dtype=float) * 1e-3 + 0.5e-3
    afe = interp(t, d["v(afe_out)"], sample_t)
    hold = interp(t, d["v(adc_hold)"], sample_t)
    clip = interp(t, d["v(adc_clip)"], sample_t)
    code = np.rint(interp(t, d["v(adc_code)"], sample_t)).astype(int)
    signed = np.rint(interp(t, d["v(adc_signed)"], sample_t)).astype(int)
    out = NOMINAL / ("ltspice_adc_samples.csv" if variant == "intent_aligned" else "ltspice_adc_samples_as_implemented.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["sample_index", "time_s", "afe_out_v", "adc_hold_v", "adc_clip_v", "adc_code", "adc_signed", "hex12"])
        for i in range(len(sample_t)):
            w.writerow([i, f"{sample_t[i]:.9f}", f"{afe[i]:.12g}", f"{hold[i]:.12g}", f"{clip[i]:.12g}", code[i], signed[i], f"{signed[i] & 0xFFF:03X}"])
    if variant == "intent_aligned":
        mem = NOMINAL / "ltspice_adc_signed.mem"
        with mem.open("w", encoding="ascii", newline="\n") as f:
            f.write("// LTspice-derived validation vector; not an official locked reference vector.\n")
            f.write("// Valid sample phase: 500 us after each 1 ms period start.\n")
            for value in signed:
                f.write(f"{value & 0xFFF:03X}\n")
    return sample_t, afe, hold, clip, code, signed, out


def export_transient_uniform(d, variant):
    t = d["time"]
    q = np.arange(100001, dtype=float) * 100e-6
    names = ["v(inp_raw)", "v(inn_raw)", "v(hpf_p)", "v(hpf_n)", "v(u1_out)", "v(u2_out)",
             "v(ia_out)", "v(notch_out)", "v(afe_out)", "v(clk)", "v(adc_hold)", "v(adc_clip)",
             "v(adc_code)", "v(adc_signed)"]
    vals = [interp(t, d[n], q) for n in names]
    path = NOMINAL / ("transient_export.csv" if variant == "intent_aligned" else "transient_export_as_implemented.csv")
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "inp_raw_v", "inn_raw_v", "hpf_p_v", "hpf_n_v", "u1_out_v", "u2_out_v",
                    "ia_out_v", "notch_out_v", "afe_out_v", "clk_v", "adc_hold_v", "adc_clip_v", "adc_code", "adc_signed"])
        for i in range(len(q)):
            w.writerow([f"{q[i]:.7f}"] + [f"{v[i]:.12g}" for v in vals])
    return path


def transient_metrics_for(variant, filename):
    raw_path = RAW / filename
    d = read_ascii_raw(raw_path, TRANSIENT_WANTED)
    t = d["time"]
    source = f"schematics/transient_testbenches/{filename[:-4]}.cir"
    evidence = rel(raw_path)
    rows = []
    derived = {
        "input_diff": d["v(inp_raw)"] - d["v(inn_raw)"],
        "hpf_diff": d["v(hpf_p)"] - d["v(hpf_n)"],
        "u1_out": d["v(u1_out)"], "u2_out": d["v(u2_out)"], "ia_out": d["v(ia_out)"],
        "notch_out": d["v(notch_out)"], "afe_out": d["v(afe_out)"], "adc_hold": d["v(adc_hold)"],
        "adc_clip": d["v(adc_clip)"], "adc_code": d["v(adc_code)"], "adc_signed": d["v(adc_signed)"],
    }
    for window, lo, hi in (("full_0to10s", 0, 10), ("initial_0to1s", 0, 1), ("settled_1to10s", 1, 10)):
        mask = (t >= lo) & (t <= hi)
        tw = t[mask]
        for name, y in derived.items():
            yy = y[mask]
            for metric, value in (("min", np.min(yy)), ("max", np.max(yy)), ("peak_to_peak", np.ptp(yy)), ("rms", time_rms(tw, yy))):
                unit = "code" if name in ("adc_code", "adc_signed") else "V"
                rows.append(row("TRAN_STAGE", variant, source, "TRAN", f"{window}.{name}.{metric}", value, unit, evidence,
                                status="MEASURED", notes="RMS is time-weighted trapezoidal integration."))
    settled = (t >= 1) & (t <= 10)
    outputs = {"U1": d["v(u1_out)"], "U2": d["v(u2_out)"], "U3": d["v(ia_out)"],
               "U4": d["v(notch_out)"], "U5": d["v(vk)"], "U6": d["v(afe_out)"]}
    rail = {}
    for name, y in outputs.items():
        yy = y[settled]
        headroom = min(5 - float(np.max(yy)), float(np.min(yy)) + 5)
        rail[name] = headroom
        rows.append(row("TRAN_RAIL", variant, source, "TRAN", f"{name}_minimum_rail_headroom_1to10s", headroom, "V", evidence,
                        notes="Minimum distance to either +5 V or -5 V rail."))
    closest = min(rail, key=rail.get)
    rows.append(row("TRAN_RAIL", variant, source, "TRAN", "closest_stage_to_rail", closest, "stage", evidence,
                    notes=f"Minimum headroom {rail[closest]:.12g} V."))
    afe_abs = float(np.max(np.abs(d["v(afe_out)"][settled])))
    rows.append(row("TRAN_ADC_HEADROOM", variant, source, "TRAN", "AFE_OUT_headroom_to_1p65V", 1.65-afe_abs, "V", evidence))
    rows.append(row("TRAN_ADC_HEADROOM", variant, source, "TRAN", "continuous_time_clipping_detected", afe_abs > 1.65, "boolean", evidence))
    sample_t, afe, hold, clip, code, signed, sample_path = export_samples(d, variant, source, raw_path)
    clip_mask = np.abs(hold) > 1.65 + 1e-12
    rows.append(row("TRAN_ADC_HEADROOM", variant, source, "TRAN", "sampled_clip_count", int(np.sum(clip_mask)), "samples", rel(sample_path)))
    rows.append(row("TRAN_ADC_HEADROOM", variant, source, "TRAN", "sampled_clip_ratio", float(np.mean(clip_mask)), "ratio", rel(sample_path)))
    pos_mask = settled & (derived["hpf_diff"] > 0)
    idxs = np.flatnonzero(pos_mask)
    pi = idxs[int(np.argmax(derived["hpf_diff"][pos_mask]))]
    rows.append(row("TRAN_POLARITY", variant, source, "TRAN", "positive_HPF_event_IA_OUT", d["v(ia_out)"][pi], "V", evidence,
                    notes=f"At t={t[pi]:.9g} s, HPF differential={derived['hpf_diff'][pi]:.12g} V; topology is non-inverting."))
    track_end = np.arange(10000) * 1e-3 + 101.5e-6
    acq = interp(t, d["v(afe_out)"], track_end) - interp(t, d["v(adc_hold)"], track_end)
    hs = np.arange(10000) * 1e-3 + 102e-6
    he = np.arange(10000) * 1e-3 + 999e-6
    droop = interp(t, d["v(adc_hold)"], he) - interp(t, d["v(adc_hold)"], hs)
    th = []
    def thadd(metric, measured, unit, notes=""):
        th.append(row("TRACK_HOLD", variant, source, "TRAN", metric, measured, unit, evidence, notes=notes))
    thadd("track_start_phase", 0.52, "us", "Rising threshold Vt+Vh=2.6 V on a 1 us 0-5 V edge.")
    thadd("track_end_phase", 101.52, "us", "Falling threshold Vt-Vh=2.4 V; falling edge begins at 101 us.")
    thadd("switch_reliably_off_phase", 102, "us")
    thadd("valid_sample_phase", 500, "us", "Fixed hold-phase sample, safely after switch turn-off.")
    thadd("acquisition_error_max_abs", float(np.max(np.abs(acq))), "V")
    thadd("acquisition_error_rms", float(math.sqrt(np.mean(acq*acq))), "V")
    thadd("acquisition_error_max_abs", float(np.max(np.abs(acq)) / LSB), "LSB")
    thadd("hold_droop_max_abs", float(np.max(np.abs(droop))), "V")
    thadd("hold_droop_rms", float(math.sqrt(np.mean(droop*droop))), "V")
    thadd("hold_droop_max_abs", float(np.max(np.abs(droop)) / LSB), "LSB")
    unstable = 0; max_codes = 1
    adc_code = np.rint(d["v(adc_code)"]).astype(np.int32)
    for n in range(10000):
        a = np.searchsorted(t, n*1e-3 + 103e-6, side="left")
        b = np.searchsorted(t, n*1e-3 + 999e-6, side="right")
        count = len(np.unique(adc_code[a:b])) if b > a else 0
        max_codes = max(max_codes, count)
        unstable += count > 1
    thadd("hold_periods_with_multiple_codes", unstable, "periods", "Code changes caused by hold droop/quantizer boundary crossing are counted.")
    thadd("maximum_distinct_codes_in_one_hold", max_codes, "codes")
    thadd("valid_codes_exported", len(code), "samples", "Exactly one sample at 500 us phase per 1 ms period.")
    export_path = export_transient_uniform(d, variant)
    summary = {"variant": variant, "sample_path": sample_path, "export_path": export_path,
               "qrs_time": float(sample_t[int(np.argmax(np.abs(afe)))]),
               "sample_t": sample_t, "sample_afe": afe, "sample_hold": hold,
               "sample_code": code, "sample_signed": signed}
    if variant == "intent_aligned":
        mask_plot = (t >= 0) & (t <= 10)
        idx = np.flatnonzero(mask_plot)
        idx = idx[np.linspace(0, len(idx)-1, 12000).astype(int)]
        svg_line_plot(PLOTS/"patient_stage_waveforms.svg", "Patient ECG stage waveforms (0-10 s)", t[idx],
                      {"IA_OUT": d["v(ia_out)"][idx], "NOTCH_OUT": d["v(notch_out)"][idx], "AFE_OUT": d["v(afe_out)"][idx]},
                      "Time (s)", "Voltage (V)")
        idx = np.flatnonzero((t >= 1) & (t <= 10))
        idx = idx[np.linspace(0, len(idx)-1, 12000).astype(int)]
        svg_line_plot(PLOTS/"patient_stage_waveforms_after_settling.svg", "Patient ECG stage waveforms after settling (1-10 s)", t[idx],
                      {"IA_OUT": d["v(ia_out)"][idx], "NOTCH_OUT": d["v(notch_out)"][idx], "AFE_OUT": d["v(afe_out)"][idx]},
                      "Time (s)", "Voltage (V)")
        center = summary["qrs_time"]
        lo = max(1.0, center - .004); hi = min(10.0, center + .004)
        zoom = (t >= lo) & (t <= hi)
        valid = [x for x in sample_t if lo <= x <= hi]
        svg_line_plot(PLOTS/"track_hold_zoom.svg", "Track-and-hold QRS zoom", t[zoom],
                      {"AFE_OUT (V)": d["v(afe_out)"][zoom], "ADC_HOLD (V)": d["v(adc_hold)"][zoom], "CLK/20": d["v(clk)"][zoom]/20,
                       "ADC_CODE/16384": d["v(adc_code)"][zoom]/16384}, "Time (s)", "Scaled amplitude", False, (lo, hi), verticals=valid)
    del d
    gc.collect()
    return rows, th, summary


def timestep_convergence():
    wanted = {"time", "v(afe_out)", "v(adc_hold)", "v(adc_code)"}
    a = read_ascii_raw(RAW/"patient_th_short_10us.raw", wanted)
    b = read_ascii_raw(RAW/"patient_th_short_5us.raw", wanted)
    q = np.arange(300) * 1e-3 + .5e-3
    source = "schematics/transient_testbenches/patient_th_short_10us.cir"
    evidence = rel(RAW/"patient_th_short_10us.raw") + ";" + rel(RAW/"patient_th_short_5us.raw")
    rows = []
    for name, unit in (("v(afe_out)", "V"), ("v(adc_hold)", "V")):
        delta = interp(a["time"], a[name], q) - interp(b["time"], b[name], q)
        rows.append(row("TIMESTEP", "intent_aligned", source, "TRAN", f"10us_vs_5us.{name}.max_abs_difference", np.max(np.abs(delta)), unit, evidence))
        rows.append(row("TIMESTEP", "intent_aligned", source, "TRAN", f"10us_vs_5us.{name}.rms_difference", math.sqrt(np.mean(delta*delta)), unit, evidence))
    ca = np.rint(interp(a["time"], a["v(adc_code)"], q)).astype(int)
    cb = np.rint(interp(b["time"], b["v(adc_code)"], q)).astype(int)
    rows.append(row("TIMESTEP", "intent_aligned", source, "TRAN", "10us_vs_5us.code_mismatch_count", np.sum(ca != cb), "samples", evidence))
    qa = read_ascii_raw(RAW/"patient_th_qrs_10us.raw", wanted)
    qb = read_ascii_raw(RAW/"patient_th_qrs_5us.raw", wanted)
    q = np.arange(1830, 1860) * 1e-3 + .5e-3
    q_evidence = rel(RAW/"patient_th_qrs_10us.raw") + ";" + rel(RAW/"patient_th_qrs_5us.raw")
    for name, unit in (("v(afe_out)", "V"), ("v(adc_hold)", "V")):
        delta = interp(qa["time"], qa[name], q) - interp(qb["time"], qb[name], q)
        rows.append(row("TIMESTEP_QRS", "intent_aligned", "schematics/transient_testbenches/patient_th_qrs_10us.cir", "TRAN",
                        f"QRS_10us_vs_5us.{name}.max_abs_difference", np.max(np.abs(delta)), unit, q_evidence))
    ca = np.rint(interp(qa["time"], qa["v(adc_code)"], q)).astype(int)
    cb = np.rint(interp(qb["time"], qb["v(adc_code)"], q)).astype(int)
    rows.append(row("TIMESTEP_QRS", "intent_aligned", "schematics/transient_testbenches/patient_th_qrs_10us.cir", "TRAN",
                    "QRS_10us_vs_5us.code_mismatch_count", np.sum(ca != cb), "samples", q_evidence))
    track = np.arange(1830, 1860) * 1e-3 + 101.5e-6
    for label, data in (("10us", qa), ("5us", qb)):
        err = interp(data["time"], data["v(afe_out)"], track) - interp(data["time"], data["v(adc_hold)"], track)
        rows.append(row("TIMESTEP_QRS", "intent_aligned", f"schematics/transient_testbenches/patient_th_qrs_{label}.cir", "TRAN",
                        f"QRS_{label}.acquisition_error_max_abs", np.max(np.abs(err)), "V", q_evidence))
    full10 = read_ascii_raw(RAW/"patient_full_intent_aligned_10us.raw", wanted)
    full5 = read_ascii_raw(RAW/"patient_full_intent_aligned_5us.raw", wanted)
    q = np.arange(10000) * 1e-3 + .5e-3
    full_evidence = rel(RAW/"patient_full_intent_aligned_10us.raw") + ";" + rel(RAW/"patient_full_intent_aligned_5us.raw")
    for name, unit in (("v(afe_out)", "V"), ("v(adc_hold)", "V")):
        delta = interp(full10["time"], full10[name], q) - interp(full5["time"], full5[name], q)
        rows.append(row("TIMESTEP_FULL", "intent_aligned", "schematics/transient_testbenches/patient_full_intent_aligned_5us.cir", "TRAN",
                        f"full_10us_vs_5us.{name}.max_abs_difference", np.max(np.abs(delta)), unit, full_evidence))
        rows.append(row("TIMESTEP_FULL", "intent_aligned", "schematics/transient_testbenches/patient_full_intent_aligned_5us.cir", "TRAN",
                        f"full_10us_vs_5us.{name}.rms_difference", math.sqrt(np.mean(delta*delta)), unit, full_evidence))
    c10 = np.rint(interp(full10["time"], full10["v(adc_code)"], q)).astype(int)
    c5 = np.rint(interp(full5["time"], full5["v(adc_code)"], q)).astype(int)
    rows.append(row("TIMESTEP_FULL", "intent_aligned", "schematics/transient_testbenches/patient_full_intent_aligned_5us.cir", "TRAN",
                    "full_10us_vs_5us.code_mismatch_count", np.sum(c10 != c5), "samples", full_evidence))
    track = np.arange(10000) * 1e-3 + 101.5e-6
    for label, data in (("10us", full10), ("5us", full5)):
        err = interp(data["time"], data["v(afe_out)"], track) - interp(data["time"], data["v(adc_hold)"], track)
        rows.append(row("TIMESTEP_FULL", "intent_aligned", f"schematics/transient_testbenches/patient_full_intent_aligned_{label}.cir", "TRAN",
                        f"full_{label}.acquisition_error_max_abs", np.max(np.abs(err)), "V", full_evidence))
    peak5 = read_ascii_raw(RAW/"patient_th_acqpeak_5us.raw", wanted)
    peak25 = read_ascii_raw(RAW/"patient_th_acqpeak_2p5us.raw", wanted)
    track = np.arange(4990, 5015) * 1e-3 + 101.5e-6
    peak_evidence = rel(RAW/"patient_th_acqpeak_5us.raw") + ";" + rel(RAW/"patient_th_acqpeak_2p5us.raw")
    peak_values = {}
    for label, data in (("5us", peak5), ("2p5us", peak25)):
        err = interp(data["time"], data["v(afe_out)"], track) - interp(data["time"], data["v(adc_hold)"], track)
        peak_values[label] = float(np.max(np.abs(err)))
        rows.append(row("TIMESTEP_ACQ_PEAK", "intent_aligned", f"schematics/transient_testbenches/patient_th_acqpeak_{label}.cir", "TRAN",
                        f"acq_peak_{label}.acquisition_error_max_abs", peak_values[label], "V", peak_evidence))
    rows.append(row("TIMESTEP_ACQ_PEAK", "intent_aligned", "schematics/transient_testbenches/patient_th_acqpeak_2p5us.cir", "TRAN",
                    "acq_peak_5us_vs_2p5us.max_error_difference", abs(peak_values["5us"]-peak_values["2p5us"]), "V", peak_evidence))
    write_csv(TABLES/"timestep_convergence.csv", rows, COMMON_FIELDS)


def adc_mapping_metrics():
    step = read_ascii_raw(RAW/"adc_mapping_steps.raw")
    t = step["time"]
    points = [
        ("negative_out_of_range", .5e-3, 0, -2048), ("negative_endpoint", 1.5e-3, 0, -2048),
        ("zero_input", 2.5e-3, 2047, -1), ("positive_half_lsb", 3.5e-3, 2048, 0),
        ("positive_endpoint", 4.5e-3, 4095, 2047), ("positive_out_of_range", 5.5e-3, 4095, 2047),
    ]
    rows = []
    source = "schematics/transient_testbenches/adc_mapping_steps.cir"
    evidence = rel(RAW/"adc_mapping_steps.raw")
    for label, tp, expect_code, expect_signed in points:
        code = int(round(interp(t, step["v(adc_code)"], tp)))
        signed = int(round(interp(t, step["v(adc_signed)"], tp)))
        rows.append(row("ADC_MAP", "behavioral_adc", source, "TRAN", f"{label}.adc_code", code, "code", evidence,
                        expect_code, "", "MATCH" if code == expect_code else "MISMATCH"))
        rows.append(row("ADC_MAP", "behavioral_adc", source, "TRAN", f"{label}.adc_signed", signed, "code", evidence,
                        expect_signed, "", "MATCH" if signed == expect_signed else "MISMATCH"))
    dc = read_ascii_raw(RAW/"adc_mapping.raw")
    vin = dc["v(adc_hold)"]
    code = np.rint(dc["v(adc_code)"]).astype(int)
    signed = np.rint(dc["v(adc_signed)"]).astype(int)
    monotonic = bool(np.all(np.diff(code) >= 0))
    rows.append(row("ADC_MAP", "behavioral_adc", "schematics/transient_testbenches/adc_mapping.cir", "DC", "monotonicity", monotonic, "boolean", rel(RAW/"adc_mapping.raw"), True, "", "MATCH" if monotonic else "MISMATCH"))
    rows.append(row("ADC_MAP", "behavioral_adc", "schematics/transient_testbenches/adc_mapping.cir", "DC", "adc_code_range", f"{code.min()}..{code.max()}", "code", rel(RAW/"adc_mapping.raw"), "0..4095", "", "MATCH"))
    rows.append(row("ADC_MAP", "behavioral_adc", "schematics/transient_testbenches/adc_mapping.cir", "DC", "adc_signed_range", f"{signed.min()}..{signed.max()}", "code", rel(RAW/"adc_mapping.raw"), "-2048..2047", "", "MATCH"))
    i = int(np.argmin(np.abs(vin - 1.65)))
    rows.append(row("ADC_MAP", "behavioral_adc", "schematics/transient_testbenches/adc_mapping.cir", "DC", "dc_sweep_nearest_1p65V_code", code[i], "code", rel(RAW/"adc_mapping.raw"), 4095, "", "MEASURED",
                    "DC sweep accumulation represents the nominal +1.65 V point infinitesimally below endpoint; literal plateau test maps +1.65 V to 4095."))
    write_csv(TABLES/"adc_mapping_metrics.csv", rows, COMMON_FIELDS)
    svg_line_plot(PLOTS/"adc_mapping.svg", "Behavioral ADC transfer", vin, {"ADC_CODE": code.astype(float)}, "ADC input (V)", "Offset-binary code", False, (-1.8, 1.8), (-100, 4200))


def log_qc():
    rows = []
    fields = ["log_file", "simulation_completed", "direct_newton_failed", "gmin_recovered", "fatal_or_convergence_error", "notes"]
    log_paths = list((ROOT/"results"/"logs").glob("*.log"))
    log_paths += list((ROOT/"results"/"stress"/"logs").glob("*.log"))
    log_paths += list((ROOT/"results"/"finalized"/"logs").glob("*.log"))
    for p in sorted(log_paths):
        text = p.read_text(encoding="utf-8", errors="replace")
        completed = "Total elapsed time:" in text
        direct = "Direct Newton iteration failed" in text
        gmin = "Gmin stepping succeeded" in text
        fatal = any(s in text.lower() for s in ("timestep too small", "singular matrix", "fatal error", "could not converge"))
        rows.append({"log_file": rel(p), "simulation_completed": fmt(completed), "direct_newton_failed": fmt(direct),
                     "gmin_recovered": fmt(gmin), "fatal_or_convergence_error": fmt(fatal),
                     "notes": "Completed with recovered operating-point warning." if direct and gmin and not fatal else ""})
    write_csv(TABLES/"simulation_log_qc.csv", rows, fields)


def main():
    for d in (TABLES, PLOTS, NOMINAL):
        d.mkdir(parents=True, exist_ok=True)
    ac_metrics()
    adc_mapping_metrics()
    transient_rows = []
    th_rows = []
    for variant, filename in (("as_implemented", "patient_full_as_implemented_10us.raw"),
                              ("intent_aligned", "patient_full_intent_aligned_5us.raw")):
        a, b, _ = transient_metrics_for(variant, filename)
        transient_rows.extend(a); th_rows.extend(b)
    write_csv(TABLES/"nominal_transient_metrics.csv", transient_rows, COMMON_FIELDS)
    write_csv(TABLES/"track_hold_metrics.csv", th_rows, COMMON_FIELDS)
    timestep_convergence()
    log_qc()


if __name__ == "__main__":
    main()
