#!/usr/bin/env python3
# 원인 격리: .mem(signed)에 AFE 등가 디지털 필터만 적용 → 어떤 필터가 ARR 플립을 유발하는지.
#  mode=lpf  : 150Hz 1차 LPF만 (대역제한)
#  mode=full : HPF(0.48Hz) + 60Hz 노치(Q5) + LPF(150Hz)  (AFE 필터 체인 등가)
#  출력: mem_<cls>_<mode>.mem  (12-bit 2의보수 hex), digref로 분류 확인.
import os, math, sys
DATA=os.path.join(os.path.dirname(__file__),"..","data")
mode=sys.argv[1] if len(sys.argv)>1 else "lpf"
QN=float(sys.argv[2]) if len(sys.argv)>2 else 5.0   # 노치 Q (기본 5)
SUF=sys.argv[3] if len(sys.argv)>3 else mode         # 출력 접미사
fs=1000.0
# 1차 LPF 150Hz
a_lp=1-math.exp(-2*math.pi*150/fs)
# 1차 HPF 0.48Hz
a_hp=math.exp(-2*math.pi*0.48/fs)
# 60Hz 노치 biquad (Q=5)
w0=2*math.pi*60/fs; cw=math.cos(w0); al=math.sin(w0)/(2*QN)
b0=1/ (1+al); b1=-2*cw/(1+al); b2=1/(1+al); a1=-2*cw/(1+al); a2=(1-al)/(1+al)
def sgn(v): return v if v<2048 else v-4096
def to12(v):
    v=int(round(v))
    if v>2047: v=2047
    if v<-2048: v=-2048
    return v & 0xFFF
for cls in ["NSR","CHF","ARR","AFF"]:
    x=[sgn(int(l.strip(),16)) for i,l in enumerate(open(os.path.join(DATA,f"mem_{cls}.mem"))) if l.strip()]
    y=list(x)
    do_hpf   = mode in ("hpf","hpflpf","full")
    do_notch = mode in ("notch","full")
    do_lpf   = mode in ("lpf","hpflpf","full")
    if do_hpf:
        h=[0.0]*len(y)
        for n in range(1,len(y)): h[n]=a_hp*(h[n-1]+y[n]-y[n-1])
        y=h
    if do_notch:
        z=[0.0]*len(y)
        for n in range(2,len(y)): z[n]=b0*y[n]+b1*y[n-1]+b2*y[n-2]-a1*z[n-1]-a2*z[n-2]
        y=z
    if do_lpf:
        lp=[0.0]*len(y); lp[0]=y[0]
        for n in range(1,len(y)): lp[n]=lp[n-1]+a_lp*(y[n]-lp[n-1])
        y=lp
    out=os.path.join(DATA,f"mem_{cls}_{SUF}.mem")
    with open(out,"w") as o:
        for v in y: o.write(f"{to12(v):03x}\n")
    print(f"{cls}_{mode}: {out}")
