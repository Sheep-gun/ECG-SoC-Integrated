#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [건이형 #2] noise threshold (0.5/1.0/2.0 LSB) 전용 result artifact.
#   map CSV(NSR noise rows) + clean golden으로 절대 final_mem 산출.
#   출력: docs/afe_stress/adc_nonideal_noise_threshold_xsim.{csv,md}
import os, csv
from pathlib import Path
ROOT = Path(os.environ.get("ECG_SOC_ROOT", Path(__file__).resolve().parents[1]))
AFE = ROOT / "docs/afe_stress"
CASES = ROOT / "digital_block/reports/final/board_replay_36_cases.csv"
LBL = ["NSR", "CHF", "ARR", "AFF"]

# clean golden: src_case_id -> (pred, mem4)
clean = {}
for r in csv.DictReader(open(CASES)):
    clean[r["source_prediction_case_id"]] = (int(r["expected_final_pred"]),
                                             [int(r[f"expected_final_mem_{c}"]) for c in LBL])
mp = list(csv.DictReader(open(AFE / "adc_nonideal_finalpred_xsim_map.csv")))
# NSR noise rows만 (threshold sweep)
sel = [r for r in mp if r["class_label"] == "NSR" and r["perturb_type"] == "noise"]
def nval(v):  # "0.5 LSB rms" -> 0.5
    return float(v.split()[0])
sel.sort(key=lambda r: nval(r["perturb_value"]))

cols = ["manifest_id", "base_case_id", "class_label", "record_id", "noise_rms_lsb",
        "clean_pred", "pert_pred", "flipped",
        "final_mem_NSR", "final_mem_CHF", "final_mem_ARR", "final_mem_AFF"]
rows = []
for r in sel:
    cp, cmem = clean[r["base_case_id"]]
    fm = [cmem[i] + int(r[f"final_mem_drift_{c}"]) for i, c in enumerate(LBL)]
    rows.append(dict(manifest_id=r["manifest_id"], base_case_id=r["base_case_id"],
                     class_label=r["class_label"], record_id=r["record_id"],
                     noise_rms_lsb=nval(r["perturb_value"]),
                     clean_pred=r["clean_pred"], pert_pred=r["pert_pred"], flipped=r["flipped"],
                     final_mem_NSR=fm[0], final_mem_CHF=fm[1], final_mem_ARR=fm[2], final_mem_AFF=fm[3]))
with open(AFE / "adc_nonideal_noise_threshold_xsim.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
with open(AFE / "adc_nonideal_noise_threshold_xsim.md", "w", encoding="utf-8") as f:
    f.write("# ADC white-noise threshold — locked RTL final_pred (NSR chunk)\n\n")
    f.write("> 대상: NSR record 16483 w010 (clean golden = NSR 30/0/0/0). canonical 30분 chunk에 백색잡음 주입.\n")
    f.write("> claim: `noise ≤1 LSB rms에서 final_pred 안정`의 XSim result 근거. (worst-condition 16-case = `adc_nonideal_finalpred_xsim.csv`)\n\n")
    f.write("| noise_rms_lsb | clean_pred | pert_pred | flipped | final_mem (N/C/A/F) |\n")
    f.write("|---|---|---|---|---|\n")
    for r in rows:
        f.write(f"| {r['noise_rms_lsb']} | {r['clean_pred']} | {r['pert_pred']} | {r['flipped']} | "
                f"{r['final_mem_NSR']}/{r['final_mem_CHF']}/{r['final_mem_ARR']}/{r['final_mem_AFF']} |\n")
    f.write("\n**noise 0.5·1.0 LSB → NSR 유지(30/0/0/0), 2.0 LSB에서만 CHF flip.** → classification stability는 noise ≤1 LSB에서 안정, 2 LSB는 extreme stress 민감성.\n")
print(f"{len(rows)} rows -> adc_nonideal_noise_threshold_xsim.csv/.md")
for r in rows:
    print(f"  noise {r['noise_rms_lsb']} LSB -> {r['pert_pred']} ({r['final_mem_NSR']}/{r['final_mem_CHF']}/{r['final_mem_ARR']}/{r['final_mem_AFF']})")
