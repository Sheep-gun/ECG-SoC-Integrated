#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 나머지 원본 WFDB record -> full-record AFE+ADC (fullrec_afe와 동일 조건) -> signed12 .mem
#  입력: handoff_to_suhwan_remaining_records / remaining_original_records/<class>/<rec>/
#  출력: datasets/fullrec_afe_remaining/<split>/<class>/<rec>.mem + manifest
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, sys, csv, time, glob
import numpy as np
sys.path.insert(0, _ROOT + "/scripts")
from afe_full import read_record_1ksps, afe_adc_unsigned

ROOT = "/mnt/c/Users/USER/Downloads/handoff_remaining/handoff_to_suhwan_remaining_records"
MAN_IN = ROOT + "/remaining_records_manifest.csv"
RECDIR = ROOT + "/remaining_original_records"
ECG = _ROOT + ""
OUT = ECG + "/datasets/fullrec_afe_remaining"

# split map: 기존 record-wise split (strict60_large + strict_varlen)
split_of = {}
for mf in glob.glob(ECG + "/datasets/strict60_large/afe_manifest_*_strict60_large.csv"):
    sp = os.path.basename(mf).split("_")[2]
    for r in csv.DictReader(open(mf, newline="", encoding="utf-8-sig")):
        split_of.setdefault(str(r["record_id"]), sp)
for mf in glob.glob(ECG + "/datasets/strict_varlen/*/dataset_manifest_*_meta.csv"):
    sp = os.path.basename(mf).split("_")[2]
    for r in csv.DictReader(open(mf, newline="", encoding="utf-8-sig")):
        rid = str(r.get("record") or r.get("record_id") or "")
        if rid:
            split_of.setdefault(rid, sp)
print(f"split map: {len(split_of)} records known", flush=True)

recs = [(r["class"], r["record_id"], r["database"]) for r in
        csv.DictReader(open(MAN_IN, newline="", encoding="utf-8-sig"))]
print(f"records to convert: {len(recs)}  OUT={OUT}", flush=True)

hexlut = np.array([f"{i:03x}" for i in range(4096)])
rows = []; t0 = time.time()
for c, rid, db in recs:
    rec_path = f"{RECDIR}/{c}/{rid}/{rid}"
    sp = split_of.get(str(rid), "unassigned")
    try:
        x1k, fs, nsrc = read_record_1ksps(rec_path)
    except Exception as e:
        print(f"  SKIP {c}/{rid}: {e}", flush=True); continue
    u = afe_adc_unsigned(x1k)
    s12 = ((u - 2048) & 0xFFF).astype(np.int32)
    d = os.path.join(OUT, sp, c); os.makedirs(d, exist_ok=True)
    outp = os.path.join(d, f"{rid}.mem")
    with open(outp, "w") as f:
        CH = 2_000_000
        for i in range(0, len(s12), CH):
            f.write("\n".join(hexlut[s12[i:i+CH]])); f.write("\n")
    rows.append(dict(split=sp, class_label=c, record_id=rid, source_db=db,
                     original_record_file=f"{db}/{rid}.dat",
                     afe_adc_mem_file=f"fullrec_afe_remaining/{sp}/{c}/{rid}.mem",
                     sample_rate=1000, adc_format="signed12",
                     total_samples=len(u), total_duration_sec=round(len(u) / 1000.0, 3),
                     settling_skip_sec=2,
                     notes=f"native_fs={int(fs)};linear_resample;xmodelmatch_emulator"))
    print(f"  [{c}/{rid}] split={sp} fs={int(fs)} n={len(u)} ({len(u)/1000/3600:.2f}h) {time.time()-t0:.0f}s", flush=True)

man = os.path.join(OUT, "fullrec_remaining_manifest.csv")
with open(man, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"DONE {len(rows)} records, manifest={man}, {time.time()-t0:.0f}s", flush=True)
print("split 분포: " + ", ".join(f"{s}={sum(1 for r in rows if r['split']==s)}" for s in ["train", "val", "test", "unassigned"]), flush=True)
ua = [(r['class_label'], r['record_id']) for r in rows if r['split'] == 'unassigned']
if ua:
    print(f"UNASSIGNED({len(ua)}): " + ", ".join(f"{c}/{r}" for c, r in ua), flush=True)
