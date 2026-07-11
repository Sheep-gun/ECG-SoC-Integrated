#!/usr/bin/env python3
# XModel 정합 AFE+ADC 에뮬레이터 (코드도메인 python_equiv의 누락분 보정)
#  체인: in/200000(V) -> HPF(0.482Hz) -> IA x201 -> notch(60Hz Q5) -> LPF(150Hz)
#        -> ADC: code=$rtoi(((V+1.65)/3.3)*4095), clip[0,4095]  (offset-binary unsigned 12-bit)
import math

fs = 1000.0
SCALE = 1.0 / 200000.0
GAIN = 201.0
a_hp = math.exp(-2 * math.pi * 0.482 / fs)
a_lp = 1 - math.exp(-2 * math.pi * 150.0 / fs)
QN = 5.0
w0 = 2 * math.pi * 60 / fs
cw = math.cos(w0)
al = math.sin(w0) / (2 * QN)
b0 = 1 / (1 + al); b1 = -2 * cw / (1 + al); b2 = 1 / (1 + al)
a1 = -2 * cw / (1 + al); a2 = (1 - al) / (1 + al)


def sgn(v):
    return v if v < 2048 else v - 4096


def read_mem_signed(path, n=60000):
    r = []
    with open(path) as f:
        for i, l in enumerate(f):
            if i >= n:
                break
            l = l.strip()
            if l:
                r.append(sgn(int(l, 16)))
    return r


def afe_adc_unsigned(codes):
    x = [c * SCALE for c in codes]
    h = [0.0] * len(x)
    for n in range(1, len(x)):
        h[n] = a_hp * (h[n - 1] + x[n] - x[n - 1])
    g = [v * GAIN for v in h]
    z = [0.0] * len(g)
    if g:
        z[0] = g[0]
    if len(g) > 1:
        z[1] = g[1]
    for n in range(2, len(g)):
        z[n] = b0 * g[n] + b1 * g[n - 1] + b2 * g[n - 2] - a1 * z[n - 1] - a2 * z[n - 2]
    lp = [0.0] * len(z)
    if z:
        lp[0] = z[0]
    for n in range(1, len(z)):
        lp[n] = lp[n - 1] + a_lp * (z[n] - lp[n - 1])
    out = []
    for v in lp:
        q = int(((v + 1.65) / 3.3) * 4095.0)
        if q > 4095:
            q = 4095
        if q < 0:
            q = 0
        out.append(q)
    return out
