#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 36-case XSim 결과(우리 AFE chunk) vs 팀원 golden(fulltop XSim) 대조.
#  사용: python3 compare36.py <our_result.csv>
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import sys, csv, os
ECG = _ROOT + ""
GOLD = ECG + "/digital_block/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv"
LBL = ["NSR", "CHF", "ARR", "AFF"]
our = {r["case_id"]: r for r in csv.DictReader(open(sys.argv[1]))}
gold = {r["case_id"]: r for r in csv.DictReader(open(GOLD))}
pm = mm = 0; tot = 0; bad = []
for cid, g in sorted(gold.items(), key=lambda x: int(x[0])):
    o = our.get(cid)
    if not o:
        bad.append(f"{cid}(missing)"); continue
    tot += 1
    gp, op = int(g["final_pred_class"]), int(o["final_pred_class"])
    gmem = tuple(int(g[f"final_mem_{c}"]) for c in LBL)
    omem = tuple(int(o[f"final_mem_{c}"]) for c in LBL)
    p_ok = gp == op; m_ok = gmem == omem
    pm += p_ok; mm += m_ok
    if not (p_ok and m_ok):
        bad.append(f"{cid}:pred {op}vs{gp} mem {omem}vs{gmem}")
print(f"cases={tot}  final_pred match={pm}/{tot}  final_mem(bit-exact) match={mm}/{tot}")
if bad:
    print("MISMATCH:", "; ".join(bad))
else:
    print("ALL 36 bit-exact (final_pred + final_membrane).")
