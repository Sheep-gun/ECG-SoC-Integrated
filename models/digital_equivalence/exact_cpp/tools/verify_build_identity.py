#!/usr/bin/env python3
"""Verify current debug/trace and release/no-trace outputs on all locked cases."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,subprocess
from pathlib import Path
EXACT=Path(__file__).resolve().parents[1];INTEGRATED_ROOT=EXACT.parents[2]
DIGITAL_ROOT=INTEGRATED_ROOT/"design/digital";BENCH=INTEGRATED_ROOT/"models/digital_equivalence"
CASES=DIGITAL_ROOT/"reports/final/board_replay_36_cases.csv";MANIFEST=BENCH/"results/benchmark_dataset_manifest.csv"
FIELDS=("final_pred","final_mem_NSR","final_mem_CHF","final_mem_ARR","final_mem_AFF","accepted_samples","snapshot_count","decision_count","model_id","parameter_hash")
def rows(p:Path)->list[dict[str,str]]:
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--debug-exe",type=Path,required=True);ap.add_argument("--release-exe",type=Path,required=True);ap.add_argument("--data-root",type=Path,required=True);a=ap.parse_args()
    hashes={r["case_id"]:r["sha256"] for r in rows(MANIFEST)};work=EXACT/"build-identity-evidence";work.mkdir(exist_ok=True)
    env=os.environ.copy()
    if os.environ.get("EXACT_CPP_TOOLCHAIN_BIN"):
        env["PATH"]=os.environ["EXACT_CPP_TOOLCHAIN_BIN"]+os.pathsep+env.get("PATH","")
    out=[]
    for case in rows(CASES):
        cid=case["case_id"];source=(a.data_root/case["mem_path"]).resolve()
        if hashlib.sha256(source.read_bytes()).hexdigest()!=hashes[cid]:raise RuntimeError(f"input hash mismatch: {cid}")
        values=[]
        for name,exe in (("debug",a.debug_exe),("release",a.release_exe)):
            dst=work/f"{cid}.{name}.json"
            subprocess.run([os.fspath(exe.resolve()),"--input",os.fspath(source),"--format","signed12_hex","--expected-samples","1800000","--output",os.fspath(dst)],check=True,env=env)
            values.append(json.loads(dst.read_text(encoding="utf-8")))
        bad=next((f for f in FIELDS if values[0][f]!=values[1][f]),"")
        out.append({"case_id":cid,"debug_result_sha256":hashlib.sha256(json.dumps({f:values[0][f] for f in FIELDS},sort_keys=True).encode()).hexdigest(),
                    "release_result_sha256":hashlib.sha256(json.dumps({f:values[1][f] for f in FIELDS},sort_keys=True).encode()).hexdigest(),
                    "first_mismatch_field":bad,"exact_match":int(not bad)})
        print(cid,"exact" if not bad else f"MISMATCH:{bad}",flush=True)
    path=EXACT/"results/build_identity.csv"
    with path.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator="\n");w.writeheader();w.writerows(out)
    return 0 if all(r["exact_match"] for r in out) else 1
if __name__=="__main__":raise SystemExit(main())
