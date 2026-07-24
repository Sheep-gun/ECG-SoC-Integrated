#!/usr/bin/env python3
"""Extract XMODEL-aligned LTspice evidence without inventing XMODEL results."""

from __future__ import annotations

import csv
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_results import (  # noqa: E402
    crossing_frequency, db20, dev, interp_complex_log, read_ascii_raw,
    svg_line_plot,
)

RAW = ROOT / "results" / "xmodel_aligned" / "raw"
OUT = ROOT / "results" / "xmodel_aligned" / "nominal"
TABLES = ROOT / "tables"
PLOTS = ROOT / "plots"
LSB = 3.3 / 4095.0
RAIL = 1.65
FIELDS = [
    "test_id", "variant", "source_schematic", "simulation_type", "metric",
    "target", "measured", "unit", "deviation", "status", "evidence_path", "notes",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fmt(x):
    if x is None or x == "":
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (bool, np.bool_)):
        return "true" if x else "false"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.12g}"


def metric(test_id, variant, source, sim, name, measured, unit,
           target="", deviation="", status="MEASURED", evidence="", notes=""):
    return {
        "test_id": test_id, "variant": variant, "source_schematic": source,
        "simulation_type": sim, "metric": name, "target": fmt(target),
        "measured": fmt(measured), "unit": unit, "deviation": fmt(deviation),
        "status": status, "evidence_path": evidence, "notes": notes,
    }


def write_csv(path: Path, rows: list[dict], fields=FIELDS):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def quantize(v):
    c = np.clip(v, -RAIL, RAIL)
    return np.clip(np.floor((c + RAIL) / 3.3 * 4095.0), 0, 4095).astype(np.int64)


def at(t, y, q):
    return np.interp(q, t, y)


def lag_metrics(a, b, max_lag=20):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = a - b
    corr0 = float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else float("nan")
    best = (float("-inf"), 0, float("nan"))
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            aa, bb = a[-lag:], b[:lag]
        elif lag > 0:
            aa, bb = a[:-lag], b[lag:]
        else:
            aa, bb = a, b
        c = float(np.corrcoef(aa, bb)[0, 1]) if len(aa) > 1 and np.std(aa) and np.std(bb) else float("nan")
        if np.isfinite(c) and c > best[0]:
            best = (c, lag, float(np.sqrt(np.mean((aa - bb) ** 2))))
    return {
        "mean": float(np.mean(d)), "mae": float(np.mean(np.abs(d))),
        "rms": float(np.sqrt(np.mean(d*d))), "max": float(np.max(np.abs(d))),
        "corr0": corr0, "best_corr": best[0], "best_lag": best[1], "best_rms": best[2],
    }


