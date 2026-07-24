#!/usr/bin/env python3
"""Generate XMODEL-aligned LTspice AC, nominal, and analog-stress decks."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "schematics" / "xmodel_aligned"
NET = DIR / "FULL_AFE_ADC_SH_xmodel_aligned.net"
TABLE = ROOT / "tables" / "xmodel_aligned_stress_matrix.csv"
COMMIT = "4756a5086023547328ef44fd5fd87da3c250dc39"

patient = np.loadtxt(ROOT.parent / "patient100_ecg_10s.txt")
pt, pv = patient[:, 0], patient[:, 1]


def base_lines() -> list[str]:
    out = []
    for line in NET.read_text(encoding="utf-8", errors="replace").splitlines():
        low = line.strip().lower()
        if low.startswith((".tran", ".ac", ".save", ".backanno", ".end")):
            continue
        out.append(line)
    return out


def write_deck(name: str, lines: list[str]) -> Path:
    p = DIR / f"{name}.cir"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def patient_hold(t: np.ndarray) -> np.ndarray:
    idx = np.searchsorted(pt, t, side="right") - 1
    idx = np.clip(idx, 0, len(pv)-1)
    return pv[idx]


def zoh_pwl(path: Path, duration: float, pos_fn, neg_fn) -> None:
    t = np.arange(50e-6, duration + 1e-12, 50e-6)
    ph = patient_hold(t)
    pos = np.asarray(pos_fn(t, ph), dtype=float)
    neg = np.asarray(neg_fn(t, ph), dtype=float)
    for suffix, values in (("pos", pos), ("neg", neg)):
        with (path.with_name(path.stem + f"_{suffix}.txt")).open("w", encoding="ascii", newline="\n") as f:
            # The loop emits the pre-step point at 49.999 us for the first
            # 50 us update.  Keep only t=0 here so every timestamp is unique
            # and strictly increasing in LTspice's PWL reader.
            f.write("0.000000000 0\n")
            prev = 0.0
            for ti, value in zip(t, values):
                f.write(f"{ti-1e-9:.9f} {prev:.12g}\n{ti:.9f} {value:.12g}\n")
                prev = float(value)
            f.write(f"{duration+1e-6:.9f} {prev:.12g}\n")


def replace_source(lines: list[str], pos_file: str, neg_file: str) -> list[str]:
    out = []
    for line in lines:
        if line.startswith("V3 INP_RAW 0 "):
            out.append(f"V3 INP_RAW 0 PWL file={pos_file}")
        elif line.startswith("V5 INN_RAW 0 "):
            out.append(f"V5 INN_RAW 0 PWL file={neg_file}")
        else:
            out.append(line)
    return out


def apply_params(lines: list[str], mm=0.0, gbw="1e9", vos="0") -> list[str]:
    out = []
    replacements = {
        "R3 ": ("100k", "{100k*P}"), "R4 ": ("100k", "{100k*N}"),
        "R5 ": ("10k", "{10k*P}"), "R6 ": ("10k", "{10k*N}"),
        "R7 ": ("10k", "{10k*N}"), "R8 ": ("10k", "{10k*P}"),
        "R12 ": ("{RNOTCH}", "{RNOTCH*P}"), "R13 ": ("{RNOTCH}", "{RNOTCH*N}"),
        "C3 ": ("200n", "{200n*P}"), "C4 ": ("{CNOTCH}", "{CNOTCH*N}"),
        "C5 ": ("{CNOTCH}", "{CNOTCH*P}"), "R14 ": ("13.263k", "{13.263k*N}"),
    }
    for line in lines:
        if line.startswith(".param AOL_DB="):
            out.append(f".param AOL_DB=100 CMRR_DB=110 GBW_HZ={gbw} VOS={vos}")
            out.append(f".param MM={mm:.12g} P={{1+MM}} N={{1-MM}}")
            continue
        changed = line
        if mm != 0:
            for prefix, (old, new) in replacements.items():
                if changed.startswith(prefix) and changed.rstrip().endswith(old):
                    changed = changed[:changed.rfind(old)] + new
                    break
        out.append(changed)
    return out


def transient_deck(name: str, pos_file: str, neg_file: str, mm=0.0, gbw="1e9", vos="0", duration=5.001) -> Path:
    lines = apply_params(replace_source(base_lines(), pos_file, neg_file), mm, gbw, vos)
    lines.extend([
        # Stress decks use the XMODEL 50 us input-update contract and a
        # 20 us maximum step.  The final 10 s graphical nominal deck retains
        # 5 us for Track-and-Hold acquisition/droop evidence.
        f".tran 0 {duration:g} 0 20u",
        ".options plotwinsize=0",
        ".save V(INP_RAW) V(INN_RAW) V(U1_OUT) V(U2_OUT) V(IA_OUT) V(LPF_IN) V(VK) V(AFE_OUT)",
        ".end",
    ])
    return write_deck(name, lines)


def ac_deck(name: str, mm=0.0, cmrr=False, fine=False, gbw="1e9") -> Path:
    lines = apply_params(base_lines(), mm, gbw, "0")
    out = []
    for line in lines:
        if line.startswith("V3 INP_RAW 0 "):
            out.append("V3 INP_RAW 0 AC 1" if cmrr else "V3 INP_RAW 0 AC 1")
        elif line.startswith("V5 INN_RAW 0 "):
            out.append("V5 INN_RAW 0 AC 1" if cmrr else "V5 INN_RAW 0 0")
        else:
            out.append(line)
    if fine:
        out.extend([".ac lin 20001 55 65", ".save V(IA_OUT) V(LPF_IN)", ".end"])
    elif cmrr:
        out.extend([".ac list 10", ".save V(INP_RAW) V(INN_RAW) V(IA_OUT)", ".end"])
    else:
        out.extend([".ac dec 200 0.01 100k", ".save V(INP_RAW) V(INN_RAW) V(HPF_P) V(HPF_N) V(IA_OUT) V(LPF_IN) V(LPF_NODE) V(AFE_OUT) V(K_DIV) V(VK)", ".end"])
    return write_deck(name, out)


def convergence_deck() -> Path:
    """2 s, 10 us max-step companion to the final 5 us nominal run."""
    lines = apply_params(base_lines())
    lines.extend([
        ".tran 0 2.001 0 10u",
        ".options plotwinsize=0",
        ".save V(AFE_OUT) V(CLK) V(ADC_HOLD) V(ADC_CLIP) V(ADC_CODE) V(ADC_SIGNED)",
        ".end",
    ])
    return write_deck("xma_nominal_convergence_10u", lines)


def adc_mapping_deck() -> Path:
    """Behavioral ADC-only monotonic plateaus, independent of patient data."""
    return write_deck("xma_adc_mapping", [
        "* XMODEL-aligned behavioral ADC mapping; not a transistor-level SAR ADC",
        "VADCIN ADC_IN 0 PWL(0 -2 1m -2 1.001m -1.65 2m -1.65 2.001m 0 3m 0 3.001m 0.000402931 4m 0.000402931 4.001m 1.65 5m 1.65 5.001m 2 6m 2)",
        "BCLIP ADC_CLIP 0 V=limit(V(ADC_IN),-1.65,1.65)",
        "BCODE ADC_CODE 0 V=limit(floor((V(ADC_CLIP)+1.65)/3.3*4095),0,4095)",
        "BSIGNED ADC_SIGNED 0 V=V(ADC_CODE)-2048",
        ".tran 0 6m 0 1u",
        ".options plotwinsize=0",
        ".save V(ADC_IN) V(ADC_CLIP) V(ADC_CODE) V(ADC_SIGNED)",
        ".end",
    ])


def main() -> None:
    rows = []
    # XMODEL 50 us input-update contract.
    cases = {
        "nominal": (lambda t,p:p, lambda t,p:np.zeros_like(t)),
        "dc_p10m": (lambda t,p:p+0.010, lambda t,p:np.zeros_like(t)),
        "dc_p50m": (lambda t,p:p+0.050, lambda t,p:np.zeros_like(t)),
        "dc_p100m": (lambda t,p:p+0.100, lambda t,p:np.zeros_like(t)),
        "dc_p200m": (lambda t,p:p+0.200, lambda t,p:np.zeros_like(t)),
        "dc_m200m": (lambda t,p:p-0.200, lambda t,p:np.zeros_like(t)),
        "bw_0p1hz_1m": (lambda t,p:p+0.001*np.sin(2*np.pi*.1*t), lambda t,p:np.zeros_like(t)),
        "bw_0p2hz_2m": (lambda t,p:p+0.002*np.sin(2*np.pi*.2*t), lambda t,p:np.zeros_like(t)),
        "pli60": (lambda t,p:p+0.501*np.sin(2*np.pi*60*t), lambda t,p:0.5*np.sin(2*np.pi*60*t)),
        "pli50": (lambda t,p:p+0.501*np.sin(2*np.pi*50*t), lambda t,p:0.5*np.sin(2*np.pi*50*t)),
    }
    for name, (pf, nf) in cases.items():
        zoh_pwl(DIR/f"drive_{name}.txt", 5.001, pf, nf)
        transient_deck(f"xma_{name}", f"drive_{name}_pos.txt", f"drive_{name}_neg.txt")
        note = "OUT_OF_TARGET_DIAGNOSTIC; 50Hz uses the same CM/differential amplitude as fixed 60Hz PLI" if name == "pli50" else "50us ZOH input update; 1ms aperture"
        rows.append([name,"LTSPICE_OWNED","EXECUTED_OR_READY",f"schematics/xmodel_aligned/xma_{name}.cir",COMMIT,note])
    transient_deck("xma_nominal_short", "drive_nominal_pos.txt", "drive_nominal_neg.txt", duration=.02)
    convergence_deck()
    adc_mapping_deck()
    # Full 10 s graphical schematic is the final nominal deck.
    rows.append(["nominal_10s_graphical","LTSPICE_OWNED","EXECUTED_OR_READY","schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc",COMMIT,"10s patient; final vector source"])
    ac_deck("xma_ac_nominal")
    ac_deck("xma_notch_fine", fine=True)
    for label, mm in (("0",0.0),("0p1pct",.001),("0p5pct",.005),("1pct",.01)):
        ac_deck(f"xma_mm_{label}_cmrr", mm=mm, cmrr=True)
        ac_deck(f"xma_mm_{label}_notch", mm=mm, fine=True)
        transient_deck(f"xma_mm_{label}_pli60", "drive_pli60_pos.txt", "drive_pli60_neg.txt", mm=mm)
        rows.append([f"mm_{label}","LTSPICE_OWNED","EXECUTED_OR_READY",f"schematics/xmodel_aligned/xma_mm_{label}_pli60.cir",COMMIT,"IA/Twin-T fixed-XMODEL worst-direction mismatch"])
    for label, gbw in (("100k","100k"),("500k","500k"),("1m","1Meg"),("5m","5Meg")):
        transient_deck(f"xma_gbw_{label}", "drive_nominal_pos.txt", "drive_nominal_neg.txt", gbw=gbw)
        rows.append([f"gbw_{label}","LTSPICE_OWNED","EXECUTED_OR_READY",f"schematics/xmodel_aligned/xma_gbw_{label}.cir",COMMIT,"ecg_afe_xmodel_op.sv GBW parameter"])
    for label, vos in (("0p5m","0.0005"),("1m","0.001"),("2m","0.002")):
        transient_deck(f"xma_vos_{label}", "drive_nominal_pos.txt", "drive_nominal_neg.txt", vos=vos)
        rows.append([f"vos_{label}","LTSPICE_OWNED","EXECUTED_OR_READY",f"schematics/xmodel_aligned/xma_vos_{label}.cir",COMMIT,"U1=+VOS; U2=-VOS"])
    rows.extend([
        ["adc_white_noise","XMODEL_OWNED","XMODEL_OWNED","",COMMIT,"Not duplicated in LTspice final gate"],
        ["sample_jitter","XMODEL_OWNED","XMODEL_OWNED","",COMMIT,"Not duplicated in LTspice final gate"],
        ["30min_locked_regression","XMODEL_RTL_OWNED","XMODEL_OWNED","",COMMIT,"Use locked XMODEL/RTL flow"],
        ["final_pred_final_mem","LOCKED_RTL_FPGA_OWNED","XMODEL_OWNED","",COMMIT,"Outside LTspice analog scope"],
    ])
    with TABLE.open("w", newline="", encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["case_id","owner","execution_status","source_schematic","source_commit","notes"]); w.writerows(rows)
    print(f"Generated XMODEL-aligned decks in {DIR}")


if __name__ == "__main__":
    main()
