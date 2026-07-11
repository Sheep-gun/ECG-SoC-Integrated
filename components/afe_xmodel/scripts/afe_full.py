#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# full WFDB record -> 1kSPS(linear) -> AFE+ADC (vectorized lfilter) -> unsigned 12-bit stream.
#  xmodelmatch와 동일 AFE: /200000 -> HPF(0.482) -> x201 -> notch(60,Q5) -> LPF(150) -> ADC.
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import numpy as np, math
import wfdb
from scipy.signal import lfilter

FS = 1000.0
SCALE = 1.0 / 200000.0
GAIN = 201.0
_a_hp = math.exp(-2 * math.pi * 0.482 / FS)
_a_lp = 1 - math.exp(-2 * math.pi * 150.0 / FS)
_QN = 5.0
_w0 = 2 * math.pi * 60 / FS
_cw = math.cos(_w0); _al = math.sin(_w0) / (2 * _QN)
_b0 = 1 / (1 + _al); _b1 = -2 * _cw / (1 + _al); _b2 = 1 / (1 + _al)
_a1 = -2 * _cw / (1 + _al); _a2 = (1 - _al) / (1 + _al)

# lfilter 계수
_HPF_B = [_a_hp, -_a_hp]; _HPF_A = [1.0, -_a_hp]
_NOTCH_B = [_b0, _b1, _b2]; _NOTCH_A = [1.0, _a1, _a2]
_LPF_B = [_a_lp]; _LPF_A = [1.0, -(1 - _a_lp)]


def afe_adc_unsigned(codes):
    """codes: 1D float array (pre-AFE signed code stream @1kSPS) -> unsigned 12-bit ADC array."""
    x = np.asarray(codes, dtype=np.float64) * SCALE
    h = lfilter(_HPF_B, _HPF_A, x)
    g = h * GAIN
    z = lfilter(_NOTCH_B, _NOTCH_A, g)
    lp = lfilter(_LPF_B, _LPF_A, z)
    q = np.trunc((lp + 1.65) / 3.3 * 4095.0)
    return np.clip(q, 0, 4095).astype(np.int32)


def read_record_1ksps(rec_path):
    """WFDB record -> ch0(ECG1) digital, linear-resampled to 1kSPS (float array)."""
    r = wfdb.rdrecord(rec_path, physical=False)
    fs = float(r.fs)
    sig = r.d_signal[:, 0].astype(np.float64)
    n_out = int(len(sig) / fs * 1000.0)
    t_old = np.arange(len(sig)) / fs
    t_new = np.arange(n_out) / 1000.0
    return np.interp(t_new, t_old, sig), fs, len(sig)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, _ROOT + "/scripts")
    from afe_emu import afe_adc_unsigned as afe_slow, read_mem_signed

    REC = "/mnt/c/Users/USER/Downloads/handoff_to_suhwan/handoff_to_suhwan/selected_records/NSR/16265/16265"
    XM = _ROOT + "/datasets/afe_output_xmodelmatch/train/unsigned/0000_NSR_16265_60s_1640000ms.mem"
    START_S = 1640.0

    x1k, fs, nsrc = read_record_1ksps(REC)
    print(f"record: fs={fs} src_n={nsrc} dur_h={nsrc/fs/3600:.2f} -> 1kSPS n={len(x1k)} ({len(x1k)/1000/3600:.2f} h)")

    # (A) fast lfilter AFE vs slow pure-python AFE, on a median-centered 60s segment
    i0 = int(round(START_S * 1000)); seg = x1k[i0:i0 + 60000].copy(); seg -= np.median(seg)
    seg_c = np.clip(np.round(seg), -2048, 2047)
    fast = afe_adc_unsigned(seg_c)
    slow = np.array(afe_slow([int(v) for v in seg_c]))
    d1 = fast - slow
    print(f"[A] fast vs slow AFE (60s seg): RMS={np.sqrt(np.mean(d1.astype(float)**2)):.3f} maxabs={int(np.abs(d1).max())}")

    # (B) full-stream AFE (no per-seg centering) sliced vs xmodelmatch segment, skip 2s settling
    u_full = afe_adc_unsigned(x1k)              # full-record AFE+ADC unsigned
    seg_full = u_full[i0:i0 + 60000]
    ref = np.array([int(l.strip(), 16) for l in open(XM) if l.strip()])  # xmodelmatch unsigned 0..4095
    skip = 2000
    n = min(len(seg_full), len(ref))
    d2 = seg_full[skip:n] - ref[skip:n]
    print(f"[B] full-AFE slice vs xmodelmatch (skip2s): RMS={np.sqrt(np.mean(d2.astype(float)**2)):.2f} maxabs={int(np.abs(d2).max())} exact={100*np.mean(d2==0):.1f}%")
    print(f"    full-AFE seg range[{int(seg_full.min())},{int(seg_full.max())}] ref range[{int(ref.min())},{int(ref.max())}]")
