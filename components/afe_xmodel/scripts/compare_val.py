#!/usr/bin/env python3
# XMODEL/Questa simulation(xmodel/*.adc) vs 에뮬레이터(emu/*.adc) 샘플단위 비교.
#  HPF 정착(앞 3s) 제외, 소량 lag(-3..3) 탐색해 RMS/max 오차(LSB) 보고.
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os
W = _ROOT + '/sim_out/afe_val'
SKIP = 3000


def load(p):
    return [int(x) for x in open(p) if x.strip()]


def best_lag(a, b):
    best = None
    for lag in range(-3, 4):
        errs = []
        n = min(len(a), len(b))
        for i in range(SKIP, n - 3):
            j = i + lag
            if 0 <= j < len(b):
                errs.append(a[i] - b[j])
        if not errs:
            continue
        rms = (sum(e * e for e in errs) / len(errs)) ** 0.5
        mx = max(abs(e) for e in errs)
        if best is None or rms < best[1]:
            best = (lag, rms, mx)
    return best


tot_rms = []
for line in open(W + '/list.txt'):
    base = line.strip()[:-4]
    xp, ep = W + '/xmodel/' + base + '.adc', W + '/emu/' + base + '.adc'
    if not (os.path.exists(xp) and os.path.exists(ep)):
        print(f"{base}: MISSING (xmodel={os.path.exists(xp)} emu={os.path.exists(ep)})")
        continue
    x, e = load(xp), load(ep)
    if len(x) < SKIP + 100:
        print(f"{base}: xmodel too short n={len(x)}")
        continue
    lag, rms, mx = best_lag(x, e)
    tot_rms.append(rms)
    cls = base.split('_')[1]
    print(f"{cls:3s} {base}: nX={len(x)} nE={len(e)} lag={lag:+d} RMS={rms:6.2f} LSB  maxabs={mx:4d} LSB  (X range {min(x)}~{max(x)})")
if tot_rms:
    print(f"\nOVERALL mean RMS = {sum(tot_rms)/len(tot_rms):.2f} LSB over {len(tot_rms)} segments")
