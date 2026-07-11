#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# full WFDB record -> 1kSPS(linear) -> AFE+ADC -> signed 12-bit .mem (record 전체 스트림).
#  구조: <OUT>/<split>/<class>/<record>.mem  + manifest CSV
#  사용: python3 afe_fullrec_gen.py <pilot N | full>
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, sys, csv, time, glob
import numpy as np
sys.path.insert(0, _ROOT + "/scripts")
from afe_full import read_record_1ksps, afe_adc_unsigned

HANDOFF = "/mnt/c/Users/USER/Downloads/handoff_to_suhwan/handoff_to_suhwan"
SEL_MAN = HANDOFF + "/selected_records_manifest.csv"
STRICT_MAN_GLOB = _ROOT + "/datasets/strict60_large/afe_manifest_*_strict60_large.csv"
ECG = _ROOT + ""

mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"
N = int(sys.argv[2]) if (mode == "pilot" and len(sys.argv) > 2) else 3
OUT = ECG + ("/datasets/fullrec_afe_pilot" if mode == "pilot" else "/datasets/fullrec_afe")

# record_id -> split : 기존 프로젝트의 record-wise split 전부에서 도출
#   (1) strict60_large manifest  (2) strict_varlen manifest)  먼저 등록된 값 우선.
split_of = {}
for mf in glob.glob(STRICT_MAN_GLOB):
    sp = os.path.basename(mf).split("_")[2]  # afe_manifest_<split>_strict60_large.csv
    for r in csv.DictReader(open(mf, newline="", encoding="utf-8-sig")):
        split_of.setdefault(str(r["record_id"]), sp)
for mf in glob.glob(ECG + "/datasets/strict_varlen/*/dataset_manifest_*_meta.csv"):
    sp = os.path.basename(mf).split("_")[2]  # dataset_manifest_<split>_varlen_meta.csv
    for r in csv.DictReader(open(mf, newline="", encoding="utf-8-sig")):
        rid = str(r.get("record") or r.get("record_id") or "")
        if rid:
            split_of.setdefault(rid, sp)
print(f"split map: {len(split_of)} records known", flush=True)

# 선택 record 목록 (include_main=True)
recs = []
for r in csv.DictReader(open(SEL_MAN, newline="", encoding="utf-8-sig")):
    if r["include_main"].strip().lower() == "true":
        recs.append((r["class"], r["record_id"], r["database"]))

# 클래스별 정렬, pilot이면 N개씩
from collections import defaultdict, OrderedDict
byc = OrderedDict()
for c, rid, db in recs:
    byc.setdefault(c, []).append((rid, db))
sel = []
for c in ["NSR", "CHF", "ARR", "AFF"]:
    lst = byc.get(c, [])
    sel += [(c, rid, db) for rid, db in (lst[:N] if mode == "pilot" else lst)]

print(f"mode={mode} records={len(sel)} OUT={OUT}", flush=True)
rows = []
t0 = time.time()
for c, rid, db in sel:
    rec_path = f"{HANDOFF}/selected_records/{c}/{rid}/{rid}"
    sp = split_of.get(str(rid), "unassigned")
    try:
        x1k, fs, nsrc = read_record_1ksps(rec_path)
    except Exception as e:
        print(f"  SKIP {c}/{rid}: {e}", flush=True); continue
    u = afe_adc_unsigned(x1k)            # unsigned 0..4095
    s12 = ((u - 2048) & 0xFFF).astype(np.int32)   # signed 2's-comp 12-bit hex value
    d = os.path.join(OUT, sp, c); os.makedirs(d, exist_ok=True)
    outp = os.path.join(d, f"{rid}.mem")
    hexlut = np.array([f"{i:03x}" for i in range(4096)])
    with open(outp, "w") as f:
        CH = 2_000_000
        for i in range(0, len(s12), CH):
            f.write("\n".join(hexlut[s12[i:i+CH]])); f.write("\n")
    rows.append(dict(split=sp, class_label=c, record_id=rid, source_db=db,
                     original_record_file=f"{db}/{rid}.dat",
                     afe_adc_mem_file=f"{os.path.basename(OUT)}/{sp}/{c}/{rid}.mem",
                     sample_rate=1000, adc_format="signed12",
                     total_samples=len(u), total_duration_sec=round(len(u)/1000.0, 3),
                     settling_skip_sec=2,
                     notes=f"native_fs={int(fs)};linear_resample;xmodelmatch_emulator"))
    print(f"  [{c}/{rid}] split={sp} fs={int(fs)} n={len(u)} ({len(u)/1000/3600:.2f}h) {time.time()-t0:.0f}s", flush=True)

man = os.path.join(OUT, "fullrec_manifest.csv")
with open(man, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
unassigned = [(r["class_label"], r["record_id"]) for r in rows if r["split"] == "unassigned"]
print(f"DONE {len(rows)} records, manifest={man}, {time.time()-t0:.0f}s", flush=True)
print(f"split 분포: " + ", ".join(f"{s}={sum(1 for r in rows if r['split']==s)}" for s in ["train","val","test","unassigned"]), flush=True)
if unassigned:
    print(f"UNASSIGNED({len(unassigned)}): " + ", ".join(f"{c}/{r}" for c, r in unassigned), flush=True)
