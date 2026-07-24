#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,statistics
from pathlib import Path

def read(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(rows:list[dict[str,str]],scope:str,case_id:str,label:str,mode:str)->dict[str,object]:
    lat=[float(r["latency_ms"]) for r in rows];sps=[float(r["samples_per_s"]) for r in rows]
    cyc=[float(r["thread_cycles"]) for r in rows];cps=[float(r["cycles_per_sample"]) for r in rows]
    mhz=[float(r["effective_clock_mhz"]) for r in rows];cur=[int(r["current_mhz_before"]) for r in rows if r["current_mhz_before"]]
    return {"scope":scope,"case_id":case_id,"class_label":label,"mode":mode,"runs":len(rows),"samples_per_run":int(rows[0]["samples"]),
            "latency_median_ms":f"{statistics.median(lat):.9f}","latency_mean_ms":f"{statistics.mean(lat):.9f}",
            "latency_stddev_ms":f"{statistics.stdev(lat):.9f}","latency_min_ms":f"{min(lat):.9f}","latency_max_ms":f"{max(lat):.9f}",
            "samples_per_s_median":f"{statistics.median(sps):.3f}","samples_per_s_mean":f"{statistics.mean(sps):.3f}",
            "thread_cycles_median":f"{statistics.median(cyc):.3f}","cycles_per_sample_median":f"{statistics.median(cps):.6f}",
            "effective_clock_mhz_median":f"{statistics.median(mhz):.3f}","current_mhz_min":min(cur) if cur else "","current_mhz_max":max(cur) if cur else "",
            "output_exact_count":sum(r["output_exact"]=="1" for r in rows)}
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--raw",type=Path,required=True);ap.add_argument("--summary",type=Path,required=True);ap.add_argument("--comparison",type=Path,required=True);ap.add_argument("--fpga-summary",type=Path,required=True);a=ap.parse_args()
    rows=read(a.raw);assert len(rows)==720
    modes=("kernel","end_to_end");cases=sorted(set(r["case_id"] for r in rows));assert len(cases)==36
    assert all(r["output_exact"]=="1" and r["accepted_samples"]=="1800000" and r["snapshots"]=="30" and r["decisions"]=="1" and r["trace_enabled"]=="0" and r["march_native_enabled"]=="1" and r["affinity_cpu"]=="2" for r in rows)
    out=[]
    for cid in cases:
        for mode in modes:
            group=[r for r in rows if r["case_id"]==cid and r["mode"]==mode]
            assert len(group)==10 and sorted(int(r["repetition"]) for r in group)==list(range(1,11))
            out.append(stats(group,"case",cid,group[0]["class_label"],mode))
    aggregate={}
    for mode in modes:
        group=[r for r in rows if r["mode"]==mode];assert len(group)==360
        aggregate[mode]=stats(group,"all_cases","ALL","ALL",mode);out.append(aggregate[mode])
    a.summary.parent.mkdir(parents=True,exist_ok=True)
    with a.summary.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator="\n");w.writeheader();w.writerows(out)
    fpga=json.loads(a.fpga_summary.read_text(encoding="utf-8"));assert fpga["status"]=="CYCLE_DERIVED" and fpga["sample_gap_cycles"]==2 and fpga["clock_frequency_hz"]==100000000
    fpga_ms=float(fpga["total_latency_ms"]["median"]);cpu_ms=float(aggregate["kernel"]["latency_median_ms"]);ratio=cpu_ms/fpga_ms
    comparison={"comparison_name":"single-thread Exact C++ versus cycle-derived FPGA-core speedup estimate","cpu_metric":"measured kernel-only median over 360 runs","cpu_latency_ms":f"{cpu_ms:.9f}","fpga_reference":"cycle-derived FPGA accelerator-core latency","fpga_cycles":5401260,"fpga_clock_hz":100000000,"fpga_latency_ms":f"{fpga_ms:.9f}","ratio_cpu_over_fpga":f"{ratio:.9f}","interpretation":f"cycle-derived FPGA core latency is {ratio:.6f}x lower than measured Exact C++ kernel latency" if ratio>=1 else f"measured Exact C++ kernel latency is {1/ratio:.6f}x lower than cycle-derived FPGA core latency","fpga_scope":"excludes host transfer, MicroBlaze, UART, board power, and system latency","board_latency_status":"PENDING_BOARD","board_power_status":"PENDING_BOARD","board_energy_status":"PENDING_BOARD"}
    with a.comparison.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(comparison),lineterminator="\n");w.writeheader();w.writerow(comparison)
    result={"status":"pass","raw_rows":len(rows),"cases":len(cases),"runs_per_case_per_mode":10,"raw_sha256":sha(a.raw),"summary_sha256":sha(a.summary),"comparison_sha256":sha(a.comparison),"kernel":aggregate["kernel"],"end_to_end":aggregate["end_to_end"],"cpu_over_fpga_ratio":ratio}
    print(json.dumps(result,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
