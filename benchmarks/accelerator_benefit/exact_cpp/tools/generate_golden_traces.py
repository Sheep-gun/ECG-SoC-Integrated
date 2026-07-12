#!/usr/bin/env python3
"""Generate 36x30 normalized Snapshot goldens from the locked full-top XSim."""
from __future__ import annotations
import argparse,csv,hashlib,re,shutil,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXACT=Path(__file__).resolve().parents[1]; REPO=EXACT.parents[2]; VIVADO=Path(r"C:\Xilinx\Vivado\2020.2\bin")
CASES=REPO/"reports/final/board_replay_36_cases.csv"; MANIFEST=REPO/"benchmarks/accelerator_benefit/results/benchmark_dataset_manifest.csv"
CORE=["ecg_event_encoder.v","ecg_event_encoder_adaptive.v","snn_ecg_input_normalizer.v","qrs_lif_detector.v","pnn_rhythm_predictor.v","dscr_spike_counter.v","ram_peak_accumulator.v","rdm_variability_neuron.v","ectopic_pair_neuron.v","qrs_maf_neuron.v","rbbb_qrs_delay_bank.v","abandoned_feature_stubs.v","class_score_neurons.v","snn_ecg_3feat_top.v"]

def slash(p:Path)->str:return str(p).replace("\\","/")
def read_csv(p:Path)->list[dict[str,str]]:
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def run(cmd:list[str],cwd:Path,log:Path)->None:
    with log.open("w",encoding="utf-8",errors="replace") as out:r=subprocess.run(cmd,cwd=cwd,stdout=out,stderr=subprocess.STDOUT,text=True)
    if r.returncode:raise RuntimeError(f"failed ({r.returncode}): {' '.join(cmd)}; see {log}")

def build(worker:int)->Path:
    work=(EXACT/"build-xsim-golden"/f"worker_{worker}").resolve()
    if work.exists():
        if EXACT not in work.parents:raise RuntimeError("unsafe build path")
        shutil.rmtree(work)
    work.mkdir(parents=True)
    sources=[REPO/"rtl/core"/n for n in CORE]+[REPO/"rtl/final_membrane_layer.v",REPO/"rtl/snn_ecg_30min_final_top.v",EXACT/"tools/tb_exact_cpp_snapshot_trace.v"]
    prj=work/"sources.prj";prj.write_text("\n".join(f'verilog work "{slash(s)}"' for s in sources)+"\n",encoding="utf-8",newline="\n")
    (work/"run.tcl").write_text("run all\nquit\n",encoding="utf-8",newline="\n")
    run([str(VIVADO/"xvlog.bat"),"--nolog","-i",slash(REPO/"rtl"),"-prj",slash(prj)],work,work/"xvlog.log")
    run([str(VIVADO/"xelab.bat"),"--nolog","-debug","typical","tb_exact_cpp_snapshot_trace","-s","tb_exact_cpp_snapshot_trace"],work,work/"xelab.log")
    return work

