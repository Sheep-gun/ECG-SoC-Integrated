#!/usr/bin/env python3
"""Compare fixed-commit MATLAB nominal output with LTspice valid-phase samples."""

import csv
import math
from pathlib import Path

import numpy as np

from parse_results import ROOT, TABLES, PLOTS, NOMINAL, COMMON_FIELDS, row, write_csv, svg_line_plot, rel


def load_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def aligned(a, b, lag):
    if lag > 0:
        return a[lag:], b[:-lag]
    if lag < 0:
        return a[:lag], b[-lag:]
    return a, b


def metrics(a, b):
    e = a.astype(float) - b.astype(float)
    corr = float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else float("nan")
    return {"mean_error": np.mean(e), "mae": np.mean(np.abs(e)),
            "rms_error": math.sqrt(np.mean(e*e)), "max_abs_error": np.max(np.abs(e)),
            "correlation": corr}


def best_lag(a, b, limit=100):
    best = None
    for lag in range(-limit, limit + 1):
        aa, bb = aligned(a, b, lag)
        c = float(np.corrcoef(aa, bb)[0, 1])
        if best is None or c > best[1]:
            best = (lag, c)
    return best


def main():
    lt_path = NOMINAL / "ltspice_adc_samples.csv"
    ml_path = NOMINAL / "matlab_fixed_execution" / "matlab_fixed_patient100_output.csv"
    lt = load_csv(lt_path); ml = load_csv(ml_path)
    lt_t = np.array([float(r["time_s"]) for r in lt])
    ml_t = np.array([float(r["time_s"]) for r in ml])
    lt_code = np.array([int(r.get("direct_adc_signed", r["adc_signed"])) for r in lt])
    ml_code = np.array([int(float(r["adc_signed"])) for r in ml])
    ml_afe = np.array([float(r["v_lpf"]) for r in ml])
    rows = []
    source = "reference/matlab_fixed_907f7e1@907f7e1f081a9d6a5703a32095d962143315a192"
    evidence = rel(lt_path) + ";" + rel(ml_path)
    rows.append(row("MATLAB_ALIGN", "fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "sample_count_ltspice", len(lt_code), "samples", evidence, 10000, "", "MATCH" if len(lt_code)==10000 else "MISMATCH"))
    rows.append(row("MATLAB_ALIGN", "fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "sample_count_matlab", len(ml_code), "samples", evidence, 10000, "", "MATCH" if len(ml_code)==10000 else "MISMATCH"))
    offset = float(lt_t[0] - ml_t[0])
    rows.append(row("MATLAB_ALIGN", "fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "first_sample_time_offset_lt_minus_matlab", offset, "s", evidence,
                    notes="XMODEL-aligned LTspice direct aperture starts at 1.000 ms; fixed MATLAB output starts at 0 s."))
    rows.append(row("MATLAB_ALIGN", "fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "matlab_clipping_count", int(np.sum(np.abs(ml_afe)>=1.65)), "samples", evidence))
    rows.append(row("MATLAB_ALIGN", "fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "ltspice_clipping_count", int(np.sum(np.array([abs(float(r['adc_hold_v'])) for r in lt])>1.65)), "samples", evidence))
    for window, start in (("full", 0), ("settled_after_1s", 1000)):
        a, b = lt_code[start:], ml_code[start:]
        z = metrics(a, b)
        for name, value in z.items():
            unit = "ratio" if name == "correlation" else "LSB"
            rows.append(row("MATLAB_ZERO_LAG", f"{window}.fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", name, value, unit, evidence,
                            notes="Index-aligned comparison; LTspice first aperture is 1.000 ms and MATLAB first sample is 0 s."))
        rows.append(row("MATLAB_ZERO_LAG", f"{window}.fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "ltspice_code_min", int(a.min()), "code", evidence))
        rows.append(row("MATLAB_ZERO_LAG", f"{window}.fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "ltspice_code_max", int(a.max()), "code", evidence))
        rows.append(row("MATLAB_ZERO_LAG", f"{window}.fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "matlab_code_min", int(b.min()), "code", evidence))
        rows.append(row("MATLAB_ZERO_LAG", f"{window}.fixed_matlab_vs_xmodel_aligned_ltspice", source, "CROSS_MODEL", "matlab_code_max", int(b.max()), "code", evidence))
        lag, corr = best_lag(a, b)
        aa, bb = aligned(a, b, lag)
        q = metrics(aa, bb)
        rows.append(row("MATLAB_BEST_LAG", f"{window}.diagnostic_only", source, "CROSS_MODEL", "lag_at_max_cross_correlation", lag, "samples", evidence,
                        notes="Positive lag means LTspice indices are dropped from the beginning; data were not silently shifted in zero-lag results."))
        rows.append(row("MATLAB_BEST_LAG", f"{window}.diagnostic_only", source, "CROSS_MODEL", "lag_at_max_cross_correlation", lag, "ms", evidence))
        for name, value in q.items():
            unit = "ratio" if name == "correlation" else "LSB"
            rows.append(row("MATLAB_BEST_LAG", f"{window}.diagnostic_only", source, "CROSS_MODEL", name, value, unit, evidence,
                            notes="Diagnostic best-lag overlap only; not used to replace zero-lag comparison."))
    write_csv(TABLES/"matlab_ltspice_comparison.csv", rows, COMMON_FIELDS)
    svg_line_plot(PLOTS/"matlab_ltspice_waveform_comparison.svg", "MATLAB and LTspice signed-code comparison", lt_t,
                  {"LTspice": lt_code.astype(float), "MATLAB": ml_code.astype(float)}, "Time (s)", "Signed code")
    err = lt_code.astype(float) - ml_code.astype(float)
    svg_line_plot(PLOTS/"matlab_ltspice_error.svg", "Zero-lag signed-code error", lt_t, {"LTspice - MATLAB": err}, "Time (s)", "Error (LSB)")
    settled = [r for r in rows if r["variant"].startswith("settled_after_1s") and r["test_id"] == "MATLAB_ZERO_LAG"]
    vals = {r["metric"]: r["measured"] for r in settled}
    best = [r for r in rows if r["variant"] == "settled_after_1s.diagnostic_only" and r["metric"] == "lag_at_max_cross_correlation" and r["unit"] == "samples"][0]
    report = f"""# MATLAB–LTspice nominal 비교 해석

## 확인된 사실

- MATLAB source는 fixed commit `907f7e1f081a9d6a5703a32095d962143315a192`의 함수들을 실행했다.
- 두 결과의 sample count는 각각 10,000이다.
- fixed MATLAB output은 0 s에서 시작하고 XMODEL-aligned LTspice direct aperture는 1.000 ms에서 시작한다.
- index-aligned 정착 후 MAE는 {vals['mae']} LSB, RMS error는 {vals['rms_error']} LSB, correlation은 {vals['correlation']}이다.
- 정착 후 best-lag diagnostic은 {best['measured']} samples이며 zero-lag 결과를 대체하지 않는다.

## 해석과 한계

MATLAB은 digital HPF/notch/LPF 수식 모델이고 LTspice는 continuous-time R/C와 analog Twin-T를 사용한다. 따라서 bit-exact 일치는 요구하지 않으며, 이 비교는 nominal intent의 polarity, range, sampling 및 gross waveform consistency 진단으로 제한한다. 최종 LTspice 상관 gate의 기준은 MATLAB이 아니라 fixed XMODEL이다.
"""
    (ROOT/"report"/"matlab_ltspice_interpretation_ko.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
