#!/usr/bin/env python3
"""Compare accepted-sample feature-architecture hashes against locked XSim."""
from __future__ import annotations
import argparse,csv,hashlib,os,re,subprocess
from pathlib import Path

EXACT=Path(__file__).resolve().parents[1];REPO=EXACT.parents[2]
CASES=REPO/"reports/final/board_replay_36_cases.csv"
MANIFEST=REPO/"benchmarks/accelerator_benefit/results/benchmark_dataset_manifest.csv"
SELECTED=("NSR_nsrdb_16272_chunk03","CHF_chfdb_chf07_chunk09",
          "ARR_mitdb_118_chunk00","AFF_afdb_06995_chunk12")
RX=re.compile(r"STATE_HASH sample=(\d+) hash=([0-9a-fA-F]{16})")
def rows(p:Path)->list[dict[str,str]]:
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def digest_stream(data:dict[int,str])->str:
    h=hashlib.sha256()
    for i in sorted(data):h.update(f"{i},{data[i].lower()}\n".encode())
    return h.hexdigest()
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--exe",type=Path,required=True);ap.add_argument("--data-root",type=Path,required=True);a=ap.parse_args()
    case_map={r["case_id"]:r for r in rows(CASES)}; expected={r["case_id"]:r["sha256"] for r in rows(MANIFEST)}
    work=EXACT/"build-sample-hash-evidence";work.mkdir(exist_ok=True)
    env=os.environ.copy();env["PATH"]=r"C:\Xilinx\Vitis_HLS\2020.2\tps\win64\msys64\mingw64\bin"+os.pathsep+env.get("PATH","")
    out=[]
    for case_id in SELECTED:
        case=case_map[case_id];source=(a.data_root/case["mem_path"]).resolve()
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected[case_id]:raise RuntimeError(f"input hash mismatch: {case_id}")
        xlog=work/f"{case_id}.xsim.log";ccsv=work/f"{case_id}.cpp.csv";jsonout=work/f"{case_id}.json"
        subprocess.run([os.fspath(Path(os.sys.executable)),os.fspath(EXACT/"tools/run_xsim_sample_hash.py"),"--input",os.fspath(source),"--log",os.fspath(xlog)],check=True)
        subprocess.run([os.fspath(a.exe.resolve()),"--input",os.fspath(source),"--format","signed12_hex","--expected-samples","60000","--stop-after-expected","true","--allow-incomplete","true","--sample-hash-output",os.fspath(ccsv),"--output",os.fspath(jsonout)],check=True,env=env)
        x={int(i):h.lower() for i,h in RX.findall(xlog.read_text(encoding="utf-8",errors="replace"))}
        c={int(r["accepted_sample"]):r["state_hash"].lower() for r in rows(ccsv)}
        keys=sorted(set(x)|set(c));bad=[i for i in keys if x.get(i)!=c.get(i)]
        out.append({"case_id":case_id,"class_label":case["class_label"],"accepted_samples_compared":len(keys),
                    "expected_rtl_hash_stream_sha256":digest_stream(x),"actual_cpp_hash_stream_sha256":digest_stream(c),
                    "matched_samples":len(keys)-len(bad),"first_mismatch_sample":bad[0] if bad else "","exact_match":int(not bad and len(keys)==60000)})
        print(case_id,f"{len(keys)-len(bad)}/{len(keys)}",flush=True)
    path=EXACT/"results/sample_state_hash_equivalence.csv";path.parent.mkdir(exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator="\n");w.writeheader();w.writerows(out)
    return 0 if all(r["exact_match"] for r in out) else 1
if __name__=="__main__":raise SystemExit(main())
