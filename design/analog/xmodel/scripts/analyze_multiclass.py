#!/usr/bin/env python3
# 클래스별 AFE ADC 출력 분석: 동적범위·클리핑 + R-peak/RR 통계(클래스 특징)
import os, statistics
W = os.path.join(os.path.dirname(__file__), "..", "sim_out", "multiclass")
VALID = 2000      # t>=2s (HPF 정착 후)
REFRACT = 200     # R-peak 최소 간격 200ms(200샘플)
print(f"{'CLS':4} {'코드범위':>12} {'span':>5} {'clip':>5} {'beats':>6} {'RR평균(ms)':>10} {'RR표준편차':>10} {'RR_CV%':>7}")
for cls in ["NSR", "ARR", "AFF", "CHF"]:
    p = os.path.join(W, f"adc_{cls}.txt")
    if not os.path.exists(p):
        print(f"{cls}: 파일 없음"); continue
    idx, code = [], []
    for line in open(p):
        if line.startswith("#"): continue
        a = line.split()
        if len(a) >= 2:
            idx.append(int(a[0])); code.append(int(a[1]))
    v = [(i, c) for i, c in zip(idx, code) if i >= VALID]
    cs = [c for _, c in v]
    if not cs:
        print(f"{cls}: 유효샘플 없음"); continue
    mn, mx = min(cs), max(cs)
    clip = sum(1 for c in cs if c <= 1 or c >= 4094)
    mean = sum(cs) / len(cs)
    th = mean + 0.35 * (mx - mean)        # 적응형 R-peak 임계
    # R-peak 검출 (불응기 적용)
    peaks = []
    last = -REFRACT
    for i, c in v:
        if c > th and (i - last) >= REFRACT:
            peaks.append(i); last = i
    rr = [(peaks[k+1]-peaks[k]) for k in range(len(peaks)-1)]   # ms (1샘플=1ms)
    if len(rr) >= 2:
        rmean = statistics.mean(rr); rstd = statistics.pstdev(rr)
        cv = 100.0 * rstd / rmean if rmean else 0
        print(f"{cls:4} {mn:5d}~{mx:<5d} {mx-mn:5d} {clip:5d} {len(peaks):6d} {rmean:10.1f} {rstd:10.1f} {cv:7.1f}")
    else:
        print(f"{cls:4} {mn:5d}~{mx:<5d} {mx-mn:5d} {clip:5d} {len(peaks):6d}   (RR 산출 불가)")
print("\n해석: NSR/CHF=규칙적(낮은 CV), AFF=불규칙(높은 CV), ARR=중간/이상박동")
