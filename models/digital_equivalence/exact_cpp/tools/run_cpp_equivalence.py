#!/usr/bin/env python3
"""Run the hand-written C++ model over the hash-locked 36-case corpus."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,subprocess
from pathlib import Path

EXACT=Path(__file__).resolve().parents[1]
INTEGRATED_ROOT=EXACT.parents[2]
DIGITAL_ROOT=INTEGRATED_ROOT/"design/digital"
BENCH=INTEGRATED_ROOT/"models/digital_equivalence"
CASES=DIGITAL_ROOT/"reports/final/board_replay_36_cases.csv"
MANIFEST=BENCH/"results/benchmark_dataset_manifest.csv"

def rows(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def write(path:Path,data:list[dict[str,object]],fields:list[str])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(data)

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--exe",type=Path,required=True);p.add_argument("--data-root",type=Path,required=True);p.add_argument("--case-id",action="append",default=[]);a=p.parse_args()
    expected_hash={r["case_id"]:r["sha256"] for r in rows(MANIFEST)}; selected=set(a.case_id) if a.case_id else None
    final_rows=[]; snapshot_rows=[]; outdir=EXACT/"results/case_outputs";outdir.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    if os.environ.get("EXACT_CPP_TOOLCHAIN_BIN"):
        env["PATH"]=os.environ["EXACT_CPP_TOOLCHAIN_BIN"]+os.pathsep+env.get("PATH","")
    for case in rows(CASES):
        if selected and case["case_id"] not in selected:continue
        source=(a.data_root/case["mem_path"]).resolve(); digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=expected_hash[case["case_id"]]:raise RuntimeError(f"input hash mismatch: {case['case_id']}")
        result_path=outdir/f"{case['case_id']}.json"; trace_path=outdir/f"{case['case_id']}.csv"
        subprocess.run([str(a.exe.resolve()),"--input",str(source),"--format","signed12_hex","--expected-samples","1800000","--output",str(result_path),"--trace-output",str(trace_path)],check=True,env=env)
        actual=json.loads(result_path.read_text(encoding="utf-8")); exact=(actual["final_pred"]==int(case["expected_final_pred"]) and all(actual[f"final_mem_{c}"]==int(case[f"expected_final_mem_{c}"]) for c in ("NSR","CHF","ARR","AFF")) and actual["accepted_samples"]==1800000 and actual["snapshot_count"]==30 and actual["decision_count"]==1)
        final_rows.append({"case_id":case["case_id"],"expected_final_pred":case["expected_final_pred"],"actual_final_pred":actual["final_pred"],**{f"expected_final_mem_{c}":case[f"expected_final_mem_{c}"] for c in ("NSR","CHF","ARR","AFF")},**{f"actual_final_mem_{c}":actual[f"final_mem_{c}"] for c in ("NSR","CHF","ARR","AFF")},"accepted_samples":actual["accepted_samples"],"snapshots":actual["snapshot_count"],"decisions":actual["decision_count"],"exact_match":int(exact)})
        for snap in rows(trace_path): snapshot_rows.append({"case_id":case["case_id"],"class_label":case["class_label"],**snap})
        print(case["case_id"],"exact" if exact else "MISMATCH",flush=True)
    final_fields=["case_id","expected_final_pred","actual_final_pred","expected_final_mem_NSR","actual_final_mem_NSR","expected_final_mem_CHF","actual_final_mem_CHF","expected_final_mem_ARR","actual_final_mem_ARR","expected_final_mem_AFF","actual_final_mem_AFF","accepted_samples","snapshots","decisions","exact_match"]
    write(EXACT/"results/final_equivalence.csv",final_rows,final_fields)
    snap_fields=list(snapshot_rows[0]) if snapshot_rows else []
    write(EXACT/"results/cpp_snapshot_trace.csv",snapshot_rows,snap_fields)
    matched=sum(int(r["exact_match"]) for r in final_rows); print(f"final exact: {matched}/{len(final_rows)}")
    return 0 if matched==len(final_rows) else 1
if __name__=="__main__":raise SystemExit(main())
