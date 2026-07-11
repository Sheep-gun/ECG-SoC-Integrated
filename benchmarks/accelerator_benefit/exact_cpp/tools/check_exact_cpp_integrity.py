#!/usr/bin/env python3
"""Fail-closed integrity audit for the exact-C++ implementation/evidence package."""
from __future__ import annotations
import argparse,csv,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path

EXACT=Path(__file__).resolve().parents[1];REPO=EXACT.parents[2]
LOCKED="c6b80de19cdcad5b7e43fe7835588b629d847f75";MODEL="structural_guarded_silent_aff_1008710"
PARAM="7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b"
GIT=shutil.which("git") or r"C:\Users\YangGeon\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
LOCKED_PATHS=["rtl/core/class_score_neurons.v","rtl/strict_recordwise_locked_params.vh","rtl/final_membrane_layer.v","rtl/snn_ecg_30min_final_top.v","rtl/core/ecg_event_encoder_adaptive.v","rtl/core/qrs_lif_detector.v","rtl/core/pnn_rhythm_predictor.v","rtl/core/rdm_variability_neuron.v","rtl/core/dscr_spike_counter.v","rtl/core/ram_peak_accumulator.v","rtl/core/ectopic_pair_neuron.v","rtl/core/qrs_maf_neuron.v","rtl/core/rbbb_qrs_delay_bank.v","rtl/core/snn_ecg_3feat_top.v","configs/final_submission_locked_model.json","configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json"]
EXPECTED_HASHES={
 "benchmarks/accelerator_benefit/results/benchmark_dataset_manifest.csv":"4965b8a098617d6138e4e56e2b45febda20706b031e9bbaa2558d874517dee72",
 "reports/final/board_replay_36_cases.csv":"f01d4afb4a67ba06b768ac99891868f9cbc2061a3d28ddf67d800b5b56d9f324",
 "reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv":"3c2312416b39474053a0cd4bde5f7fe9c2c9f4d81777c169f8c78107c2e0b757",
}
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p:Path)->list[dict[str,str]]:
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def git_ok(*args:str)->bool:return subprocess.run([GIT,*args],cwd=REPO,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--data-root",type=Path,default=Path(r"C:\Users\YangGeon\SNN ECG Classifier"));a=ap.parse_args()
    failures=[];checks=[]
    def check(name:str,ok:bool,detail:str="")->None:
        checks.append({"check":name,"status":"pass" if ok else "fail","detail":detail})
        if not ok:failures.append(f"{name}: {detail}")

    check("locked_commit_to_head_diff",git_ok("diff","--quiet",LOCKED,"HEAD","--",*LOCKED_PATHS))
    check("locked_worktree_diff",git_ok("diff","--quiet","--",*LOCKED_PATHS))
    check("locked_index_diff",git_ok("diff","--cached","--quiet","--",*LOCKED_PATHS))
    for rel,want in EXPECTED_HASHES.items():check("artifact_sha256:"+rel,sha(REPO/rel)==want,sha(REPO/rel))
    config=json.loads((REPO/"configs/final_submission_locked_model.json").read_text(encoding="utf-8-sig"))
    check("model_id",config.get("final_model_id")==MODEL,str(config.get("final_model_id")))
    check("parameter_payload",config.get("locked_params_hash")==PARAM,str(config.get("locked_params_hash")))

    manifest=rows(REPO/"benchmarks/accelerator_benefit/results/benchmark_dataset_manifest.csv")
    cases={r["case_id"]:r for r in rows(REPO/"reports/final/board_replay_36_cases.csv")};input_bad=[]
    for row in manifest:
        case=cases.get(row["case_id"]);p=(a.data_root/case["mem_path"]).resolve() if case else Path()
        if not case or not p.is_file() or sha(p)!=row["sha256"]:input_bad.append(row["case_id"])
    check("locked_final_test_inputs",len(manifest)==36 and not input_bad,",".join(input_bad))

    header=EXACT/"include/locked_parameters.hpp";before=sha(header)
    gen=subprocess.run([sys.executable,str(EXACT/"tools/generate_locked_parameters.py")],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    after=sha(header);check("parameter_regeneration",gen.returncode==0 and before==after,gen.stdout.strip())
    htext=header.read_text(encoding="utf-8")
    check("header_identity",MODEL in htext and PARAM in htext and LOCKED in htext)

    model_src=(EXACT/"src/exact_model.cpp").read_text(encoding="utf-8")
    check("canonical_two_idle_transitions",model_src.count("frontend_.tick(false,false,false,false,0);")>=3 and "if (segment_samples_ == 60000)" in model_src)
    check("flush_semantics", "for (int i=0;i<36;++i)" in model_src and "c24_readout_busy_ticks = 35" in (EXACT/"src/snapshot_readout.cpp").read_text())
    cmake=(EXACT/"CMakeLists.txt").read_text();maincpp=(EXACT/"src/main.cpp").read_text()
    check("trace_mode_separation","EXACT_CPP_TRACE" in cmake and "#if EXACT_CPP_TRACE" in model_src and "#if !EXACT_CPP_TRACE" in maincpp)

    fw=(EXACT/"include/fixed_width.hpp").read_text();required=("wrap_add","wrap_sub","wrap_mul","arithmetic_right","logical_right","saturating_signed_add","saturating_signed_sub","wrapping_abs","concat","slice")
    check("fixed_width_helper_surface",all(x in fw for x in required))
    sources="\n".join(p.read_text(encoding="utf-8") for p in (EXACT/"src").glob("*.cpp"))
    risky=[pat for pat in (r"\b(?:score|local|c24)\s*\[[^]]+\]\s*[+*-]=",r"\b(?:int32_t|int64_t)\s+\w+\s*>>") if re.search(pat,sources)]
    check("no_known_signed_overflow_patterns",not risky,",".join(risky))
    classifier=(EXACT/"src").read_text if False else "\n".join(p.read_text(encoding="utf-8") for d in (EXACT/"src",EXACT/"include") for p in d.glob("*.*") if p.name!="locked_parameters.hpp")
    tuning=re.findall(r"(?i)(?:mitdb|chfdb|afdb|nsrdb|expected_final|final_test|30min_w\d+)",classifier)
    check("no_final_test_tuning_in_classifier",not tuning,",".join(sorted(set(tuning))))

    r=EXACT/"results";fixed=json.loads((r/"fixed_width_test_summary.json").read_text())
    check("fixed_width_tests",fixed.get("status")=="pass" and fixed.get("failures")==0,str(fixed))
    micro=rows(r/"module_microtrace_equivalence.csv");check("module_microtraces",len(micro)>=18 and all(x["exact_match"]=="1" for x in micro),str(len(micro)))
    sample=rows(r/"sample_state_hash_equivalence.csv");check("sample_state_hashes",len(sample)>=4 and sum(int(x["matched_samples"]) for x in sample)>=240000 and all(x["exact_match"]=="1" for x in sample),str(len(sample)))
    side=(r/"golden_snapshot_trace.sha256").read_text().split()[0];gold=sha(r/"golden_snapshot_trace.csv")
    check("golden_snapshot_hash",side==gold=="7fbdaf2a4a182a3c2757e7c7f923ff857b79d96756b509f75c588db515717a13",gold)
    snap=rows(r/"snapshot_equivalence.csv");check("snapshot_1080",len(snap)==1080 and all(x["snapshot_match"]=="1" for x in snap),str(len(snap)))
    final=rows(r/"final_equivalence.csv");counts=all(x["accepted_samples"]=="1800000" and x["snapshots"]=="30" and x["decisions"]=="1" for x in final)
    check("final_36",len(final)==36 and counts and all(x["exact_match"]=="1" for x in final),str(len(final)))
    mem=sum(sum(x[f"expected_final_mem_{c}"]==x[f"actual_final_mem_{c}"] for c in ("NSR","CHF","ARR","AFF")) for x in final)
    check("final_membrane_144",mem==144,str(mem))
    identity=rows(r/"build_identity.csv");check("debug_release_identity",len(identity)==36 and all(x["exact_match"]=="1" and x["debug_result_sha256"]==x["release_result_sha256"] for x in identity),str(len(identity)))
    summary=json.loads((r/"equivalence_summary.json").read_text());check("summary_status",summary.get("status")=="pass" and summary.get("performance_values_present") is False,str(summary.get("status")))

    required_docs=("README.md","reports/SOURCE_PROVENANCE.md","reports/EXACT_CPP_DESIGN.md","reports/RTL_SEMANTICS_INVENTORY.md","reports/CADENCE_COMPRESSION_JUSTIFICATION.md","reports/LOCKED_PARAMETER_EQUIVALENCE.md","reports/EXACT_CPP_EQUIVALENCE.md","READY_FOR_EXACT_CPP_BENCHMARK.md")
    check("required_documentation",all((EXACT/p).is_file() for p in required_docs))
    docs="\n".join((EXACT/p).read_text(encoding="utf-8") for p in required_docs if (EXACT/p).is_file())
    premature=re.findall(r"(?i)(?:54\.01\s*ms|33\.3\s*MSPS|cpu[_ -]?runtime\s*[:=]\s*\d|speedup\s*[:=]\s*\d)",docs)
    check("no_premature_benchmark_values",not premature,",".join(premature))
    ready=(EXACT/"READY_FOR_EXACT_CPP_BENCHMARK.md").read_text();check("benchmark_pending_status","EXACT_CPP_IMPLEMENTED_AND_VERIFIED" in ready and "PERFORMANCE_MEASUREMENT_PENDING" in ready)

    result={"status":"pass" if not failures else "fail","checks":checks,"failures":failures}
    (r/"integrity_check.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"status":result["status"],"checks":len(checks),"failures":failures},indent=2))
    return 0 if not failures else 1
if __name__=="__main__":raise SystemExit(main())
