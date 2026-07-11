#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [검증 2.3] R-peak timing / morphology preservation
#   원본 ECG(.mem raw) vs AFE 출력에서 R-peak 위치·RR interval 보존 정량화.
#   대상: strict60_large/raw/test (분류기 test 60s 세그) 전체 = "final_test"
#   측정: R-peak timing shift[ms](중앙값=군지연, 표준편차=지터), 매칭율/누락,
#         RR interval error[ms](군지연 불변), QRS 대역 상관도
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, sys, glob, csv
import numpy as np
sys.path.insert(0, _ROOT + "/scripts")
from afe_analysis_lib import (read_mem_signed, afe_float, quantize,
                              detect_rpeaks, match_peaks, rr_intervals, fs)

ECG = _ROOT + ""
OUTDIR = ECG + "/docs/afe_stress"; os.makedirs(OUTDIR, exist_ok=True)
SETTLE = 2000

def one_record(path):
    raw = read_mem_signed(path)
    if len(raw) < 3 * SETTLE:
        return None
    afe_v = afe_float(raw)
    afe_code = quantize(afe_v).astype(float)          # ideal ADC
    # 정착구간 제외
    raw_b = raw[SETTLE:]; afe_b = afe_code[SETTLE:]
    pr = detect_rpeaks(raw_b)
    pa = detect_rpeaks(afe_b)
    if len(pr) < 3:
        return None
    shifts, nm, miss = match_peaks(pr, pa, tol_ms=60)
    rr_raw = rr_intervals(pr); rr_afe = rr_intervals(pa)
    # RR 비교: 공통 길이만 (peak 수 다를 수 있음)
    k = min(len(rr_raw), len(rr_afe))
    rr_err = np.abs(rr_raw[:k] - rr_afe[:k]) if k > 0 else np.array([])
    # QRS 대역 형태 상관도 (군지연 보정 후)
    lag = int(round(np.median(shifts))) if len(shifts) else 0
    a = afe_b.astype(float)
    if lag > 0:
        corr_ref = raw_b[:-lag] if lag < len(raw_b) else raw_b
        corr_afe = a[lag:lag + len(corr_ref)]
    elif lag < 0:
        corr_afe = a[:lag]; corr_ref = raw_b[-lag:-lag + len(corr_afe)]
    else:
        corr_ref = raw_b[:len(a)]; corr_afe = a[:len(corr_ref)]
    m = min(len(corr_ref), len(corr_afe))
    corr = float(np.corrcoef(corr_ref[:m], corr_afe[:m])[0, 1]) if m > 10 else float("nan")
    return dict(
        n_rpeak_raw=len(pr), n_rpeak_afe=len(pa), matched=nm, missed=miss,
        match_pct=round(100.0 * nm / len(pr), 2),
        shift_med_ms=round(float(np.median(shifts)), 2) if len(shifts) else None,
        shift_std_ms=round(float(np.std(shifts)), 2) if len(shifts) else None,
        shift_p95_ms=round(float(np.percentile(np.abs(shifts), 95)), 2) if len(shifts) else None,
        rr_err_med_ms=round(float(np.median(rr_err)), 2) if len(rr_err) else None,
        rr_err_max_ms=round(float(np.max(rr_err)), 2) if len(rr_err) else None,
        corr=round(corr, 4))

def main():
    files = sorted(glob.glob(ECG + "/datasets/strict60_large/raw/test/*/*.mem"))
    print(f"[2.3] R-peak timing 검증 — raw/test {len(files)} 세그", flush=True)
    rows = []
    for p in files:
        cls = os.path.basename(os.path.dirname(p))
        rid = os.path.splitext(os.path.basename(p))[0]
        try:
            r = one_record(p)
        except Exception as e:
            print(f"  SKIP {cls}/{rid}: {e}", flush=True); continue
        if r is None:
            continue
        r.update(class_label=cls, record_id=rid)
        rows.append(r)
    if not rows:
        print("no usable records"); return
    def col(k):
        return np.array([r[k] for r in rows if r[k] is not None], float)
    print(f"\n=== 요약 (n={len(rows)} 세그) ===")
    print(f"  R-peak 매칭율(중앙값)   : {np.median(col('match_pct')):.2f} %")
    print(f"  최저 매칭율             : {col('match_pct').min():.2f} %")
    print(f"  timing shift 중앙값(군지연): {np.median(col('shift_med_ms')):.2f} ms")
    print(f"  timing 지터 std(중앙값)  : {np.median(col('shift_std_ms')):.2f} ms")
    print(f"  timing shift |p95|(최대) : {col('shift_p95_ms').max():.2f} ms")
    print(f"  RR interval err 중앙값   : {np.median(col('rr_err_med_ms')):.2f} ms")
    print(f"  RR interval err 최대     : {col('rr_err_max_ms').max():.2f} ms")
    print(f"  QRS대역 상관도 중앙값    : {np.median(col('corr')):.4f}")
    outp = os.path.join(OUTDIR, "rpeak_timing_test.csv")
    with open(outp, "w", newline="") as f:
        cols = ["class_label", "record_id", "n_rpeak_raw", "n_rpeak_afe", "matched", "missed",
                "match_pct", "shift_med_ms", "shift_std_ms", "shift_p95_ms",
                "rr_err_med_ms", "rr_err_max_ms", "corr"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({c: r[c] for c in cols})
    print(f"\nCSV -> {outp}")

if __name__ == "__main__":
    main()
