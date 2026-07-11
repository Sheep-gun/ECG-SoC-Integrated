#!/usr/bin/env python3
# .mem(2의보수 signed 12-bit hex, 1kSPS) -> analog PWL
#  convert_mem.py와 동일: voltage = signed_code/200000, UP=4 선형보간
import sys
inp, out = sys.argv[1], sys.argv[2]
secs = int(sys.argv[3]) if len(sys.argv) > 3 else 60
SCALE = 1.0 / 200000.0
UP = 4
n = secs * 1000
vals = []
with open(inp) as f:
    for i, l in enumerate(f):
        if i >= n:
            break
        l = l.strip()
        if not l:
            continue
        v = int(l, 16)
        vals.append((v if v < 2048 else v - 4096) * SCALE)
with open(out, "w") as o:
    for i in range(len(vals) - 1):
        for k in range(UP):
            t = (i + k / float(UP)) * 0.001
            v = vals[i] + (vals[i + 1] - vals[i]) * (k / float(UP))
            o.write(f"{t:.6f}\t{v:.8f}\n")
    o.write(f"{(len(vals) - 1) * 0.001:.6f}\t{vals[-1]:.8f}\n")
