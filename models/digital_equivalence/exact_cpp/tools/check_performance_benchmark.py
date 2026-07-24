#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math,shutil,statistics,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];R=HERE/"results";REPORTS=HERE/"reports"
BASE_COMMIT="fb4f77fc5faa34073697cc5cf6ad07c188e0aff1"
GIT=shutil.which("git")
def rows(p:Path):
 with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def text_sha(p:Path):return hashlib.sha256(p.read_bytes().replace(b"\r\n",b"\n")).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--reference-exact",type=Path);ap.add_argument("--authority",type=Path);a=ap.parse_args()
 failures=[];checks=[]
 def check(name,ok,detail=""):
  checks.append({"check":name,"status":"pass" if ok else "fail","detail":str(detail)})
  if not ok:failures.append(f"{name}: {detail}")
 required=[R/"exact_cpp_cpu_raw.csv",R/"exact_cpp_cpu_summary.csv",R/"cpu_fpga_comparison.csv",REPORTS/"EXACT_CPP_PERFORMANCE_BENCHMARK.md",REPORTS/"BENCHMARK_ENVIRONMENT.md"]
 check("required_outputs",all(p.is_file() for p in required))
 raw=rows(required[0]);check("raw_720",len(raw)==720,len(raw));check("case_coverage",len(set(r["case_id"] for r in raw))==36)
 check("mode_coverage",sum(r["mode"]=="kernel" for r in raw)==360 and sum(r["mode"]=="end_to_end" for r in raw)==360)
 check("protocol_flags",all(r["warmups"]=="3" and r["measured_repetitions"]=="10" and r["affinity_cpu"]=="2" and r["affinity_mask"]=="0x4" and r["trace_enabled"]=="0" and r["march_native_enabled"]=="1" for r in raw))
 check("all_outputs_exact",all(r["output_exact"]=="1" and r["accepted_samples"]=="1800000" and r["snapshots"]=="30" and r["decisions"]=="1" for r in raw))
 for cid in set(r["case_id"] for r in raw):
  for mode in ("kernel","end_to_end"):
   group=[r for r in raw if r["case_id"]==cid and r["mode"]==mode]
   if len(group)!=10 or sorted(int(r["repetition"]) for r in group)!=list(range(1,11)):failures.append(f"repetition coverage: {cid}/{mode}")
 check("repetition_coverage",not any(x.startswith("repetition coverage") for x in failures))
 summary=rows(required[1]);check("summary_rows",len(summary)==74,len(summary));agg={(r["mode"]):r for r in summary if r["scope"]=="all_cases"}
 for mode in ("kernel","end_to_end"):
  med=statistics.median(float(r["latency_ms"]) for r in raw if r["mode"]==mode)
  check(f"{mode}_median",math.isclose(med,float(agg[mode]["latency_median_ms"]),abs_tol=5e-10),med)
 cmp=rows(required[2]);check("comparison_single_row",len(cmp)==1);c=cmp[0];ratio=float(agg["kernel"]["latency_median_ms"])/54.0126
 check("comparison_formula",math.isclose(ratio,float(c["ratio_cpu_over_fpga"]),abs_tol=5e-10),ratio)
 check("fpga_scope",c["fpga_cycles"]=="5401260" and c["fpga_clock_hz"]=="100000000" and c["fpga_latency_ms"]=="54.012600000" and all(c[x]=="PENDING_BOARD" for x in ("board_latency_status","board_power_status","board_energy_status")))
 post=json.loads((R/"post_benchmark_equivalence.json").read_text());check("post_benchmark_equivalence",post["status"]=="pass" and post["snapshot_boundaries"]=="1080/1080" and post["accepted_sample_state_hashes"]=="240000/240000")
 sh=rows(R/"sample_state_hash_equivalence.csv");check("post_sample_hashes",len(sh)==4 and all(r["exact_match"]=="1" and r["matched_samples"]=="60000" for r in sh))
 if a.reference_exact:
  for sub in ("include","src"):
   for p in (a.reference_exact/sub).glob("*"):
    if p.is_file():check(f"classifier_source:{sub}/{p.name}",text_sha(p)==text_sha(HERE/sub/p.name))
 else:
  repo=HERE.parents[2];rel=HERE.relative_to(repo)
  if not GIT:raise RuntimeError("git is required; add it to PATH")
  clean=subprocess.run([GIT,"diff","--quiet",BASE_COMMIT,"HEAD","--",str(rel/"include"),str(rel/"src")],cwd=repo).returncode==0
  working=subprocess.run([GIT,"diff","--quiet","--",str(rel/"include"),str(rel/"src")],cwd=repo).returncode==0
  check("classifier_source_commit_identity",clean and working)
 if a.authority:
  check("fpga_cycle_csv_sha",sha(a.authority/"rtl_cycle_benchmark.csv")=="ace07930c5959dc169a6798868e231f61b005aa5ecae6fb544d155943f260b1f")
  rtl=json.loads((a.authority/"rtl_cycle_summary.json").read_text(encoding="utf-8"))
  check("fpga_cycle_summary_fields",rtl.get("status")=="CYCLE_DERIVED" and rtl.get("case_count")==36 and rtl.get("sample_gap_cycles")==2 and rtl.get("clock_frequency_hz")==100000000 and math.isclose(float(rtl.get("total_latency_ms",{}).get("median",0)),54.0126,abs_tol=1e-12))
 perf=(REPORTS/"EXACT_CPP_PERFORMANCE_BENCHMARK.md").read_text();env=(REPORTS/"BENCHMARK_ENVIRONMENT.md").read_text()
 check("report_scoping","cycle-derived FPGA accelerator-core latency" in perf and "PENDING_BOARD" in perf and "not a measured FPGA or board speedup" in perf)
 check("environment_limitations","Temperature" in env and "denied" in env and "-march=native" in env)
 check("raw_sha",sha(R/"exact_cpp_cpu_raw.csv")=="7dc3b65fe0316d08f6a6e3b740427d91340effe6f5abb598885e5f98a782bee9")
 result={"status":"pass" if not failures else "fail","checks":checks,"failures":failures,"raw_sha256":sha(R/"exact_cpp_cpu_raw.csv"),"summary_sha256":sha(R/"exact_cpp_cpu_summary.csv"),"comparison_sha256":sha(R/"cpu_fpga_comparison.csv")}
 (R/"performance_integrity.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n");print(json.dumps({"status":result["status"],"checks":len(checks),"failures":failures},indent=2));return 0 if not failures else 1
if __name__=="__main__":raise SystemExit(main())
