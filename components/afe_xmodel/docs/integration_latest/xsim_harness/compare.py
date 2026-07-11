#!/usr/bin/env python3
# 우리 AFE(w000) → 최신 locked model XSim 결과 vs 팀원 골든(fulltop XSim = board replay 정본) 대조
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
# 골든: digital_block/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv
GOLDEN = {
    "37": dict(rec="ARR/105", pred=2, mem=(8, 1, 21, 0)),
    "45": dict(rec="ARR/118", pred=2, mem=(7, 1, 21, 1)),
    "56": dict(rec="ARR/214", pred=2, mem=(0, 0, 30, 0)),
}
LBL = ["NSR", "CHF", "ARR", "AFF"]
rows = list(csv.DictReader(open(os.path.join(HERE, "result.csv"))))
print(f"{'case':>4} {'record':>8} | {'our_pred':>8} {'gold_pred':>9} | {'our_mem(N/C/A/F)':>18} {'gold_mem':>12} | pred_match mem_match")
allp = allm = True
for r in rows:
    cid = r["case_id"]; g = GOLDEN.get(cid)
    if not g: continue
    ourpred = int(r["final_pred_class"])
    ourmem = (int(r["final_mem_NSR"]), int(r["final_mem_CHF"]), int(r["final_mem_ARR"]), int(r["final_mem_AFF"]))
    pm = ourpred == g["pred"]; mm = ourmem == g["mem"]
    allp &= pm; allm &= mm
    print(f"{cid:>4} {g['rec']:>8} | {LBL[ourpred]:>8} {LBL[g['pred']]:>9} | {str(ourmem):>18} {str(g['mem']):>12} | {'OK' if pm else 'X':>10} {'OK' if mm else 'X'}")
print(f"\nfinal_pred 일치: {'ALL' if allp else 'MISMATCH'}   final_mem 일치: {'ALL(bit-exact)' if allm else 'MISMATCH'}")
