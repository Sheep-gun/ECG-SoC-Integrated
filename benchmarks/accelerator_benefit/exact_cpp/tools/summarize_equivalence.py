#!/usr/bin/env python3
"""Create the deterministic aggregate equivalence summary."""
from __future__ import annotations
import csv,json
from pathlib import Path
EXACT=Path(__file__).resolve().parents[1];R=EXACT/"results"
def rows(name:str)->list[dict[str,str]]:
    with (R/name).open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def main()->int:
    fixed=json.loads((R/"fixed_width_test_summary.json").read_text())
    micro=rows("module_microtrace_equivalence.csv");sample=rows("sample_state_hash_equivalence.csv")
    snap=rows("snapshot_equivalence.csv");final=rows("final_equivalence.csv");identity=rows("build_identity.csv")
    membranes=sum(sum(r[f"expected_final_mem_{c}"]==r[f"actual_final_mem_{c}"] for c in ("NSR","CHF","ARR","AFF")) for r in final)
    summary={
        "status":"pass",
        "exactness_terminology":"exact C++ baseline",
        "locked_model_id":"structural_guarded_silent_aff_1008710",
        "locked_commit":"c6b80de19cdcad5b7e43fe7835588b629d847f75",
        "parameter_payload_sha256":"7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b",
        "fixed_width":{"checks":fixed["checks"],"failures":fixed["failures"]},
        "module_microtrace":{"matched":sum(r["exact_match"]=="1" for r in micro),"total":len(micro)},
        "accepted_sample_state_hash":{"matched":sum(int(r["matched_samples"]) for r in sample),"total":sum(int(r["accepted_samples_compared"]) for r in sample),"cases":len(sample)},
        "snapshot_boundaries":{"matched":sum(r["snapshot_match"]=="1" for r in snap),"total":len(snap)},
        "final_predictions":{"matched":sum(r["expected_final_pred"]==r["actual_final_pred"] for r in final),"total":len(final)},
        "final_membranes":{"matched":membranes,"total":len(final)*4},
        "debug_release_identity":{"matched":sum(r["exact_match"]=="1" for r in identity),"total":len(identity)},
        "golden_snapshot_trace_sha256":"7fbdaf2a4a182a3c2757e7c7f923ff857b79d96756b509f75c588db515717a13",
        "benchmark_status":"PERFORMANCE_MEASUREMENT_PENDING",
        "performance_values_present":False,
    }
    required=[fixed["failures"]==0,len(micro)==18 and all(r["exact_match"]=="1" for r in micro),
              len(sample)>=4 and all(r["exact_match"]=="1" for r in sample),
              len(snap)==1080 and all(r["snapshot_match"]=="1" for r in snap),
              len(final)==36 and all(r["exact_match"]=="1" for r in final),membranes==144,
              len(identity)==36 and all(r["exact_match"]=="1" for r in identity)]
    if not all(required):summary["status"]="fail"
    (R/"equivalence_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(summary,indent=2));return 0 if summary["status"]=="pass" else 1
if __name__=="__main__":raise SystemExit(main())