def panel_svg(path: Path, title: str, x, panels, verticals=()):
    """Small dependency-free stacked-panel SVG for mixed-unit S/H evidence."""
    width, ph, left, right, top, bottom = 1150, 145, 90, 35, 55, 55
    height = top + bottom + ph * len(panels)
    x = np.asarray(x); xlo, xhi = float(x.min()), float(x.max())
    colors = ["#1565c0", "#d84315", "#2e7d32", "#6a1b9a"]
    def X(v): return left + (v-xlo)/(xhi-xlo)*(width-left-right)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{title}</text>']
    for pi, (label, series) in enumerate(panels):
        y0 = top + pi*ph; vals = np.concatenate([np.asarray(v) for v in series.values()])
        lo, hi = float(np.nanmin(vals)), float(np.nanmax(vals))
        if hi == lo: hi = lo + 1
        pad = .08*(hi-lo); lo -= pad; hi += pad
        def Y(v): return y0 + 12 + (hi-v)/(hi-lo)*(ph-28)
        parts.append(f'<rect x="{left}" y="{y0+10}" width="{width-left-right}" height="{ph-25}" fill="none" stroke="#999"/>')
        parts.append(f'<text x="12" y="{y0+ph/2}" font-family="Arial" font-size="13">{label}</text>')
        for vv in verticals:
            parts.append(f'<line x1="{X(vv):.2f}" y1="{y0+10}" x2="{X(vv):.2f}" y2="{y0+ph-15}" stroke="#777" stroke-dasharray="4,4"/>')
        for si, (name, yy) in enumerate(series.items()):
            step = max(1, len(x)//2500); pts = " ".join(f"{X(xx):.2f},{Y(yv):.2f}" for xx, yv in zip(x[::step], np.asarray(yy)[::step]))
            parts.append(f'<polyline fill="none" stroke="{colors[si%len(colors)]}" stroke-width="1.2" points="{pts}"/>')
            parts.append(f'<text x="{width-right-8-si*155}" y="{y0+25}" text-anchor="end" font-family="Arial" font-size="12" fill="{colors[si%len(colors)]}">{name}</text>')
    parts.append(f'<text x="{width/2}" y="{height-15}" text-anchor="middle" font-family="Arial" font-size="14">time (s)</text></svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def parse_ac():
    source = "schematics/xmodel_aligned/xma_ac_nominal.cir"
    rawp = RAW / "xma_ac_nominal.raw"; ev = rel(rawp)
    d = read_ascii_raw(rawp)
    f = d["frequency"].real
    vin = d["v(inp_raw)"] - d["v(inn_raw)"]
    hpd = d["v(hpf_p)"] - d["v(hpf_n)"]
    hpf = hpd/vin; ia = d["v(ia_out)"]/hpd
    notch = d["v(lpf_in)"]/d["v(ia_out)"]
    lpf = d["v(afe_out)"]/d["v(lpf_in)"]
    full = d["v(afe_out)"]/vin
    rows = []
    hpb = float(np.median(np.abs(hpf[(f >= 5) & (f <= 20)])))
    hfc = crossing_frequency(f, np.abs(hpf), hpb/math.sqrt(2), rising=True, lo=.05, hi=5)
    for name, val, unit, target in [
        ("-3dB_cutoff", hfc, "Hz", .4823),
        ("gain_at_1Hz", abs(interp_complex_log(f,hpf,1)), "V/V", ""),
        ("gain_at_10Hz", abs(interp_complex_log(f,hpf,10)), "V/V", ""),
    ]:
        rows.append(metric("AC_HPF","XMODEL_ALIGNED",source,"AC",name,val,unit,target,
                           dev(val,target) if target else "",evidence=ev,notes="V(HPF_P,HPF_N)/V(INP_RAW,INN_RAW)"))
    iag = abs(interp_complex_log(f,ia,10))
    rows += [
        metric("AC_IA","XMODEL_ALIGNED",source,"AC","gain_at_10Hz",iag,"V/V",201,dev(iag,201),evidence=ev,notes="V(IA_OUT)/V(HPF_P,HPF_N)"),
        metric("AC_IA","XMODEL_ALIGNED",source,"AC","gain_at_10Hz_db",20*math.log10(iag),"dB",evidence=ev),
    ]
    lpb = float(np.median(np.abs(lpf[(f >= 1) & (f <= 10)])))
    lfc = crossing_frequency(f,np.abs(lpf),lpb/math.sqrt(2),rising=False,lo=20,hi=2000)
    rows.append(metric("AC_LPF","XMODEL_ALIGNED",source,"AC","-3dB_cutoff",lfc,"Hz",150.15,dev(lfc,150.15),evidence=ev,notes="V(AFE_OUT)/V(LPF_IN)"))
    for fq in (10,60,150,1000):
        rows.append(metric("AC_LPF","XMODEL_ALIGNED",source,"AC",f"gain_at_{fq}Hz",abs(interp_complex_log(f,lpf,fq)),"V/V",evidence=ev))
    for fq in (.1,1,10,60,150,1000):
        rows.append(metric("AC_FULL_AFE","XMODEL_ALIGNED",source,"AC",f"gain_at_{fq:g}Hz",abs(interp_complex_log(f,full,fq)),"V/V",evidence=ev,notes="V(AFE_OUT)/V(INP_RAW,INN_RAW)"))

    nf = RAW/"xma_notch_fine.raw"; nd = read_ascii_raw(nf)
    ff = nd["frequency"].real; nt = nd["v(lpf_in)"]/nd["v(ia_out)"]; mag = np.abs(nt); j=int(np.argmin(mag))
    m60=abs(np.interp(60,ff,nt.real)+1j*np.interp(60,ff,nt.imag))
    nsrc="schematics/xmodel_aligned/xma_notch_fine.cir"; nev=rel(nf)
    rows += [
        metric("AC_NOTCH","XMODEL_ALIGNED",nsrc,"AC","attenuation_at_60Hz",20*math.log10(max(m60,1e-300)),"dB",evidence=nev,notes="V(NOTCH_OUT)/V(NOTCH_IN)=V(LPF_IN)/V(IA_OUT)"),
        metric("AC_NOTCH","XMODEL_ALIGNED",nsrc,"AC","minimum_frequency",ff[j],"Hz",60,dev(ff[j],60),evidence=nev,notes="search window 55-65 Hz"),
        metric("AC_NOTCH","XMODEL_ALIGNED",nsrc,"AC","minimum_attenuation",20*math.log10(max(mag[j],1e-300)),"dB",evidence=nev,notes="search window 55-65 Hz"),
        metric("AC_NOTCH","XMODEL_ALIGNED",nsrc,"AC","maximum_gain_in_55_65Hz",float(np.max(mag)),"V/V",evidence=nev,notes="peaking diagnostic; no arbitrary Q claim"),
    ]
    write_csv(TABLES/"xmodel_aligned_nominal_ac_metrics.csv",rows)
    # Final canonical table now points to aligned evidence; ±5 V snapshot is preserved.
    write_csv(TABLES/"nominal_ac_metrics.csv",rows)
    svg_line_plot(PLOTS/"xmodel_aligned_hpf_response.svg","XMODEL-aligned differential HPF",f,{"HPF":db20(hpf)},"frequency (Hz)","magnitude (dB)",True,(.03,100))
    svg_line_plot(PLOTS/"xmodel_aligned_ia_response.svg","XMODEL-aligned IA",f,{"IA":db20(ia)},"frequency (Hz)","magnitude (dB)",True,(.1,1000))
    svg_line_plot(PLOTS/"xmodel_aligned_notch_response.svg","XMODEL-aligned active Twin-T",ff,{"notch":db20(nt)},"frequency (Hz)","magnitude (dB)",False,(55,65),verticals=[60])
    svg_line_plot(PLOTS/"xmodel_aligned_lpf_response.svg","XMODEL-aligned LPF + buffer",f,{"LPF":db20(lpf)},"frequency (Hz)","magnitude (dB)",True,(1,10000))
    svg_line_plot(PLOTS/"xmodel_aligned_full_afe_response.svg","XMODEL-aligned full AFE",f,{"full AFE":db20(full)},"frequency (Hz)","magnitude (dB)",True,(.03,10000),verticals=[60,150.15])
    for src,dst in [("xmodel_aligned_hpf_response.svg","hpf_response.svg"),("xmodel_aligned_ia_response.svg","ia_response.svg"),("xmodel_aligned_notch_response.svg","notch_response.svg"),("xmodel_aligned_lpf_response.svg","lpf_response.svg"),("xmodel_aligned_full_afe_response.svg","full_afe_response.svg")]:
        shutil.copy2(PLOTS/src,PLOTS/dst)
    return rows


def parse_nominal():
    rawp=RAW/"FULL_AFE_ADC_SH_xmodel_aligned.raw"; ev=rel(rawp)
    wanted={"time","v(inp_raw)","v(inn_raw)","v(hpf_p)","v(hpf_n)","v(u1_out)","v(u2_out)","v(ia_out)","v(lpf_in)","v(lpf_node)","v(afe_out)","v(clk)","v(adc_hold)","v(adc_clip)","v(adc_code)","v(adc_signed)","v(vk)"}
    d=read_ascii_raw(rawp,wanted); t=d["time"]
    source="schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc"
    sig={
        "input_diff":d["v(inp_raw)"]-d["v(inn_raw)"],
        "hpf_diff":d["v(hpf_p)"]-d["v(hpf_n)"],
        "u1_out":d["v(u1_out)"],"u2_out":d["v(u2_out)"],"ia_out":d["v(ia_out)"],
        "notch_out":d["v(lpf_in)"],"lpf_node":d["v(lpf_node)"],"afe_out":d["v(afe_out)"],
        "adc_hold":d["v(adc_hold)"],"adc_clip":d["v(adc_clip)"],
        "adc_code":d["v(adc_code)"],"adc_signed":d["v(adc_signed)"],
    }
    rows=[]
    for window,mask in (("full_0_10s",t<=10),("settled_1_10s",(t>=1)&(t<=10))):
        for name,y in sig.items():
            yy=y[mask]
            for stat,val in (("min",np.min(yy)),("max",np.max(yy)),("peak_to_peak",np.ptp(yy)),("rms",np.sqrt(np.mean(yy*yy)))):
                rows.append(metric("TRAN_STAGE",f"XMODEL_ALIGNED_{window}",source,"TRAN",f"{name}_{stat}",val,"code" if "code" in name or "signed" in name else "V",evidence=ev,notes="settling boundary=1 s"))
    opouts={"U1":d["v(u1_out)"],"U2":d["v(u2_out)"],"U3":d["v(ia_out)"],"U4":d["v(lpf_in)"],"U5":d["v(vk)"],"U6":d["v(afe_out)"]}
    m=(t>=1)&(t<=10); head={k:min(RAIL-float(np.max(v[m])),float(np.min(v[m]))+RAIL) for k,v in opouts.items()}
    for k,v in head.items(): rows.append(metric("RAIL_HEADROOM","XMODEL_ALIGNED_SETTLED",source,"TRAN",f"{k}_minimum_headroom",v,"V",evidence=ev,notes="distance to ±1.65 V rail"))
    closest=min(head,key=head.get); rows.append(metric("RAIL_HEADROOM","XMODEL_ALIGNED_SETTLED",source,"TRAN","closest_stage",closest,"stage",evidence=ev,notes=f"minimum headroom={head[closest]:.12g} V"))
    afe=d["v(afe_out)"]; cmask=np.abs(afe)>=RAIL-1e-9
    clip_duration=float(np.trapz(cmask.astype(float),t))
    rows += [
        metric("ADC_HEADROOM","XMODEL_ALIGNED",source,"TRAN","continuous_afe_minimum_headroom",min(RAIL-float(np.max(afe)),float(np.min(afe))+RAIL),"V",evidence=ev),
        metric("ADC_HEADROOM","XMODEL_ALIGNED",source,"TRAN","continuous_clip_occurred",bool(np.any(cmask)),"boolean",evidence=ev),
        metric("ADC_HEADROOM","XMODEL_ALIGNED",source,"TRAN","continuous_clip_duration",clip_duration,"s",evidence=ev,notes="time-weighted from raw; threshold |AFE_OUT| >= 1.65V-1nV"),
        metric("ADC_HEADROOM","XMODEL_ALIGNED",source,"TRAN","continuous_clip_time_ratio",clip_duration/(t[-1]-t[0]),"ratio",evidence=ev),
    ]
    hp=d["v(hpf_p)"]-d["v(hpf_n)"]; ia=d["v(ia_out)"]
    slope=float(np.dot(hp[m],ia[m])/np.dot(hp[m],hp[m])); corr=float(np.corrcoef(hp[m],ia[m])[0,1])
    rows += [metric("POLARITY","XMODEL_ALIGNED",source,"TRAN","IA_slope_vs_HPF_differential",slope,"V/V",evidence=ev,notes="positive slope means non-inverting differential polarity"),metric("POLARITY","XMODEL_ALIGNED",source,"TRAN","IA_zero_lag_correlation_vs_HPF_differential",corr,"ratio",evidence=ev)]

    aperture=np.arange(1,10001,dtype=float)*1e-3
    direct_v=at(t,afe,aperture); direct_code=quantize(direct_v); direct_signed=direct_code-2048
    valid=aperture+0.1e-6; hold_v=at(t,d["v(adc_hold)"],valid); clip_v=np.clip(hold_v,-RAIL,RAIL)
    th_code=np.rint(at(t,d["v(adc_code)"],valid)).astype(np.int64); th_signed=th_code-2048
    acq_t=aperture-0.48e-6; acq=at(t,afe,acq_t)-at(t,d["v(adc_hold)"],acq_t)
    # Droop window excludes both control edges: after falling edge completion
    # through 0.1 us before the next 900 us-delayed rising edge begins.
    ds=aperture[:-1]+0.1e-6; de=aperture[:-1]+0.8999e-3
    droop=at(t,d["v(adc_hold)"],de)-at(t,d["v(adc_hold)"],ds)
    trans=np.flatnonzero(np.rint(d["v(adc_code)"][1:])!=np.rint(d["v(adc_code)"][:-1]))+1
    tt=t[trans]; phase=np.mod(tt,1e-3); hold_change_mask=(tt>=1e-3)&(tt<10)&(phase>0.1e-6)&(phase<0.8999e-3)
    hold_change_times=tt[hold_change_mask]; hold_changes=len(hold_change_times)
    hold_period_counts=np.bincount(np.floor(hold_change_times/1e-3).astype(int),minlength=10001)
    clip_direct=(direct_code<=0)|(direct_code>=4095); clip_th=(th_code<=0)|(th_code>=4095)
    throws=[
        metric("TH_APERTURE","XMODEL_ALIGNED",source,"TRAN","first_direct_aperture",1e-3,"s",1e-3,0,evidence=ev,notes="XMODEL first falling edge"),
        metric("TH_APERTURE","XMODEL_ALIGNED",source,"TRAN","switch_off_threshold_crossing",0.99952e-3,"s",evidence=ev,notes="PULSE falling 999-1000us; SW_ADC turn-off at 2.4V"),
        metric("TH_APERTURE","XMODEL_ALIGNED",source,"TRAN","valid_hold_phase_after_aperture",0.1e-6,"s",evidence=ev),
        metric("TH_ACQUISITION","XMODEL_ALIGNED",source,"TRAN","maximum_absolute_error",np.max(np.abs(acq)),"V",evidence=ev),
        metric("TH_ACQUISITION","XMODEL_ALIGNED",source,"TRAN","rms_error",np.sqrt(np.mean(acq*acq)),"V",evidence=ev),
        metric("TH_ACQUISITION","XMODEL_ALIGNED",source,"TRAN","maximum_absolute_error",np.max(np.abs(acq))/LSB,"LSB",evidence=ev),
        metric("TH_DROOP","XMODEL_ALIGNED",source,"TRAN","maximum_absolute_droop",np.max(np.abs(droop)),"V",evidence=ev),
        metric("TH_DROOP","XMODEL_ALIGNED",source,"TRAN","rms_droop",np.sqrt(np.mean(droop*droop)),"V",evidence=ev),
        metric("TH_DROOP","XMODEL_ALIGNED",source,"TRAN","maximum_absolute_droop",np.max(np.abs(droop))/LSB,"LSB",evidence=ev),
        metric("TH_CODE","XMODEL_ALIGNED",source,"TRAN","valid_sample_count",len(th_code),"samples",10000,0,evidence=ev),
        metric("TH_CODE","XMODEL_ALIGNED",source,"TRAN","hold_interval_code_change_count",hold_changes,"changes",evidence=ev),
        metric("TH_CODE","XMODEL_ALIGNED",source,"TRAN","hold_periods_with_code_change",int(np.sum(hold_period_counts>0)),"periods",evidence=ev),
        metric("TH_CODE","XMODEL_ALIGNED",source,"TRAN","maximum_code_changes_in_one_hold",int(np.max(hold_period_counts)),"changes/period",evidence=ev),
        metric("ADC_DIRECT","XMODEL_ALIGNED",source,"TRAN","clip_count",int(np.sum(clip_direct)),"samples",evidence=ev),
        metric("ADC_DIRECT","XMODEL_ALIGNED",source,"TRAN","clip_ratio",float(np.mean(clip_direct)),"ratio",evidence=ev),
        metric("ADC_TRACK_HOLD","XMODEL_ALIGNED",source,"TRAN","clip_count",int(np.sum(clip_th)),"samples",evidence=ev),
        metric("ADC_TRACK_HOLD","XMODEL_ALIGNED",source,"TRAN","clip_ratio",float(np.mean(clip_th)),"ratio",evidence=ev),
    ]
    rows.extend(throws)
    write_csv(TABLES/"xmodel_aligned_nominal_transient_metrics.csv",rows)
    write_csv(TABLES/"nominal_transient_metrics.csv",rows)
    write_csv(TABLES/"xmodel_aligned_track_hold_metrics.csv",throws)
    write_csv(TABLES/"track_hold_metrics.csv",throws)

    OUT.mkdir(parents=True,exist_ok=True)
    sample_fields=["sample_index","time_s","afe_out_v","adc_hold_v","adc_clip_v","adc_code","adc_signed","hex12","direct_adc_code","direct_adc_signed","direct_hex12","th_adc_code","th_adc_signed","th_hex12"]
    sample_path=OUT/"ltspice_xmodel_aligned_adc_samples.csv"
    with sample_path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(sample_fields)
        for i in range(len(aperture)):
            dhex=f"{int(direct_signed[i])&0xFFF:03X}"; thex=f"{int(th_signed[i])&0xFFF:03X}"
            w.writerow([i,fmt(aperture[i]),fmt(direct_v[i]),fmt(hold_v[i]),fmt(clip_v[i]),int(direct_code[i]),int(direct_signed[i]),dhex,int(direct_code[i]),int(direct_signed[i]),dhex,int(th_code[i]),int(th_signed[i]),thex])
    for name,vals,label in [("ltspice_xmodel_equivalent_adc_signed.mem",direct_signed,"direct XMODEL-equivalent aperture"),("ltspice_track_hold_adc_signed.mem",th_signed,"LTspice Track-and-Hold")]:
        with (OUT/name).open("w",encoding="ascii",newline="\n") as f:
            f.write(f"// LTspice-derived vector; {label}; not an official locked XMODEL/RTL vector\n")
            for v in vals: f.write(f"{int(v)&0xFFF:03X}\n")
    # Canonical final vector is the direct XMODEL-equivalent stream; TH remains separate.
    shutil.copy2(sample_path,ROOT/"results"/"nominal"/"ltspice_adc_samples.csv")
    shutil.copy2(OUT/"ltspice_xmodel_equivalent_adc_signed.mem",ROOT/"results"/"nominal"/"ltspice_adc_signed.mem")

    # 50 us evidence export; raw remains the authoritative full-resolution source.
    grid=np.arange(0,10.0000001,50e-6); export=OUT/"transient_export_50us.csv"
    names=["inp_raw","inn_raw","hpf_p","hpf_n","u1_out","u2_out","ia_out","lpf_in","lpf_node","afe_out","clk","adc_hold","adc_clip","adc_code","adc_signed"]
    with export.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["time_s"]+names)
        arrays=[at(t,d[f"v({n})"],grid) for n in names]
        for i,tm in enumerate(grid): w.writerow([fmt(tm)]+[fmt(a[i]) for a in arrays])

    # Waveform and QRS/S&H plots.
    pm=(t>=0)&(t<=10); step=max(1,int(np.sum(pm))//10000)
    svg_line_plot(PLOTS/"xmodel_aligned_patient_stage_waveforms.svg","XMODEL-aligned patient ECG stages",t[pm][::step],{"input diff x201":sig["input_diff"][pm][::step]*201,"IA":ia[pm][::step],"notch":d["v(lpf_in)"][pm][::step],"AFE":afe[pm][::step]},"time (s)","voltage (V)")
    sm=(t>=1)&(t<=10); step=max(1,int(np.sum(sm))//10000)
    svg_line_plot(PLOTS/"xmodel_aligned_patient_after_settling.svg","XMODEL-aligned patient ECG after 1 s",t[sm][::step],{"input diff x201":sig["input_diff"][sm][::step]*201,"IA":ia[sm][::step],"notch":d["v(lpf_in)"][sm][::step],"AFE":afe[sm][::step]},"time (s)","voltage (V)")
    ai=int(np.argmax(np.abs(np.diff(direct_v))))+1; center=aperture[ai]; zm=(t>=center-.005)&(t<=center+.005)
    panel_svg(PLOTS/"xmodel_aligned_track_hold_zoom.svg",f"Track-and-Hold / ADC around QRS-like maximum slope ({center:.3f} s)",t[zm],[
        ("analog (V)",{"AFE_OUT":afe[zm],"ADC_HOLD":d["v(adc_hold)"][zm]}),
        ("clock (V)",{"CLK":d["v(clk)"][zm]}),
        ("ADC code",{"ADC_CODE":d["v(adc_code)"][zm]}),
        ("signed code",{"ADC_SIGNED":d["v(adc_signed)"][zm]}),
    ],aperture[(aperture>=center-.005)&(aperture<=center+.005)])
    shutil.copy2(PLOTS/"xmodel_aligned_patient_stage_waveforms.svg",PLOTS/"patient_stage_waveforms.svg")
    shutil.copy2(PLOTS/"xmodel_aligned_patient_after_settling.svg",PLOTS/"patient_stage_waveforms_after_settling.svg")
    shutil.copy2(PLOTS/"xmodel_aligned_track_hold_zoom.svg",PLOTS/"track_hold_zoom.svg")
    return d, aperture, direct_code, th_code, direct_signed, th_signed


def parse_adc_mapping():
    p=RAW/"xma_adc_mapping.raw"; d=read_ascii_raw(p); t=d["time"]
    source="schematics/xmodel_aligned/xma_adc_mapping.cir"; ev=rel(p)
    tests=[("below_range",-2,.0005,0,-2048),("negative_endpoint",-1.65,.0015,0,-2048),("zero",0,.0025,2047,-1),("plus_half_lsb",.5*LSB,.0035,2048,0),("positive_endpoint",1.65,.0045,4095,2047),("above_range",2,.0055,4095,2047)]
    rows=[]
    for name,vin,tm,ec,es in tests:
        code=int(round(float(at(t,d["v(adc_code)"],tm)))); signed=int(round(float(at(t,d["v(adc_signed)"],tm))))
        rows += [metric("ADC_MAPPING","XMODEL_ALIGNED",source,"TRAN",f"{name}_adc_code",code,"code",ec,code-ec,"MATCH" if code==ec else "MISMATCH",ev,notes=f"input={vin:.12g} V; floor quantizer"),metric("ADC_MAPPING","XMODEL_ALIGNED",source,"TRAN",f"{name}_adc_signed",signed,"code",es,signed-es,"MATCH" if signed==es else "MISMATCH",ev)]
    code=np.rint(d["v(adc_code)"]).astype(int)
    monotonic=bool(np.all(np.diff(code)>=0))
    rows.append(metric("ADC_MAPPING","XMODEL_ALIGNED",source,"TRAN","monotonicity",monotonic,"boolean",True,"","MATCH" if monotonic else "MISMATCH",ev))
    rows.append(metric("ADC_MAPPING","XMODEL_ALIGNED",source,"TRAN","output_code_min",int(code.min()),"code",0,int(code.min()),"MATCH" if code.min()==0 else "MISMATCH",ev))
    rows.append(metric("ADC_MAPPING","XMODEL_ALIGNED",source,"TRAN","output_code_max",int(code.max()),"code",4095,int(code.max()-4095),"MATCH" if code.max()==4095 else "MISMATCH",ev))
    write_csv(TABLES/"xmodel_aligned_adc_mapping_metrics.csv",rows); write_csv(TABLES/"adc_mapping_metrics.csv",rows)
    svg_line_plot(PLOTS/"xmodel_aligned_adc_mapping.svg","XMODEL-aligned behavioral 12-bit ADC mapping",d["v(adc_in)"],{"ADC_CODE":d["v(adc_code)"]},"input (V)","code")
    shutil.copy2(PLOTS/"xmodel_aligned_adc_mapping.svg",PLOTS/"adc_mapping.svg")
    return rows


def parse_convergence(final_d, aperture, direct_final, th_final):
    p=RAW/"xma_nominal_convergence_10u.raw"; d=read_ascii_raw(p); t=d["time"]
    q=aperture[aperture<=2.0]; n=len(q)
    direct10=quantize(at(t,d["v(afe_out)"],q)); th10=np.rint(at(t,d["v(adc_code)"],q+.1e-6)).astype(int)
    afe5=at(final_d["time"],final_d["v(afe_out)"],q); afe10=at(t,d["v(afe_out)"],q); diff=afe5-afe10
    rows=[]; src="schematics/xmodel_aligned/xma_nominal_convergence_10u.cir"; ev=rel(p)
    rows += [metric("TIMESTEP","XMODEL_ALIGNED_5us_vs_10us",src,"TRAN","sample_count",n,"samples",evidence=ev,notes="final 5us graphical raw vs 2s 10us companion"),metric("TIMESTEP","XMODEL_ALIGNED_5us_vs_10us",src,"TRAN","AFE_OUT_rms_difference",np.sqrt(np.mean(diff*diff)),"V",evidence=ev),metric("TIMESTEP","XMODEL_ALIGNED_5us_vs_10us",src,"TRAN","AFE_OUT_max_absolute_difference",np.max(np.abs(diff)),"V",evidence=ev),metric("TIMESTEP","XMODEL_ALIGNED_5us_vs_10us",src,"TRAN","direct_code_difference_count",int(np.sum(direct_final[:n]!=direct10)),"samples",evidence=ev),metric("TIMESTEP","XMODEL_ALIGNED_5us_vs_10us",src,"TRAN","track_hold_code_difference_count",int(np.sum(th_final[:n]!=th10)),"samples",evidence=ev)]
    write_csv(TABLES/"xmodel_aligned_timestep_convergence.csv",rows); write_csv(TABLES/"timestep_convergence.csv",rows)
    return rows


def parse_stress():
    basep=RAW/"xma_nominal.raw"; base=read_ascii_raw(basep,{"time","v(afe_out)"}); q=np.arange(1,5001)*1e-3
    base_code=quantize(at(base["time"],base["v(afe_out)"],q))
    cases=["dc_p10m","dc_p50m","dc_p100m","dc_p200m","dc_m200m","bw_0p1hz_1m","bw_0p2hz_2m","pli60","pli50","mm_0_pli60","mm_0p1pct_pli60","mm_0p5pct_pli60","mm_1pct_pli60","gbw_100k","gbw_500k","gbw_1m","gbw_5m","vos_0p5m","vos_1m","vos_2m"]
    cache={"nominal":base_code}; rows=[]; summaries=[]
    wanted={"time","v(afe_out)","v(u1_out)","v(u2_out)","v(ia_out)","v(lpf_in)","v(vk)"}
    parsed={}
    for case in cases:
        p=RAW/f"xma_{case}.raw"; d=read_ascii_raw(p,wanted); parsed[case]=d
        code=quantize(at(d["time"],d["v(afe_out)"],q)); cache[case]=code
        ref=cache["mm_0_pli60"] if case.startswith("mm_") and case!="mm_0_pli60" else base_code
        diff=code-ref; settled=np.arange(len(q))>=2000
        clips=(code<=0)|(code>=4095); ev=rel(p); src=f"schematics/xmodel_aligned/xma_{case}.cir"
        outs=[at(d["time"],d[k],q[settled]) for k in ("v(u1_out)","v(u2_out)","v(ia_out)","v(lpf_in)","v(vk)","v(afe_out)")]
        head=min(min(RAIL-float(np.max(v)),float(np.min(v))+RAIL) for v in outs)
        vals=[("signed_code_min",int((code-2048).min()),"code"),("signed_code_max",int((code-2048).max()),"code"),("clip_count_total",int(clips.sum()),"samples"),("clip_count_after_2s",int(clips[settled].sum()),"samples"),("mean_code_difference_after_2s",float(np.mean(diff[settled])),"LSB"),("mae_code_difference_after_2s",float(np.mean(np.abs(diff[settled]))),"LSB"),("rms_code_difference_after_2s",float(np.sqrt(np.mean(diff[settled]**2))),"LSB"),("maximum_code_difference_after_2s",int(np.max(np.abs(diff[settled]))),"LSB"),("minimum_opamp_rail_headroom_after_2s",head,"V")]
        for name,val,unit in vals: rows.append(metric(f"STRESS_{case}","XMODEL_ALIGNED",src,"TRAN",name,val,unit,evidence=ev,notes="reference=MM0 PLI60" if case.startswith("mm_") else "reference=aligned nominal"))
        if case.startswith("dc_") or case.startswith("bw_"):
            early=np.arange(len(q))<2000; bad=np.flatnonzero((np.abs(diff)>20)&early); rec=(bad[-1]+1)/1000 if len(bad) else 0.0
            recovered=bool(not len(bad) or bad[-1] < 1999)
            rows.append(metric(f"STRESS_{case}","XMODEL_ALIGNED",src,"TRAN","recovery_last_sample_over_20_code",rec,"s",evidence=ev,notes="fixed XMODEL run_stress.sh definition; input disturbance steps at 50us"))
            rows.append(metric(f"STRESS_{case}","XMODEL_ALIGNED",src,"TRAN","recovered_within_first_2s_window",recovered,"boolean",evidence=ev,notes="false means the fixed-script 2.000 s search window ended before a recovery time could be established; 2.000 s is censored, not a claimed recovery"))
        summaries.append((case,float(np.sqrt(np.mean(diff[settled]**2)))))

    # AC mismatch: common-mode leakage and notch shift/depth.
    for label in ("0","0p1pct","0p5pct","1pct"):
        cp=RAW/f"xma_mm_{label}_cmrr.raw"; cd=read_ascii_raw(cp); ia=abs(cd["v(ia_out)"][0]); cmrr=20*math.log10(201/ia)
        npth=RAW/f"xma_mm_{label}_notch.raw"; nd=read_ascii_raw(npth); ff=nd["frequency"].real; nt=np.abs(nd["v(lpf_in)"]/nd["v(ia_out)"]); j=int(np.argmin(nt)); m60=float(np.interp(60,ff,nt))
        src=f"schematics/xmodel_aligned/xma_mm_{label}_notch.cir"
        rows += [metric(f"STRESS_MM_{label}","XMODEL_ALIGNED",src,"AC","IA_common_mode_rejection_at_10Hz",cmrr,"dB",evidence=rel(cp),notes="both inputs AC 1 V; 20log10(201/|IA_OUT|)"),metric(f"STRESS_MM_{label}","XMODEL_ALIGNED",src,"AC","notch_minimum_frequency",ff[j],"Hz",evidence=rel(npth),notes="55-65 Hz search"),metric(f"STRESS_MM_{label}","XMODEL_ALIGNED",src,"AC","notch_minimum_attenuation",20*math.log10(max(nt[j],1e-300)),"dB",evidence=rel(npth)),metric(f"STRESS_MM_{label}","XMODEL_ALIGNED",src,"AC","notch_attenuation_at_60Hz",20*math.log10(max(m60,1e-300)),"dB",evidence=rel(npth))]
    write_csv(TABLES/"xmodel_aligned_stress_results.csv",rows); write_csv(TABLES/"stress_results.csv",rows)
    x=np.arange(len(summaries),dtype=float); svg_line_plot(PLOTS/"xmodel_aligned_stress_summary.svg","XMODEL-aligned stress code difference after 2 s",x,{"RMS code difference":np.array([v for _,v in summaries])},"case index (see CSV)","LSB")
    shutil.copy2(PLOTS/"xmodel_aligned_stress_summary.svg",PLOTS/"stress_summary.svg")
    return rows


def correlation_table(direct, th):
    p=TABLES/"xmodel_aligned_ltspice_xmodel_correlation.csv"; rows=[]
    # Internal LTspice diagnostic is measurable, but it is not the XMODEL gate.
    lm=lag_metrics(direct,th)
    for name,val,unit in [("sample_count",len(direct),"samples"),("sample_aperture",1e-3,"s"),("direct_signed_min",int(np.min(direct)),"code"),("direct_signed_max",int(np.max(direct)),"code"),("th_signed_min",int(np.min(th)),"code"),("th_signed_max",int(np.max(th)),"code"),("zero_lag_mean_error",lm["mean"],"LSB"),("zero_lag_MAE",lm["mae"],"LSB"),("zero_lag_RMS_error",lm["rms"],"LSB"),("zero_lag_maximum_error",lm["max"],"LSB"),("zero_lag_correlation",lm["corr0"],"ratio"),("best_lag",lm["best_lag"],"samples"),("best_lag_correlation",lm["best_corr"],"ratio")]:
        rows.append(metric("LTSPICE_DIRECT_VS_TH","XMODEL_ALIGNED","results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv","POST",name,val,unit,status="MEASURED",evidence="results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv",notes="diagnostic only; not LTspice↔XMODEL equivalence"))
    for scope in ("full_10s","settled_after_1s"):
        for name,unit in [("sample_count","samples"),("sample_aperture","s"),("signed_code_min","code"),("signed_code_max","code"),("clipping_count","samples"),("mean_error","LSB"),("MAE","LSB"),("RMS_error","LSB"),("maximum_error","LSB"),("zero_lag_correlation","ratio"),("best_lag","samples"),("best_lag_correlation","ratio"),("stress_code_difference","LSB")]:
            rows.append(metric("LTSPICE_VS_FIXED_XMODEL",scope,"schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc","CORRELATION",name,"",unit,target="fixed XMODEL commit 4756a5086023547328ef44fd5fd87da3c250dc39",status="PENDING_XMODEL_EXECUTION",evidence="results/xmodel_aligned/xmodel_reference/adc_nominal.txt",notes="Questa/XMODEL executable and fixed output are unavailable in this workspace; no value inferred"))
    write_csv(p,rows); write_csv(TABLES/"xmodel_ltspice_comparison.csv",rows)
    return rows


def main():
    TABLES.mkdir(exist_ok=True); PLOTS.mkdir(exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    parse_ac()
    final_d, aperture, dc, tc, ds, ts = parse_nominal()
    parse_adc_mapping()
    parse_convergence(final_d,aperture,dc,tc)
    parse_stress()
    correlation_table(ds,ts)
    print("XMODEL-aligned LTspice extraction complete")


if __name__ == "__main__":
    main()
