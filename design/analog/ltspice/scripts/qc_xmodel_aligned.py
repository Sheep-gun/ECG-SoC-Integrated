#!/usr/bin/env python3
"""Consolidate aligned run/log QC and generated-artifact hashes."""
from __future__ import annotations
import csv, hashlib, re, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/"results/xmodel_aligned/logs"; RAW=ROOT/"results/xmodel_aligned/raw"
TABLE=ROOT/"tables/xmodel_aligned_execution_manifest.csv"
FATAL=re.compile(r"timestep too small|singular matrix|fatal error|could not converge|monotonically increasing",re.I)
WARN=re.compile(r"warning|gmin stepping|source stepping|floating node",re.I)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def main():
    rows=[]
    for lp in sorted(LOG.glob("*.log")):
        s=lp.stem; text=lp.read_text(errors="replace")
        rp=RAW/f"{s}.raw"; cmd=LOG/f"{s}.command.txt"
        elapsed=re.search(r"Total elapsed time:\s*([0-9.]+) seconds",text)
        rows.append({"run_id":s,"status":"EXECUTED" if elapsed and not FATAL.search(text) and rp.exists() else "ERROR","ltspice_version":"26.0.1","log_path":lp.relative_to(ROOT).as_posix(),"raw_path":rp.relative_to(ROOT).as_posix() if rp.exists() else "","raw_bytes":rp.stat().st_size if rp.exists() else "","elapsed_s":elapsed.group(1) if elapsed else "","fatal_pattern":bool(FATAL.search(text)),"warning_pattern":bool(WARN.search(text)),"command_path":cmd.relative_to(ROOT).as_posix() if cmd.exists() else ""})
    TABLE.parent.mkdir(exist_ok=True)
    with TABLE.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    shutil.copy2(TABLE,ROOT/"tables/simulation_log_qc.csv")
    shutil.copy2(TABLE,ROOT/"tables/executed_simulations.csv")
    result_files=[
        "xmodel_aligned_nominal_ac_metrics.csv","xmodel_aligned_nominal_transient_metrics.csv",
        "xmodel_aligned_track_hold_metrics.csv","xmodel_aligned_adc_mapping_metrics.csv",
        "xmodel_aligned_timestep_convergence.csv","xmodel_aligned_stress_results.csv",
        "xmodel_aligned_ltspice_xmodel_correlation.csv",
    ]
    with (ROOT/"tables/result_qc.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["artifact","exists","row_count","status","notes"])
        for name in result_files:
            p=ROOT/"tables"/name
            n=sum(1 for _ in p.open(encoding="utf-8-sig"))-1 if p.exists() else 0
            status="PENDING_XMODEL_EXECUTION" if name.endswith("ltspice_xmodel_correlation.csv") else "MEASURED"
            w.writerow([f"tables/{name}",p.exists(),n,status,"Pending rows contain no fabricated measured value" if status.startswith("PENDING") else "Generated from aligned raw/log evidence"])
    files=[ROOT/"schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc",ROOT/"schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.net",ROOT/"schematics/xmodel_aligned/XOpAmp_XMODEL.lib",ROOT/"results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv",ROOT/"results/xmodel_aligned/nominal/ltspice_xmodel_equivalent_adc_signed.mem",ROOT/"results/xmodel_aligned/nominal/ltspice_track_hold_adc_signed.mem"]
    with (ROOT/"tables/xmodel_aligned_artifact_sha256.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["sha256","path"])
        for p in files: w.writerow([sha(p),p.relative_to(ROOT).as_posix()])
    print(f"runs={len(rows)} errors={sum(r['status']!='EXECUTED' for r in rows)} warnings={sum(r['warning_pattern'] for r in rows)}")
if __name__=="__main__": main()
