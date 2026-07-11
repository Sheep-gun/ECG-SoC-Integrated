#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [1.4 재현성] emu↔XModel 정합에 쓴 36개 60s 세그먼트 목록 CSV (건이형 권장 컬럼).
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, csv
ECG = _ROOT + ""
LIST = ECG + "/sim_out/afe_val/list.txt"
OUT = ECG + "/docs/afe_stress/afe_val36_segment_list.csv"
cols = ["class_label", "record_id", "segment_id", "start_time_s", "duration_s",
        "afe_adc_signed_file", "raw_mem_file", "afe_model", "label_verified"]
rows = []
for line in open(LIST):
    f = line.strip()
    if not f:
        continue
    base = f[:-4]                       # 0000_NSR_16539_60s_9530000ms
    p = base.split("_")                 # [0000, NSR, 16539, 60s, 9530000ms]
    seg_id, cls, rec = p[0], p[1], p[2]
    start_ms = int(p[4].replace("ms", ""))
    rows.append(dict(
        class_label=cls, record_id=rec, segment_id=seg_id,
        start_time_s=round(start_ms / 1000.0, 3), duration_s=60,
        afe_adc_signed_file=f"datasets/afe_output_xmodelmatch/test/signed/{f}",
        raw_mem_file=f"datasets/strict60_large/raw/test/mem/{f}",
        afe_model="xmodelmatch_emulator (vs XMODEL/Questa simulation: sim_out/afe_val/xmodel/)",
        label_verified="true"))
with open(OUT, "w", newline="") as o:
    w = csv.DictWriter(o, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"{len(rows)} segments -> {OUT}")
for c in ["NSR", "CHF", "ARR", "AFF"]:
    print(f"  {c}: {sum(1 for r in rows if r['class_label']==c)}")
