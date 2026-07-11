#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AFE 최초 입력(원본 digitized ECG)을 MATLAB 친화 CSV로 변환.
#  입력: data/mem_{NSR,CHF,ARR,AFF}.mem  (signed 12-bit hex, 1kSPS, 60s)
#  출력: afe_input_dataset/afe_input_{class}.csv  (sample_index,time_s,code_signed,voltage_V)
#        + real_ecg_100(360Hz native NSR record 100) → afe_input_record100_NSR.csv
#  스케일: voltage_V = code_signed / 200000  (= AFE .sv 주입식과 동일)
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, csv
ROOT = _ROOT + ""
OUT = os.path.join(ROOT, "afe_input_dataset")
os.makedirs(OUT, exist_ok=True)
FS = 1000.0
SCALE = 1.0 / 200000.0

def sgn(v):
    return v - 4096 if v > 2047 else v

def conv_mem(cls):
    src = os.path.join(ROOT, "data", f"mem_{cls}.mem")
    dst = os.path.join(OUT, f"afe_input_{cls}.csv")
    rows = []
    with open(src) as f:
        for i, l in enumerate(f):
            l = l.strip()
            if not l:
                continue
            c = sgn(int(l, 16))
            rows.append((i, round(i / FS, 6), c, round(c * SCALE, 8)))
    with open(dst, "w", newline="") as o:
        w = csv.writer(o)
        w.writerow(["sample_index", "time_s", "code_signed", "voltage_V"])
        w.writerows(rows)
    codes = [r[2] for r in rows]
    print(f"{cls}: {len(rows)} samples  code[{min(codes)}..{max(codes)}]  "
          f"V[{min(codes)*SCALE:.5f}..{max(codes)*SCALE:.5f}] -> {os.path.basename(dst)}")
    return len(rows), min(codes), max(codes)

def conv_pwl100():
    src = os.path.join(ROOT, "data", "real_ecg_100.pwl")
    if not os.path.exists(src):
        return
    dst = os.path.join(OUT, "afe_input_record100_NSR.csv")
    rows = []
    with open(src) as f:
        for l in f:
            p = l.split()
            if len(p) == 2:
                t, v = float(p[0]), float(p[1])
                rows.append((round(t, 6), round(v, 8), round(v * 200000)))
    with open(dst, "w", newline="") as o:
        w = csv.writer(o)
        w.writerow(["time_s", "voltage_V", "code_signed_est"])
        w.writerows(rows)
    print(f"record100(NSR, 360Hz native): {len(rows)} pts -> {os.path.basename(dst)}")

if __name__ == "__main__":
    summ = []
    for cls in ["NSR", "CHF", "ARR", "AFF"]:
        summ.append((cls,) + conv_mem(cls))
    conv_pwl100()
    print("DONE ->", OUT)
