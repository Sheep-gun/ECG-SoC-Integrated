#!/usr/bin/env python3
# AFE 충실도 (올바른 signed 해석):
#  AFE 출력(offset-binary, code-2048=signed) vs 원본 .mem(2의보수 signed) 상관도.
#  + 클리핑/동적범위 점검. 디지털 인터페이스 호환(offset→signed 변환 후) 검증.
import os
BASE = os.path.join(os.path.dirname(__file__), "..")
W = os.path.join(BASE, "sim_out", "multiclass")
DATA = os.path.join(BASE, "data")
VALID = 2000

def load_adc_signed(p):
    out = {}
    for line in open(p):
        if line.startswith("#"): continue
        a = line.split()
        if len(a) >= 2:
            out[int(a[0])] = int(a[1]) - 2048      # offset-binary → signed
    return out

def load_mem_signed(p, n=10000):
    v = []
    for i, line in enumerate(open(p)):
        if i >= n: break
        line = line.strip()
        if line:
            x = int(line, 16); v.append(x if x < 2048 else x - 4096)
    return v

def corr(a, b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    da=(sum((x-ma)**2 for x in a))**0.5; db=(sum((y-mb)**2 for y in b))**0.5
    return num/(da*db) if da*db else 0

print(f"{'CLS':4} {'상관도(signed,지연보정)':>20} {'지연ms':>6} {'AFE signed범위':>16} {'클리핑':>6}")
for cls in ["NSR","ARR","AFF","CHF"]:
    adc = load_adc_signed(os.path.join(W, f"adc_{cls}.txt"))
    mem = load_mem_signed(os.path.join(DATA, f"mem_{cls}.mem"))
    idxs = sorted(i for i in adc if VALID <= i < 9900)
    afe = [adc[i] for i in idxs]
    clip = sum(1 for c in afe if c <= -2047 or c >= 2046)
    best,blag=-2,0
    for lag in range(0,60):
        ref=[mem[i+lag] for i in idxs if i+lag < len(mem)]
        c=corr(afe[:len(ref)], ref)
        if c>best: best,blag=c,lag
    print(f"{cls:4} {best:20.3f} {blag:6d} {min(afe):+5d}~{max(afe):<+5d} {clip:6d}")
print("\n상관도~1.0: AFE가 각 클래스 ECG를 충실 재현. offset→signed(−2048) 변환 시 디지털과 직접 호환.")
