#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [2.1 final_pred] ADC 섭동 chunk XSim 결과 vs 깨끗한 golden(clean) 대조 → 분류 flip 여부.
#  사용: python3 compare_pert.py <pert_result.csv>
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import sys, csv
ECG = _ROOT + ""
CASES = ECG + "/digital_block/reports/final/board_replay_36_cases.csv"
PMAP = ECG + "/sim_out/chunks_pert/pert_map.csv"
LBL = ["NSR", "CHF", "ARR", "AFF"]
# clean golden: src_case_id -> (pred, mem)  (board_replay expected)
clean = {}
for r in csv.DictReader(open(CASES)):
    clean[r["source_prediction_case_id"]] = (
        int(r["expected_final_pred"]),
        tuple(int(r[f"expected_final_mem_{c}"]) for c in LBL),
        r["case_id"])
pmap = {r["manifest_id"]: r for r in csv.DictReader(open(PMAP))}
res = {r["case_id"]: r for r in csv.DictReader(open(sys.argv[1]))}
print(f"{'chunk':28} {'perturb':9} {'clean_pred':>10} {'pert_pred':>9} {'flip?':>6} {'mem drift(N/C/A/F)'}")
kept = 0; tot = 0
for mid, pm in sorted(pmap.items(), key=lambda x: int(x[0])):
    o = res.get(mid)
    if not o:
        print(f"{pm['base_case']:28} {pm['perturb']:9}  (no result)"); continue
    tot += 1
    cp, cmem, cname = clean[pm["src_case_id"]]
    op = int(o["final_pred_class"])
    omem = tuple(int(o[f"final_mem_{c}"]) for c in LBL)
    flip = "FLIP" if op != cp else "-"
    kept += (op == cp)
    drift = tuple(omem[i] - cmem[i] for i in range(4))
    print(f"{pm['base_case']:28} {pm['perturb']:9} {LBL[cp]:>10} {LBL[op]:>9} {flip:>6}  {drift}")
print(f"\nfinal_pred 유지: {kept}/{tot}  (flip {tot-kept}건)")
