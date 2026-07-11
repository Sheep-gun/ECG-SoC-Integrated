#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [건이형 #2] canonical cadence 36-case compare artifact.
#   입력: gap=2 XSim 결과 CSV (result_g2.csv, arg)
#   조인: board_replay_36_cases.csv(expected) + afe36_sha256_bitidentity.csv(input_sha256_match)
#   출력: docs/integration_latest/afe_locked_rtl_integration_36case_compare.{csv,md}
# 사용: python3 gen_36case_compare.py <result_g2.csv> [sample_gap_cycles=2]
import os, sys, csv
from pathlib import Path
ROOT = Path(os.environ.get("ECG_SOC_ROOT", Path(__file__).resolve().parents[1]))
CASES = ROOT / "digital_block/reports/final/board_replay_36_cases.csv"
SHA = ROOT / "docs/integration_latest/afe36_sha256_bitidentity.csv"
OUTD = ROOT / "docs/integration_latest"
LBL = ["NSR", "CHF", "ARR", "AFF"]
GAP = int(sys.argv[2]) if len(sys.argv) > 2 else 2

# board_replay: source_prediction_case_id -> expected 정보
exp = {}
for r in csv.DictReader(open(CASES)):
    exp[r["source_prediction_case_id"]] = dict(
        name=r["case_id"], rec=r["source_record_id"], chunk=int(r["chunk_id"]),
        pred=int(r["expected_final_pred"]),
        mem=[int(r[f"expected_final_mem_{c}"]) for c in LBL])
# sha256: case_id(name) -> match(bool str)
sham = {r["case_id"]: (r["match"] == "true") for r in csv.DictReader(open(SHA))}
# gap=2 결과: case_id(=source_prediction_case_id) -> row
res = {r["case_id"]: r for r in csv.DictReader(open(sys.argv[1]))}

cols = ["case_id", "source_record_id", "chunk_id", "expected_pred", "reproduced_pred", "pred_match",
        "expected_mem_NSR", "expected_mem_CHF", "expected_mem_ARR", "expected_mem_AFF",
        "reproduced_mem_NSR", "reproduced_mem_CHF", "reproduced_mem_ARR", "reproduced_mem_AFF",
        "mem_match", "sample_gap_cycles", "samples_driven", "accepted_samples",
        "windows", "decisions", "input_sha256_match"]
rows = []
for scid, e in sorted(exp.items(), key=lambda x: int(x[0])):
    o = res.get(scid)
    if not o:
        print(f"WARN: no result for case {scid} ({e['name']})"); continue
    rpred = int(o["final_pred_class"])
    rmem = [int(o[f"final_mem_{c}"]) for c in LBL]
    pmatch = (rpred == e["pred"])
    mmatch = (rmem == e["mem"])
    rows.append(dict(
        case_id=e["name"], source_record_id=e["rec"], chunk_id=e["chunk"],
        expected_pred=LBL[e["pred"]], reproduced_pred=LBL[rpred], pred_match=str(pmatch).lower(),
        expected_mem_NSR=e["mem"][0], expected_mem_CHF=e["mem"][1], expected_mem_ARR=e["mem"][2], expected_mem_AFF=e["mem"][3],
        reproduced_mem_NSR=rmem[0], reproduced_mem_CHF=rmem[1], reproduced_mem_ARR=rmem[2], reproduced_mem_AFF=rmem[3],
        mem_match=str(mmatch).lower(), sample_gap_cycles=GAP,
        samples_driven=int(o["samples_driven"]), accepted_samples=int(o["prof_accepted_samples"]),
        windows=int(o["prof_windows"]), decisions=int(o["prof_decisions"]),
        input_sha256_match=str(sham.get(e["name"], False)).lower()))

with open(OUTD / "afe_locked_rtl_integration_36case_compare.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

np = sum(r["pred_match"] == "true" for r in rows)
nm = sum(r["mem_match"] == "true" for r in rows)
ns = sum(r["input_sha256_match"] == "true" for r in rows)
allok = all(r["pred_match"] == "true" and r["mem_match"] == "true" and r["input_sha256_match"] == "true"
            and r["sample_gap_cycles"] == GAP and r["samples_driven"] == 1800000
            and r["accepted_samples"] == 1800000 and r["windows"] == 30 and r["decisions"] == 1 for r in rows)
with open(OUTD / "afe_locked_rtl_integration_36case_compare.md", "w", encoding="utf-8") as f:
    f.write("# AFE → locked RTL integration — canonical 36-case compare\n\n")
    f.write(f"> Canonical board-facing XSim input cadence(`sample_gap_cycles={GAP}`), locked model/RTL 변경 없음.\n")
    f.write(f"> AFE-generated 36 final-test chunks vs digital locked golden.\n\n")
    f.write(f"- **final_pred match: {np}/36**\n- **final_membrane bit-exact match: {nm}/36**\n")
    f.write(f"- **input SHA256 match: {ns}/36**\n- 전 row 조건(gap={GAP}, samples/accepted=1,800,000, windows=30, decisions=1) 충족: **{str(allok).lower()}**\n\n")
    f.write("| case | record | chunk | exp_pred | rep_pred | pred✓ | exp_mem(N/C/A/F) | rep_mem(N/C/A/F) | mem✓ | sha256✓ |\n")
    f.write("|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        f.write(f"| {r['case_id']} | {r['source_record_id']} | {r['chunk_id']} | {r['expected_pred']} | {r['reproduced_pred']} | {r['pred_match']} | "
                f"{r['expected_mem_NSR']}/{r['expected_mem_CHF']}/{r['expected_mem_ARR']}/{r['expected_mem_AFF']} | "
                f"{r['reproduced_mem_NSR']}/{r['reproduced_mem_CHF']}/{r['reproduced_mem_ARR']}/{r['reproduced_mem_AFF']} | {r['mem_match']} | {r['input_sha256_match']} |\n")
    f.write(f"\n**결과: final_pred {np}/36 · final_membrane {nm}/36 bit-exact · SHA256 {ns}/36.**\n")
print(f"pred {np}/36, mem {nm}/36, sha256 {ns}/36, all_conditions={allok} -> afe_locked_rtl_integration_36case_compare.csv/.md")
