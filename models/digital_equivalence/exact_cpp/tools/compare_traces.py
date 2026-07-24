#!/usr/bin/env python3
"""Compare normalized locked-XSim and hand-written C++ Snapshot traces."""
from __future__ import annotations
import csv,json
from pathlib import Path

EXACT=Path(__file__).resolve().parents[1]; RESULTS=EXACT/"results"
CLASSES=("NSR","CHF","ARR","AFF")
FEATURES=("beat_count","pnn_match_count","pnn_mismatch_count","dscr_flip_count","dscr_slope_count","ram_code_sum","ram_code_count","rdm_valid_count","rdm_code_sum","ectopic_pair_count","qrs_maf_count","qrs_width_abn_count","qrs_complex_abn_count","qrs_energy_abn_count","rbbb_delay_like_count","rbbb_delay_applied_count","pre_qrs_bump_count","abnormal_evidence_count","rhythm_irregular_evidence_count","morphology_evidence_count")

def read(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def vector(row:dict[str,str],prefix:str)->str:return "/".join(row[prefix+c] for c in CLASSES)

def main()->int:
    expected=read(RESULTS/"golden_snapshot_trace.csv"); actual=read(RESULTS/"cpp_snapshot_trace.csv")
    amap={(r["case_id"],r["snapshot_index"]):r for r in actual}; out=[]
    for e in expected:
        key=(e["case_id"],e["snapshot_index"]); a=amap.get(key); first=""; feature=True; snap=True
        if a is None:first="missing_actual_snapshot";feature=snap=False;a={}
        else:
            checks=[("accepted_samples",e["accepted_samples"],a["accepted_samples"]),("snapshot_pred",e["snapshot_pred"],a["snapshot_pred"])]
            checks += [("class_mem_"+c,e["class_mem_"+c],a["class_mem_"+c]) for c in CLASSES]
            for name in FEATURES:
                same=e[name]==a[name]; feature=feature and same; checks.append((name,e[name],a[name]))
            checks += [("final_mem_"+c,e["final_mem_"+c],a["final_mem_"+c]) for c in CLASSES]
            checks.append(("structural_gates",e["structural_gates"].replace(" ",""),a["structural_gates"].replace(" ","")))
            for name,x,y in checks:
                if x!=y and not first:first=name
            snap=not first
        out.append({"case_id":e["case_id"],"class_label":e["class_label"],"snapshot_index":e["snapshot_index"],"accepted_samples":e["accepted_samples"],"expected_snapshot_pred":e["snapshot_pred"],"actual_snapshot_pred":a.get("snapshot_pred","") ,"expected_snapshot_scores":vector(e,"class_mem_"),"actual_snapshot_scores":vector(a,"class_mem_") if a else "","expected_final_mem_state":vector(e,"final_mem_"),"actual_final_mem_state":vector(a,"final_mem_") if a else "","expected_structural_gates":e["structural_gates"],"actual_structural_gates":a.get("structural_gates",""),"feature_state_match":int(feature),"snapshot_match":int(snap),"first_mismatch_field":first})
    fields=list(out[0]); path=RESULTS/"snapshot_equivalence.csv"
    with path.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(out)
    matched=sum(int(r["snapshot_match"]) for r in out); summary={"boundaries":len(out),"matched":matched,"mismatched":len(out)-matched,"status":"pass" if matched==len(out) else "fail"}
    (RESULTS/"snapshot_equivalence_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(summary));return 0 if matched==len(out) else 1
if __name__=="__main__":raise SystemExit(main())