def parse_log(case:dict[str,str],log:Path)->list[dict[str,object]]:
    snapshots={}; finals=[]
    for line in log.read_text(encoding="utf-8",errors="replace").splitlines():
        if "EXACT_SNAPSHOT" in line:
            d={k:v for k,v in re.findall(r"(\w+)=([^ ]+)",line)}; d["c24"]=[int(v) for v in d.pop("c24").split(",")]
            snapshots[int(d["idx"])]=d
        elif "EXACT_FINAL_STATE" in line:
            d={k:v for k,v in re.findall(r"(\w+)=([^ ]+)",line)}; d["mem"]=[int(v) for v in d.pop("mem").split(",")]; finals.append(d)
    if len(snapshots)!=30 or len(finals)!=30:raise RuntimeError(f"{case['case_id']}: snapshots={len(snapshots)} final_states={len(finals)}")
    rows=[]
    for idx in range(30):
        # snapshot_index advances before the non-final readout pipeline reaches
        # WTA, so Final Membrane states are paired by emission order, not the
        # displayed top-level index (the final two both display index 29).
        s=snapshots[idx]; f=finals[idx]; abnormal=int(s["pnn_mis"])+int(s["ect"])+int(s["qrs"])+int(s["qrs_w"])+int(s["qrs_c"])+int(s["qrs_e"])+int(s["rbbb"]); rhythm=int(s["pnn_mis"])+int(s["rdm_code"])+int(s["ect"]); morph=int(s["dscr_flip"])+int(s["qrs"])+int(s["qrs_w"])+int(s["qrs_c"])+int(s["qrs_e"])+int(s["rbbb"])
        row={"case_id":case["case_id"],"class_label":case["class_label"],"snapshot_index":idx,"accepted_samples":int(s["accepted"]),"snapshot_pred":int(s["pred"]),
             **{f"class_mem_{c}":s["c24"][i] for i,c in enumerate(("NSR","CHF","ARR","AFF"))},"beat_count":int(s["beat"]),"pnn_match_count":int(s["pnn_match"]),"pnn_mismatch_count":int(s["pnn_mis"]),"dscr_flip_count":int(s["dscr_flip"]),"dscr_slope_count":int(s["dscr_slope"]),"ram_code_sum":int(s["ram_sum"]),"ram_code_count":int(s["ram_count"]),"rdm_valid_count":int(s["rdm_valid"]),"rdm_code_sum":int(s["rdm_code"]),"ectopic_pair_count":int(s["ect"]),"qrs_maf_count":int(s["qrs"]),"qrs_width_abn_count":int(s["qrs_w"]),"qrs_complex_abn_count":int(s["qrs_c"]),"qrs_energy_abn_count":int(s["qrs_e"]),"rbbb_delay_like_count":int(s["rbbb"]),"rbbb_delay_applied_count":int(s["rbbb_applied"]),"pre_qrs_bump_count":int(s["pre"]),"abnormal_evidence_count":abnormal,"rhythm_irregular_evidence_count":rhythm,"morphology_evidence_count":morph,**{f"final_mem_{c}":f["mem"][i] for i,c in enumerate(("NSR","CHF","ARR","AFF"))},"structural_gates":f["gates"],"source":"locked_full_top_xsim_sample_gap_2"}
        rows.append(row)
    return rows

def worker_run(worker:int,cases:list[dict[str,str]],data_root:Path,hashes:dict[str,str])->list[dict[str,object]]:
    work=build(worker); logs=EXACT/"results/xsim_snapshot_logs";logs.mkdir(parents=True,exist_ok=True); out=[]
    for case in cases:
        source=(data_root/case["mem_path"]).resolve(); digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=hashes[case["case_id"]]:raise RuntimeError(f"input hash mismatch: {case['case_id']}")
        shutil.copyfile(source,work/"input.mem"); log=logs/f"{case['case_id']}.log"
        run([str(VIVADO/"xsim.bat"),"tb_exact_cpp_snapshot_trace","--nolog","-tclbatch","{"+slash(work/"run.tcl")+"}"],work,log)
        out.extend(parse_log(case,log)); print(f"worker {worker}: {case['case_id']} 30/30",flush=True)
    return out

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--data-root",type=Path,required=True);p.add_argument("--workers",type=int,default=4);p.add_argument("--case-id",action="append",default=[]);a=p.parse_args()
    cases=read_csv(CASES); selected=set(a.case_id) if a.case_id else None
    if selected:cases=[c for c in cases if c["case_id"] in selected]
    hashes={r["case_id"]:r["sha256"] for r in read_csv(MANIFEST)}; chunks=[cases[i::a.workers] for i in range(a.workers)]; all_rows=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(worker_run,i,c,a.data_root.resolve(),hashes) for i,c in enumerate(chunks) if c]
        for f in futures:all_rows.extend(f.result())
    order={c["case_id"]:i for i,c in enumerate(cases)};all_rows.sort(key=lambda r:(order[str(r["case_id"])],int(r["snapshot_index"])))
    output=EXACT/"results/golden_snapshot_trace.csv"; fields=list(all_rows[0])
    with output.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(all_rows)
    digest=hashlib.sha256(output.read_bytes()).hexdigest();(EXACT/"results/golden_snapshot_trace.sha256").write_text(f"{digest}  golden_snapshot_trace.csv\n",encoding="ascii",newline="\n")
    print(f"golden snapshots: {len(all_rows)} sha256={digest}");return 0
if __name__=="__main__":raise SystemExit(main())
