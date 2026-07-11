#!/usr/bin/env python3
# .mem(2의보수 signed 12-bit, 0중심, 1kSPS) → 아날로그 전압 PWL
#  signed_code = v<2048 ? v : v-4096 ;  voltage = signed_code/200000 (±600코드≈±3mV)
#  UP배 선형보간으로 연속 아날로그 근사(ZOH 계단 아티팩트 제거). 기본 UP=4(250µs 간격).
import os
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SECS = 60
SCALE = 1.0/200000.0
UP = 4                       # 샘플당 보간 분할수 (1=ZOH)
for cls in ["NSR", "CHF", "ARR", "AFF"]:
    src = os.path.join(DATA, f"mem_{cls}.mem")
    dst = os.path.join(DATA, f"ecg_{cls}.pwl")
    n = SECS * 1000
    vals = []
    with open(src) as f:
        for i, line in enumerate(f):
            if i >= n: break
            line = line.strip()
            if not line: continue
            v = int(line, 16); vals.append((v if v < 2048 else v - 4096) * SCALE)
    with open(dst, "w") as o:
        for i in range(len(vals)-1):
            for k in range(UP):
                t = (i + k/float(UP)) * 0.001
                v = vals[i] + (vals[i+1]-vals[i]) * (k/float(UP))   # 선형보간
                o.write(f"{t:.6f}\t{v:.8f}\n")
        o.write(f"{(len(vals)-1)*0.001:.6f}\t{vals[-1]:.8f}\n")
    print(f"{cls}: {dst} ({len(vals)} samples ×{UP} 보간, {SECS}s)")
