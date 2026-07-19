#!/usr/bin/env python3
"""Compare fixed-XMODEL codes with both LTspice direct and S/H streams."""

from __future__ import annotations
import csv
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from parse_results import svg_line_plot
from parse_xmodel_aligned_results import FIELDS, lag_metrics, metric, write_csv

LTS=ROOT/"results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv"
XMR=ROOT/"results/xmodel_aligned/xmodel_reference/adc_nominal.txt"
OUT=ROOT/"tables/xmodel_aligned_ltspice_xmodel_correlation.csv"

def read_ltspice():
    with LTS.open(encoding="utf-8-sig") as f:
        r=list(csv.DictReader(f))
    t=np.array([float(x["time_s"]) for x in r])
    direct=np.array([int(x["direct_adc_signed"]) for x in r])
    th=np.array([int(x["th_adc_signed"]) for x in r])
    return t,direct,th

def read_xmodel():
    vals=[]
    with XMR.open() as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"): continue
            a=line.split(); vals.append((int(a[0]),int(a[1])-2048,float(a[2])*1e-9))
    return np.array(vals,float)

def main():
    if not XMR.exists():
        raise SystemExit(f"PENDING_XMODEL_EXECUTION: missing {XMR}")
    lt, direct, th=read_ltspice(); xm=read_xmodel()
    n=min(len(lt),len(xm)); structural=(len(lt)==len(xm)==10000 and np.max(np.abs(lt[:n]-xm[:n,2]))<1e-9)
    rows=[]
    for label,data in (("DIRECT",direct[:n]),("TRACK_HOLD",th[:n])):
        for scope,mask in (("full_10s",np.ones(n,bool)),("settled_after_1s",lt[:n]>=1.0)):
            ref=xm[:n,1][mask]; got=data[mask]; lm=lag_metrics(got,ref)
            exact=bool(np.array_equal(got,ref)); status="MATCH" if structural and exact else ("CORRELATED" if structural else "MISMATCH")
            for name,val,unit in [("sample_count",len(got),"samples"),("sample_aperture",float(np.median(np.diff(lt[:n]))),"s"),("signed_code_min",int(got.min()),"code"),("signed_code_max",int(got.max()),"code"),("clipping_count",int(np.sum((got<=-2048)|(got>=2047))),"samples"),("mean_error",lm["mean"],"LSB"),("MAE",lm["mae"],"LSB"),("RMS_error",lm["rms"],"LSB"),("maximum_error",lm["max"],"LSB"),("zero_lag_correlation",lm["corr0"],"ratio"),("best_lag",lm["best_lag"],"samples"),("best_lag_correlation",lm["best_corr"],"ratio")]:
                rows.append(metric("LTSPICE_VS_FIXED_XMODEL",f"{label}_{scope}","schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc","CORRELATION",name,val,unit,status=status,evidence="results/xmodel_aligned/xmodel_reference/adc_nominal.txt",notes="MATCH=exact; CORRELATED=numeric non-bit-exact with aligned count/aperture; MISMATCH=structural count/aperture mismatch"))
    write_csv(OUT,rows); write_csv(ROOT/"tables/xmodel_ltspice_comparison.csv",rows)
    svg_line_plot(ROOT/"plots/xmodel_aligned_xmodel_waveform_comparison.svg","Fixed XMODEL vs LTspice signed codes",lt[:n],{"XMODEL":xm[:n,1],"LTspice direct":direct[:n],"LTspice S/H":th[:n]},"time (s)","signed code")
    err=direct[:n]-xm[:n,1]
    svg_line_plot(ROOT/"plots/xmodel_aligned_xmodel_error.svg","LTspice direct - fixed XMODEL",lt[:n],{"zero-lag error":err},"time (s)","LSB")
    print(OUT)

if __name__=="__main__": main()
