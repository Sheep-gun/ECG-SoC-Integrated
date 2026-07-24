#!/usr/bin/env python3
"""Build the graphical ±1.65 V LTspice schematic aligned to fixed XMODEL."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "schematics" / "nominal" / "FULL_AFE_ADC_SH_validated.asc"
OUT = ROOT / "schematics" / "xmodel_aligned"
OUT.mkdir(parents=True, exist_ok=True)

MODEL = """* Fixed-XMODEL-aligned op-amp abstraction.
* Source contract: commit 4756a5086023547328ef44fd5fd87da3c250dc39
* Aol=100 dB, CMRR=110 dB, Rout=1 ohm, rails supplied at +/-1.65 V.
* GBW_HZ=1e9 and VOS=0 reproduce ecg_afe_xmodel_op nominal settings.
.subckt XOPAMP_XMODEL INP INN VCC VEE OUT params: AOL_DB=100 CMRR_DB=110 GBW_HZ=1e9 VOS=0
.param A_OL={10**(AOL_DB/20)} CMRR_LIN={10**(CMRR_DB/20)}
.param A_CM={A_OL/(2*CMRR_LIN)} FP={GBW_HZ/A_OL} RP=1k
BERR OSUM 0 V={A_OL*(V(INP)-V(INN)+VOS)+A_CM*(V(INP)+V(INN))}
RPOLE OSUM OPOLE {RP}
CPOLE OPOLE 0 {1/(2*pi*FP*RP)}
BRAIL OINT 0 V=limit(V(OPOLE),V(VEE),V(VCC))
ROUT OINT OUT 1
.ends XOPAMP_XMODEL
"""

SYMBOL = """Version 4
SymbolType CELL
LINE Normal -32 -32 32 0
LINE Normal -32 32 32 0
LINE Normal -32 -32 -32 32
LINE Normal -28 -16 -20 -16
LINE Normal -28 16 -20 16
LINE Normal -24 20 -24 12
LINE Normal 0 -32 0 -16
LINE Normal 0 32 0 16
LINE Normal 4 -20 12 -20
LINE Normal 8 -24 8 -16
LINE Normal 4 20 12 20
WINDOW 0 16 -32 Left 2
WINDOW 3 16 32 Left 2
SYMATTR Prefix X
SYMATTR Value XOPAMP_XMODEL
SYMATTR Description Fixed-XMODEL-aligned op-amp: 100dB Aol, 110dB CMRR, 1ohm Rout, explicit rails.
PIN -32 16 NONE 0
PINATTR PinName In+
PINATTR SpiceOrder 1
PIN -32 -16 NONE 0
PINATTR PinName In-
PINATTR SpiceOrder 2
PIN 0 -32 NONE 0
PINATTR PinName V+
PINATTR SpiceOrder 3
PIN 0 32 NONE 0
PINATTR PinName V-
PINATTR SpiceOrder 4
PIN 32 0 NONE 0
PINATTR PinName OUT
PINATTR SpiceOrder 5
"""


def write_xmodel_drive() -> None:
    source = np.loadtxt(ROOT.parent / "patient100_ecg_10s.txt")
    times, volts = source[:, 0], source[:, 1]
    steps: list[tuple[float, float]] = [(0.0, 0.0), (49.999e-6, 0.0)]
    prev = 0.0
    for t, v in zip(times, volts):
        # TB reads the PWL value at t and applies it at the next 50 us update.
        effective = max(50e-6, math.ceil((float(t) + 1e-12) / 50e-6) * 50e-6)
        if effective > 10.001:
            break
        if abs(float(v) - prev) > 0:
            before = max(0.0, effective - 1e-9)
            if before > steps[-1][0]:
                steps.append((before, prev))
            steps.append((effective, float(v)))
            prev = float(v)
    steps.append((10.001, prev))
    with (OUT / "patient100_xmodel_drive_10s.txt").open("w", encoding="ascii", newline="\n") as f:
        for t, v in steps:
            f.write(f"{t:.9f} {v:.12g}\n")


def transform_asc() -> str:
    s = SRC.read_text(encoding="utf-8")
    s = s.replace("WIRE 480 352 480 240\n", "")
    s = s.replace("WIRE 480 352 336 352\n", "WIRE 480 352 336 352\nWIRE 480 496 480 352\nWIRE 160 496 480 496\n")
    s = s.replace("FLAG 480 368 INN_RAW\n", "FLAG 480 368 INN_RAW\nFLAG 480 240 0\nFLAG 160 576 0\nFLAG 1152 576 VMINUS\n")
    s = s.replace("SYMBOL OpAmps\\UniversalOpAmp2", "SYMBOL XOpAmp_XMODEL")
    for u, vos in (("U1", "+VOS"), ("U2", "-VOS"), ("U3", "0"), ("U4", "0"), ("U5", "0"), ("U6", "0")):
        s = s.replace(f"SYMATTR InstName {u}\n", f"SYMATTR InstName {u}\nSYMATTR SpiceLine PARAMS: AOL_DB={{AOL_DB}} CMRR_DB={{CMRR_DB}} GBW_HZ={{GBW_HZ}} VOS={{{vos}}}\n")
    s = s.replace("SYMATTR InstName V1\nSYMATTR Value 5", "SYMATTR InstName V1\nSYMATTR Value 1.65")
    s = s.replace("SYMATTR InstName V2\nSYMATTR Value -5", "SYMATTR InstName V2\nSYMATTR Value -1.65")
    s = s.replace("PWL file=patient100_ecg_10s.txt", "PWL file=patient100_xmodel_drive_10s.txt")
    s = s.replace("PULSE(0 5 0 1u 1u 100u 1m)", "PULSE(0 5 900u 1u 1u 98u 1m)")
    s = s.replace("TEXT 256 632 Left 2 !.tran 0 10 0 5u", "TEXT 256 632 Left 2 !.tran 0 10.001 0 5u")
    s = s.replace("TEXT 256 776 Left 2 ;VALIDATION COPY: VPLUS separated from K_DIV; source ASC preserved.",
                  "TEXT 256 776 Left 2 ;XMODEL-ALIGNED: +/-1.65V, dedicated 100dB/110dB/1ohm op-amp, ECG+=patient, ECG-=0, aperture=1ms.")
    s = s.replace("TEXT 3968 832 Left 2 !.model SW_ADC SW(Ron=1 Roff=1G Vt=2.5 Vh=0.1)",
                  "TEXT 3968 832 Left 2 !.model SW_ADC SW(Ron=1 Roff=1G Vt=2.5 Vh=0.1)\nTEXT 3968 880 Left 2 !.include XOpAmp_XMODEL.lib\nTEXT -88 560 Left 2 !.param AOL_DB=100 CMRR_DB=110 GBW_HZ=1e9 VOS=0")
    s = s.replace("TEXT 256 728 Left 2 !.save ", "TEXT 256 728 Left 2 !.save V(VPLUS) V(VMINUS) ")
    insert = """SYMBOL voltage 160 480 R0
WINDOW 123 0 0 Left 0
WINDOW 39 0 0 Left 0
SYMATTR InstName V5
SYMATTR Value 0
"""
    s = s.replace("SYMBOL cap 624 32 R90\n", insert + "SYMBOL cap 624 32 R90\n")
    return s


def main() -> None:
    (OUT / "XOpAmp_XMODEL.lib").write_text(MODEL, encoding="ascii", newline="\n")
    (OUT / "XOpAmp_XMODEL.asy").write_text(SYMBOL, encoding="ascii", newline="\n")
    write_xmodel_drive()
    (OUT / "FULL_AFE_ADC_SH_xmodel_aligned.asc").write_text(transform_asc(), encoding="utf-8", newline="\n")
    print(OUT / "FULL_AFE_ADC_SH_xmodel_aligned.asc")


if __name__ == "__main__":
    main()
