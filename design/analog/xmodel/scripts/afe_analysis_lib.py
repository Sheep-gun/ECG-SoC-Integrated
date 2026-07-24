#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AFE stress 검증 공용 라이브러리 (afe_emu.py 계수와 동일 체인, numpy 벡터화)
#   - afe_float(codes): 원본 signed .mem code -> AFE 아날로그 출력(양자화 직전 V)
#   - quantize(v, off, gain, noise, jitter): ADC non-ideal 주입 -> unsigned code[0..4095]
#   - detect_rpeaks(sig): QRS 강조 후 R-peak 인덱스
#   - match_peaks(ref, test): 참조 peak 대비 매칭/누락/timing shift
import numpy as np
import math

fs = 1000.0
SCALE = 1.0 / 200000.0
GAIN = 201.0
a_hp = math.exp(-2 * math.pi * 0.482 / fs)
a_lp = 1 - math.exp(-2 * math.pi * 150.0 / fs)
QN = 5.0
w0 = 2 * math.pi * 60 / fs
cw = math.cos(w0); al = math.sin(w0) / (2 * QN)
b0 = 1 / (1 + al); b1 = -2 * cw / (1 + al); b2 = 1 / (1 + al)
a1 = -2 * cw / (1 + al); a2 = (1 - al) / (1 + al)

VREF = 1.65          # ±1.65 V
LSB = 3.3 / 4095.0   # 1 LSB (V)

def sgn12(v):
    return v - 4096 if v > 2047 else v

def read_mem_signed(path, n=None):
    r = []
    with open(path) as f:
        for i, l in enumerate(f):
            if n is not None and i >= n:
                break
            l = l.strip()
            if l:
                r.append(sgn12(int(l, 16)))
    return np.asarray(r, dtype=np.float64)

def afe_float(codes):
    """원본 code(signed) -> AFE 출력 아날로그 전압 V (ADC 양자화 직전)."""
    x = np.asarray(codes, float) * SCALE
    h = np.zeros_like(x)
    for n in range(1, len(x)):
        h[n] = a_hp * (h[n - 1] + x[n] - x[n - 1])   # HPF 0.482Hz
    g = h * GAIN                                       # IA x201
    z = np.zeros_like(g)                               # 60Hz notch
    if len(g) > 0: z[0] = g[0]
    if len(g) > 1: z[1] = g[1]
    for n in range(2, len(g)):
        z[n] = b0 * g[n] + b1 * g[n - 1] + b2 * g[n - 2] - a1 * z[n - 1] - a2 * z[n - 2]
    lp = np.zeros_like(z)                               # LPF 150Hz
    if len(z) > 0: lp[0] = z[0]
    for n in range(1, len(z)):
        lp[n] = lp[n - 1] + a_lp * (z[n] - lp[n - 1])
    return lp

def quantize(v, off_lsb=0.0, gain_err=0.0, noise_lsb=0.0, jitter_us=0.0, rng=None):
    """AFE 아날로그 전압 v -> ADC unsigned code[0..4095], non-ideal 주입.
       off_lsb: 오프셋(LSB), gain_err: 이득오차(비율, 0.01=1%),
       noise_lsb: 부가잡음 rms(LSB), jitter_us: 표본화 지터 rms(µs)."""
    v = np.asarray(v, float)
    if jitter_us and jitter_us > 0:
        if rng is None: rng = np.random.default_rng(0)
        dt = rng.normal(0, jitter_us * 1e-6 * fs, size=len(v))   # 샘플 단위 지터
        idx = np.arange(len(v)) + dt
        v = np.interp(idx, np.arange(len(v)), v)                  # 지터 시점 재표본
    vg = v * (1.0 + gain_err)
    code = ((vg + VREF) / 3.3) * 4095.0 + off_lsb
    if noise_lsb and noise_lsb > 0:
        if rng is None: rng = np.random.default_rng(0)
        code = code + rng.normal(0, noise_lsb, size=len(code))
    code = np.floor(code).astype(np.int64)
    return np.clip(code, 0, 4095)

# ---- R-peak 검출 (QRS 대역강조 + 적응 임계) ----
from scipy.signal import butter, filtfilt, find_peaks

_bp_b, _bp_a = butter(2, [8.0 / (fs / 2), 20.0 / (fs / 2)], btype="band")

def detect_rpeaks(sig):
    x = np.asarray(sig, float)
    x = x - np.median(x)
    if len(x) < 50 or np.allclose(x, 0):
        return np.array([], dtype=int)
    y = filtfilt(_bp_b, _bp_a, x)     # 8-20Hz QRS 강조 (zero-phase)
    e = y * y                          # 에너지
    thr = 0.15 * np.max(e) if np.max(e) > 0 else 0
    pk, _ = find_peaks(e, height=thr, distance=int(0.3 * fs))  # 최소 RR 300ms
    return pk

def match_peaks(ref, test, tol_ms=60):
    """ref 각 peak에 대해 test에서 ±tol 내 최근접 매칭. return (shifts_ms, n_match, n_miss)."""
    tol = tol_ms
    shifts = []; miss = 0
    tj = np.asarray(test)
    for r in ref:
        if len(tj) == 0:
            miss += 1; continue
        j = int(np.argmin(np.abs(tj - r)))
        d = tj[j] - r
        if abs(d) <= tol:
            shifts.append(float(d))   # ms (1샘플=1ms)
        else:
            miss += 1
    return np.asarray(shifts), len(shifts), miss

def rr_intervals(peaks):
    return np.diff(np.asarray(peaks, float)) if len(peaks) > 1 else np.array([])
