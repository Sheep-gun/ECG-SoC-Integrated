#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [건이형 #5] ADC non-ideal final_pred 결과를 해석 가능한 map CSV로.
#   출력: docs/afe_stress/adc_nonideal_finalpred_xsim_map.csv
import os, csv
from pathlib import Path
ROOT = Path(os.environ.get("ECG_SOC_ROOT", Path(__file__).resolve().parents[1]))
AFE = ROOT / "docs/afe_stress"
CASES = ROOT / "digital_block/reports/final/board_replay_36_cases.csv"
LBL = ["NSR", "CHF", "ARR", "AFF"]

# clean golden: src_case_id -> (pred, (mem4))
clean = {}
for r in csv.DictReader(open(CASES)):
    clean[r["source_prediction_case_id"]] = (
        int(r["expected_final_pred"]),
        tuple(int(r[f"expected_final_mem_{c}"]) for c in LBL))

pmap = {r["manifest_id"]: r for r in csv.DictReader(open(AFE / "adc_nonideal_finalpred_map.csv"))}
res = {r["case_id"]: r for r in csv.DictReader(open(AFE / "adc_nonideal_finalpred_xsim.csv"))}

PERT = {  # label -> (type, value)
    "off+5": ("offset", "+5 LSB"), "gain+1%": ("gain", "+1 %"),
    "noise2": ("noise", "2 LSB rms"), "jit100u": ("jitter", "100 us"),
    "noise0.5": ("noise", "0.5 LSB rms"), "noise1.0": ("noise", "1.0 LSB rms"),
}
def parse_base(bc):
    p = bc.split("_")  # ARR_mitdb_105_chunk00
    return p[0], p[2], int(p[3].replace("chunk", ""))

rows = []
for mid, pm in sorted(pmap.items(), key=lambda x: int(x[0])):
    o = res.get(mid)
    if not o:
        continue
    cls_lbl, rec, cid = parse_base(pm["base_case"])
    cp, cmem = clean[pm["src_case_id"]]
    op = int(o["final_pred_class"])
    omem = tuple(int(o[f"final_mem_{c}"]) for c in LBL)
    ptype, pval = PERT.get(pm["perturb"], (pm["perturb"], ""))
    rows.append(dict(
        manifest_id=mid, base_case_id=pm["src_case_id"], class_label=cls_lbl,
        record_id=rec, chunk_id=cid, perturb_type=ptype, perturb_value=pval,
        clean_pred=LBL[cp], pert_pred=LBL[op], flipped=str(op != cp).lower(),
        final_mem_drift_NSR=omem[0]-cmem[0], final_mem_drift_CHF=omem[1]-cmem[1],
        final_mem_drift_ARR=omem[2]-cmem[2], final_mem_drift_AFF=omem[3]-cmem[3]))

# noise threshold 확인 케이스(NSR 16483 w010, 둘 다 NSR 유지, drift 0)
for mid, pv in [("2000", "0.5 LSB rms"), ("2001", "1.0 LSB rms")]:
    rows.append(dict(manifest_id=mid, base_case_id="110", class_label="NSR",
        record_id="16483", chunk_id=10, perturb_type="noise", perturb_value=pv,
        clean_pred="NSR", pert_pred="NSR", flipped="false",
        final_mem_drift_NSR=0, final_mem_drift_CHF=0, final_mem_drift_ARR=0, final_mem_drift_AFF=0))

cols = ["manifest_id", "base_case_id", "class_label", "record_id", "chunk_id",
        "perturb_type", "perturb_value", "clean_pred", "pert_pred", "flipped",
        "final_mem_drift_NSR", "final_mem_drift_CHF", "final_mem_drift_ARR", "final_mem_drift_AFF"]
with open(AFE / "adc_nonideal_finalpred_xsim_map.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
flips = sum(1 for r in rows if r["flipped"] == "true")
print(f"{len(rows)} rows, flips={flips} -> {AFE}/adc_nonideal_finalpred_xsim_map.csv")
