#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [2.1 final_pred] 깨끗한 30분 chunk의 signed code에 ADC 비이상성 주입 → 섭동 .mem 생성.
#  code_signed ∝ Vin(중심0)이므로: gain→×(1+g), offset→+LSB, noise→+N(0,σ), jitter→시점 재표본.
#  clip[-2048,2047] 후 signed 3-hex 재인코드. XSim은 이후 직렬 실행.
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, sys, csv
import numpy as np
ECG = _ROOT + ""
CLEAN = ECG + "/sim_out/chunks36"
OUT = ECG + "/sim_out/chunks_pert"
os.makedirs(OUT, exist_ok=True)
FS = 1000.0
SEED = 2024

# (case파일, source_case_id, expected_class) — 대표 4클래스(경계 ARR105 포함)
CHUNKS = [
    ("ARR_mitdb_105_chunk00",  37, 2),   # golden ARR 8/1/21/0 (경계, 구통합 실패했던 레코드)
    ("NSR_nsrdb_16483_chunk10", 110, 0), # golden NSR 30/0/0/0
    ("CHF_chfdb_chf09_chunk29", 91, 1),  # golden CHF 0/29/0/1
    ("AFF_afdb_06995_chunk16",  16, 3),  # golden AFF 0/0/0/30
]
# (라벨, kwargs) 최악 수준
PERTS = [
    ("off+5",   dict(off=5.0)),
    ("gain+1%", dict(gain=0.01)),
    ("noise2",  dict(noise=2.0)),
    ("jit100u", dict(jitter=100.0)),
]

def read_signed(path):
    out = []
    with open(path) as f:
        for l in f:
            l = l.strip()
            if l:
                h = int(l, 16); out.append(h - 4096 if h > 2047 else h)
    return np.asarray(out, dtype=np.float64)

def perturb(code, off=0.0, gain=0.0, noise=0.0, jitter=0.0, rng=None):
    v = code.copy()
    if jitter > 0:
        idx = np.arange(len(v)) + rng.normal(0, jitter * 1e-6 * FS, len(v))
        v = np.interp(idx, np.arange(len(v)), v)
    v = v * (1.0 + gain) + off
    if noise > 0:
        v = v + rng.normal(0, noise, len(v))
    return np.clip(np.floor(v).astype(np.int64), -2048, 2047)

def write_mem(path, codes):
    with open(path, "w", newline="\n") as o:
        o.write("\n".join(f"{int(c) & 0xFFF:03x}" for c in codes))
        o.write("\n")

rows = []
cid = 1000
for name, srccase, cls in CHUNKS:
    clean = read_signed(os.path.join(CLEAN, name + ".mem"))
    for lbl, kw in PERTS:
        rng = np.random.default_rng(SEED)
        pc = perturb(clean, rng=rng, **kw)
        fn = f"{name}__{lbl}.mem"
        write_mem(os.path.join(OUT, fn), pc)
        rows.append(dict(manifest_id=cid, base_case=name, src_case_id=srccase,
                         expected_class=cls, perturb=lbl, mem=f"chunks_pert/{fn}"))
        cid += 1
with open(OUT + "/pert_map.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(OUT + "/manifest_pert.txt", "w", newline="\n") as m:
    for r in rows:
        m.write(f"{r['manifest_id']} {r['expected_class']} 1800000 {r['mem']}\n")
print(f"generated {len(rows)} perturbed chunks -> {OUT}")
print("manifest_pert.txt + pert_map.csv written")
