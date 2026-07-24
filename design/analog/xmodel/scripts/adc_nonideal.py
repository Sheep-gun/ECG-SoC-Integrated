#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [검증 2.1] ADC non-ideal sweep
#   기준(ideal 12-bit ADC) 대비 offset/gain/noise/jitter 주입 시 영향 정량화.
#   대상: strict60_large/raw/test 전체(=final_test 세그).  AFE는 검증된 emulator.
#   측정(세그 평균): ADC code RMS 편차[LSB], max 편차[LSB], clipping 증가,
#                   R-peak timing shift[ms], R-peak 개수변화, RR interval err[ms]
#   주: final_pred(분류결과) 변화는 SNN 통합경로(검증 1.5) 필요 → 여기선 AFE/ADC측 지표까지.
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
SEED = 12345

# (label, kwargs) — quantize()에 전달할 non-ideal 파라미터
CASES = [
    ("ideal",          dict()),
    ("offset +1LSB",   dict(off_lsb=+1)),
    ("offset +2LSB",   dict(off_lsb=+2)),
    ("offset +5LSB",   dict(off_lsb=+5)),
    ("offset -5LSB",   dict(off_lsb=-5)),
    ("gain +0.5%",     dict(gain_err=+0.005)),
    ("gain +1%",       dict(gain_err=+0.01)),
    ("gain -1%",       dict(gain_err=-0.01)),
    ("noise 0.5LSBrms", dict(noise_lsb=0.5)),
    ("noise 1LSBrms",  dict(noise_lsb=1.0)),
    ("noise 2LSBrms",  dict(noise_lsb=2.0)),
    ("jitter 10us",    dict(jitter_us=10)),
    ("jitter 50us",    dict(jitter_us=50)),
    ("jitter 100us",   dict(jitter_us=100)),
]

def eval_record(afe_v, base_code, base_pk, base_rr, kwargs):
    rng = np.random.default_rng(SEED)
    code = quantize(afe_v, rng=rng, **kwargs).astype(float)
    cb = code[SETTLE:]
    dev = cb - base_code
    rms = float(np.sqrt(np.mean(dev * dev)))
    mx = float(np.max(np.abs(dev)))
    clip = int(((cb == 0) | (cb == 4095)).sum())
    pk = detect_rpeaks(cb)
    shifts, nm, miss = match_peaks(base_pk, pk, tol_ms=60) if len(base_pk) else (np.array([]), 0, 0)
    rr = rr_intervals(pk)
    k = min(len(base_rr), len(rr))
    rr_err = float(np.max(np.abs(base_rr[:k] - rr[:k]))) if k > 0 else 0.0
    return dict(rms=rms, maxdev=mx, clip=clip,
                dnpeak=len(pk) - len(base_pk),
                shift_p95=float(np.percentile(np.abs(shifts), 95)) if len(shifts) else 0.0,
                missed=miss, rr_err_max=rr_err)

def main():
    files = sorted(glob.glob(ECG + "/datasets/strict60_large/raw/test/*/*.mem"))
    print(f"[2.1] ADC non-ideal sweep — raw/test {len(files)} 세그", flush=True)
    # 세그별로 모든 case 평가 → case별 누적
    agg = {lbl: [] for lbl, _ in CASES}
    used = 0
    for p in files:
        raw = read_mem_signed(p)
        if len(raw) < 3 * SETTLE:
            continue
        afe_v = afe_float(raw)
        base_code = quantize(afe_v)[SETTLE:].astype(float)   # ideal 기준
        base_pk = detect_rpeaks(base_code)
        base_rr = rr_intervals(base_pk)
        if len(base_pk) < 3:
            continue
        used += 1
        for lbl, kw in CASES:
            agg[lbl].append(eval_record(afe_v, base_code, base_pk, base_rr, kw))
    print(f"  사용 세그 = {used}\n")
    # case별 세그평균 표
    hdr = f"{'case':<15} {'RMSdev':>7} {'maxdev':>7} {'ΔclipΣ':>7} {'Δpeakμ':>7} {'shiftp95':>9} {'missΣ':>6} {'RRerrMax':>9}"
    print(hdr); print("-" * len(hdr))
    rows = []
    for lbl, _ in CASES:
        L = agg[lbl]
        rms = np.mean([r['rms'] for r in L])
        mx = np.mean([r['maxdev'] for r in L])
        clip = sum(r['clip'] for r in L)
        dnp = np.mean([r['dnpeak'] for r in L])
        sh = np.mean([r['shift_p95'] for r in L])
        miss = sum(r['missed'] for r in L)
        rr = np.max([r['rr_err_max'] for r in L])
        print(f"{lbl:<15} {rms:>7.3f} {mx:>7.1f} {clip:>7d} {dnp:>7.2f} {sh:>9.2f} {miss:>6d} {rr:>9.1f}")
        rows.append(dict(case=lbl, rms_dev_lsb=round(rms, 4), max_dev_lsb=round(mx, 2),
                         clip_total=clip, dpeak_mean=round(dnp, 3), shift_p95_ms=round(sh, 3),
                         missed_total=miss, rr_err_max_ms=round(rr, 2), n_seg=used))
    print("\n주: RMSdev/maxdev = ideal ADC 대비 code 편차, ΔclipΣ = 전세그 clipping 합,")
    print("   Δpeakμ = R-peak 개수변화 평균, shiftp95 = R-peak timing |shift| p95 평균,")
    print("   missΣ = 매칭실패 합, RRerrMax = RR interval 최대오차. final_pred는 1.5 통합필요.")
    outp = os.path.join(OUTDIR, "adc_nonideal_test.csv")
    with open(outp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nCSV -> {outp}")

if __name__ == "__main__":
    main()
