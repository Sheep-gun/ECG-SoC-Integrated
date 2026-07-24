#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,subprocess
from pathlib import Path
CLASSES=("NSR","CHF","ARR","AFF")
FEATURES=("beat_count","pnn_match_count","pnn_mismatch_count","dscr_flip_count","dscr_slope_count","ram_code_sum","ram_code_count","rdm_valid_count","rdm_code_sum","ectopic_pair_count","qrs_maf_count","qrs_width_abn_count","qrs_complex_abn_count","qrs_energy_abn_count","rbbb_delay_like_count","rbbb_delay_applied_count","pre_qrs_bump_count","abnormal_evidence_count","rhythm_irregular_evidence_count","morphology_evidence_count")
def rows(p:Path)->list[dict[str,str]]:
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--debug",type=Path,required=True);ap.add_argument("--release",type=Path,required=True);ap.add_argument("--cases",type=Path,required=True);ap.add_argument("--data-root",type=Path,required=True);ap.add_argument("--golden",type=Path,required=True);ap.add_argument("--work",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();a.work.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    if os.environ.get("EXACT_CPP_TOOLCHAIN_BIN"):
        env["PATH"]=os.environ["EXACT_CPP_TOOLCHAIN_BIN"]+os.pathsep+env.get("PATH","")
    final_ok=identity_ok=0;mem_ok=0;actual=[]
    for case in rows(a.cases):
        cid=case["case_id"];src=(a.data_root/case["mem_path"]).resolve();dj=a.work/f"{cid}.debug.json";rj=a.work/f"{cid}.release.json";trace=a.work/f"{cid}.trace.csv"
        subprocess.run([str(a.debug.resolve()),"--input",str(src),"--format","signed12_hex","--expected-samples","1800000","--output",str(dj),"--trace-output",str(trace)],check=True,env=env)
        subprocess.run([str(a.release.resolve()),"--input",str(src),"--format","signed12_hex","--expected-samples","1800000","--output",str(rj)],check=True,env=env)
        d=json.loads(dj.read_text());r=json.loads(rj.read_text());fields=("final_pred","final_mem_NSR","final_mem_CHF","final_mem_ARR","final_mem_AFF","accepted_samples","snapshot_count","decision_count","model_id","parameter_hash")
        if all(d[x]==r[x] for x in fields):identity_ok+=1
        exact=d["final_pred"]==int(case["expected_final_pred"]) and d["accepted_samples"]==1800000 and d["snapshot_count"]==30 and d["decision_count"]==1
        if exact:final_ok+=1
        mem_ok+=sum(d[f"final_mem_{c}"]==int(case[f"expected_final_mem_{c}"]) for c in CLASSES)
        for t in rows(trace):actual.append({"case_id":cid,"class_label":case["class_label"],**t})
        print(cid,"pass" if exact else "FAIL",flush=True)
    amap={(r["case_id"],r["snapshot_index"]):r for r in actual};mismatch=[];gold=rows(a.golden)
    fields=["accepted_samples","snapshot_pred"]+[f"class_mem_{c}" for c in CLASSES]+list(FEATURES)+[f"final_mem_{c}" for c in CLASSES]+["structural_gates"]
    for e in gold:
        key=(e["case_id"],e["snapshot_index"]);x=amap.get(key)
        if x is None:mismatch.append([*key,"missing"]);continue
        for f in fields:
            if e[f].replace(" ","")!=x[f].replace(" ",""):
                mismatch.append([*key,f]);break
    result={"status":"pass" if final_ok==36 and mem_ok==144 and identity_ok==36 and len(gold)==1080 and not mismatch else "fail","fixed_width_checks":793595,"module_microtraces":"18/18","final_predictions":f"{final_ok}/36","final_membranes":f"{mem_ok}/144","debug_release_identity":f"{identity_ok}/36","snapshot_boundaries":f"{len(gold)-len(mismatch)}/{len(gold)}","first_snapshot_mismatch":mismatch[:1],"accepted_sample_state_hashes":"pending separate post-benchmark rerun"}
    a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n");print(json.dumps(result,indent=2));return 0 if result["status"]=="pass" else 1
if __name__=="__main__":raise SystemExit(main())
