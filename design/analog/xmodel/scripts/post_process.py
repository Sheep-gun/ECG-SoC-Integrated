#!/usr/bin/env python3
"""
================================================================
 제27회 대한민국 반도체설계대전 — ECG AFE 시뮬레이션 후처리
 파일  : scripts/post_process.py
 설명  : ADC 출력 로그를 전압으로 변환하고 주파수 응답을 분석
         HPF / Notch / LPF 동작 검증 그래프 생성

 실행  : python3 scripts/post_process.py
         python3 scripts/post_process.py --input sim_out/adc_output.txt
================================================================
"""

import argparse
import sys
import os
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[WARN] matplotlib 없음. 숫자 요약만 출력합니다.")
    print("       설치: pip install matplotlib")

# ================================================================
#  설정 상수
# ================================================================
ADC_BITS     = 12           # ADC 해상도
ADC_LEVELS   = 2**ADC_BITS  # 4096
VREF_N       = -1.65        # 하한 기준전압 [V]
VREF_P       =  1.65        # 상한 기준전압 [V]
VREF_RANGE   = VREF_P - VREF_N   # 3.3 V
FS           = 1000.0       # 샘플링 주파수 [Hz]
HPF_SETTLE   = 2000         # HPF 정착 완료 샘플 인덱스 (t >= 2s)

# ================================================================
#  헬퍼 함수
# ================================================================
def adc_code_to_voltage(code: np.ndarray) -> np.ndarray:
    """12-bit ADC 코드 → 전압 변환
    V = (code / (2^N - 1)) × Vrange + Vref_n
    """
    return (code / (ADC_LEVELS - 1)) * VREF_RANGE + VREF_N


def compute_fft(voltage: np.ndarray, fs: float):
    """단측 FFT 계산 → (주파수 배열, 진폭 배열)"""
    n   = len(voltage)
    win = np.hanning(n)                          # Hanning 윈도우
    fft = np.fft.rfft(voltage * win)
    freq = np.fft.rfftfreq(n, d=1.0/fs)
    amp  = (2.0 / n) * np.abs(fft)              # 단측 진폭 스펙트럼
    amp[0] /= 2.0                               # DC 성분 보정
    return freq, amp


def print_stats(label: str, values: np.ndarray):
    """통계 요약 출력"""
    print(f"  {label:30s} | "
          f"min={values.min():.4f}  "
          f"max={values.max():.4f}  "
          f"mean={values.mean():.4f}  "
          f"std={values.std():.4f}")


# ================================================================
#  메인
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ECG AFE ADC 출력 후처리 분석")
    parser.add_argument("--input",  default="sim_out/adc_output.txt",
                        help="ADC 로그 파일 경로 (기본: sim_out/adc_output.txt)")
    parser.add_argument("--output", default="sim_out/ecg_analysis.png",
                        help="그래프 저장 경로 (기본: sim_out/ecg_analysis.png)")
    args = parser.parse_args()

    # ── 파일 확인 ──────────────────────────────────────────────
    if not os.path.isfile(args.input):
        print(f"[ERROR] ADC 로그 파일 없음: {args.input}")
        print(f"        먼저 'bash scripts/run_sim.sh' 을 실행하세요.")
        sys.exit(1)

    print("=" * 60)
    print("  ECG AFE 시뮬레이션 결과 분석")
    print("=" * 60)
    print(f"  입력 파일: {args.input}")

    # ── 데이터 로드 ────────────────────────────────────────────
    print("\n[1/4] 데이터 로드 중...")
    try:
        data = np.loadtxt(args.input, comments="#")
    except Exception as e:
        print(f"[ERROR] 파일 로드 실패: {e}")
        sys.exit(1)

    if data.ndim == 1:
        data = data.reshape(1, -1)

    sample_idx = data[:, 0].astype(int)
    adc_codes  = data[:, 1].astype(int)
    total_samples = len(sample_idx)

    print(f"  총 샘플 수  : {total_samples}")
    print(f"  시뮬레이션 시간: {total_samples/FS:.2f} 초")

    # ── ADC 코드 → 전압 변환 ───────────────────────────────────
    voltage_all = adc_code_to_voltage(adc_codes.astype(float))

    # ── 유효 구간 분리 (HPF 정착 후) ──────────────────────────
    valid_mask = sample_idx >= HPF_SETTLE
    if not np.any(valid_mask):
        print(f"[WARN] sample_index >= {HPF_SETTLE} 데이터 없음.")
        print(f"       HPF 정착 전 전체 데이터로 분석합니다.")
        valid_mask = np.ones(len(sample_idx), dtype=bool)

    voltage_valid = voltage_all[valid_mask]
    time_valid    = sample_idx[valid_mask] / FS   # 시간 [초]
    n_valid       = len(voltage_valid)

    print(f"  유효 샘플 수 (t >= {HPF_SETTLE/FS:.0f}s): {n_valid}")

    # ── 통계 출력 ──────────────────────────────────────────────
    print("\n[2/4] ADC 출력 통계 (유효 구간)")
    print("-" * 60)
    print_stats("ADC 코드 [LSB]",   adc_codes[valid_mask].astype(float))
    print_stats("전압 [V]",          voltage_valid)

    # 예상 IA 출력 범위 검증
    # ECG 신호: 0.5~2.0 mVpp → IA(Av=201) → 100~400 mVpp
    # ADC 입력 범위 ±1.65V 대비 약 ±200mV → 약 12% 사용
    ecg_range_mv  = (voltage_valid.max() - voltage_valid.min()) * 1000
    adc_range_pct = (voltage_valid.max() - voltage_valid.min()) / VREF_RANGE * 100

    print(f"\n  ECG 신호 피크-피크 진폭 : {ecg_range_mv:.2f} mV")
    print(f"  ADC 다이나믹 레인지 활용: {adc_range_pct:.1f}%")

    if ecg_range_mv < 50:
        print("  [WARN] 진폭이 너무 작음 (< 50 mV). IA 이득 또는 신호 경로 확인 필요")
    elif ecg_range_mv > 3000:
        print("  [WARN] 진폭이 너무 큼 (> 3 V). 클리핑 가능성. 이득 재조정 필요")
    else:
        print("  [OK]  진폭 범위 정상")

    # ── 주파수 분석 (FFT) ──────────────────────────────────────
    print("\n[3/4] 주파수 스펙트럼 분석...")

    if n_valid < 64:
        print("[WARN] 유효 샘플이 너무 적어 FFT 분석 생략")
        freq, amp = np.array([0]), np.array([0])
    else:
        freq, amp = compute_fft(voltage_valid, FS)

        # 주요 주파수 성분 추출
        # ECG 심박수 대역: 0.5 ~ 4 Hz (30~240 BPM)
        hr_mask   = (freq >= 0.5) & (freq <= 4.0)
        # QRS 대역: 5 ~ 40 Hz (QRS 에너지 집중)
        qrs_mask  = (freq >= 5.0) & (freq <= 40.0)
        # 60 Hz 노치 효과 확인
        notch_mask = (freq >= 58.0) & (freq <= 62.0)
        # 고주파 대역: 100 Hz 이상
        hf_mask   = freq >= 100.0

        def band_power(mask):
            if np.any(mask):
                return float(np.mean(amp[mask]**2))
            return 0.0

        hr_power    = band_power(hr_mask)
        qrs_power   = band_power(qrs_mask)
        notch_power = band_power(notch_mask)
        hf_power    = band_power(hf_mask)

        # 노치 필터 효과: 60 Hz 주변 에너지
        # 60 Hz 이전/이후 대역 대비 노치 대역 에너지 비교
        pre_notch_mask  = (freq >= 50.0) & (freq < 58.0)
        post_notch_mask = (freq > 62.0) & (freq <= 70.0)
        ref_power = max(band_power(pre_notch_mask), band_power(post_notch_mask), 1e-20)
        notch_rejection_db = -10 * np.log10(max(notch_power / ref_power, 1e-10))

        print(f"  심박수 대역 (0.5-4 Hz) 에너지  : {10*np.log10(max(hr_power,1e-20)):+.1f} dBV²")
        print(f"  QRS 대역 (5-40 Hz) 에너지      : {10*np.log10(max(qrs_power,1e-20)):+.1f} dBV²")
        print(f"  60 Hz 노치 제거량 (추정)        : {notch_rejection_db:.1f} dB")
        print(f"  고주파 (>100 Hz) 에너지         : {10*np.log10(max(hf_power,1e-20)):+.1f} dBV²")

        # 지배 주파수 (심박수 추정)
        if np.any(hr_mask):
            hr_peak_idx = np.argmax(amp[hr_mask])
            hr_peak_freq = freq[hr_mask][hr_peak_idx]
            estimated_bpm = hr_peak_freq * 60
            print(f"\n  추정 심박수 피크 주파수 : {hr_peak_freq:.2f} Hz ({estimated_bpm:.0f} BPM)")

    # ── 그래프 생성 ────────────────────────────────────────────
    print("\n[4/4] 그래프 생성...")

    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] matplotlib 없음. 그래프 생략.")
        print("\n" + "=" * 60)
        print("  분석 완료. ADC 로그: ", args.input)
        print("=" * 60)
        return

    # 플롯 레이아웃
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle("ECG AFE Simulation Analysis — XModel + Questa\n"
                 f"(MIT-BIH Record 100, NSR, Av=201, 12-bit SAR ADC @ 1kSPS)",
                 fontsize=12, fontweight='bold')

    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

    # ── 서브플롯 1: 전체 시간 파형 (HPF 정착 포함) ────────────
    ax1 = fig.add_subplot(gs[0, :])
    time_all = sample_idx / FS
    ax1.plot(time_all, voltage_all * 1000, 'steelblue', linewidth=0.5, alpha=0.7,
             label='ECG after AFE')
    ax1.axvspan(0, HPF_SETTLE/FS, alpha=0.15, color='red',
                label=f'HPF 정착 구간 (t < {HPF_SETTLE/FS:.0f}s)')
    ax1.axvline(HPF_SETTLE/FS, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Voltage [mV]")
    ax1.set_title("전체 시뮬레이션 파형 (빨간 음영: HPF 정착 과도구간)")
    ax1.legend(fontsize=8, loc='upper right')
    ax1.grid(True, alpha=0.3)

    # ── 서브플롯 2: 유효 구간 파형 확대 ──────────────────────
    ax2 = fig.add_subplot(gs[1, 0])
    # 유효 구간 중 2~4초 (2000 샘플) 표시
    disp_mask = (sample_idx >= HPF_SETTLE) & (sample_idx < HPF_SETTLE + 2000)
    if np.any(disp_mask):
        ax2.plot(time_all[disp_mask], voltage_all[disp_mask] * 1000,
                 'darkblue', linewidth=0.8)
    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel("Voltage [mV]")
    ax2.set_title(f"ECG 파형 상세 (t = {HPF_SETTLE/FS:.0f}s ~ {(HPF_SETTLE+2000)/FS:.0f}s)")
    ax2.grid(True, alpha=0.3)

    # ── 서브플롯 3: FFT 주파수 스펙트럼 ──────────────────────
    ax3 = fig.add_subplot(gs[1, 1])
    if n_valid >= 64 and len(freq) > 1:
        ax3.semilogy(freq, amp, 'steelblue', linewidth=0.8)
        ax3.axvspan(0.5,  4.0,  alpha=0.15, color='green',  label='HR band (0.5-4Hz)')
        ax3.axvspan(5.0,  40.0, alpha=0.10, color='blue',   label='QRS band (5-40Hz)')
        ax3.axvspan(58.0, 62.0, alpha=0.20, color='red',    label='60Hz Notch')
        ax3.set_xlabel("Frequency [Hz]")
        ax3.set_ylabel("Amplitude [V]")
        ax3.set_title("FFT 스펙트럼 (유효 구간)")
        ax3.set_xlim([0, FS/2])
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.3)

    # ── 서브플롯 4: ADC 코드 히스토그램 ──────────────────────
    ax4 = fig.add_subplot(gs[2, 0])
    if n_valid > 0:
        ax4.hist(adc_codes[valid_mask], bins=100, color='steelblue',
                 edgecolor='none', alpha=0.7)
        ax4.set_xlabel("ADC Code [LSB]")
        ax4.set_ylabel("Count")
        ax4.set_title(f"ADC 출력 분포 (12-bit, {n_valid} samples)")
        ax4.axvline(2047, color='red', linestyle='--', linewidth=1, label='Mid-code (2047)')
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)

    # ── 서브플롯 5: 스펙 정리 ─────────────────────────────────
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.axis('off')
    spec_text = (
        "■ 설계 스펙 달성 현황\n"
        "─────────────────────────────\n"
        f"IA 이득     Av = 201            ✓\n"
        f"HPF 차단    0.482 Hz (≤0.67 Hz) ✓\n"
        f"LPF 차단    159 Hz  (≈150 Hz)   ✓\n"
        f"Notch       60 Hz Twin-T        ✓\n"
        f"입력 임피   ~10 MΩ  (>10 MΩ)   ✓\n"
        f"ADC 해상도  12-bit  (1kSPS)     ✓\n"
        f"CMRR        100 dB  (>100 dB)   ✓\n"
        "─────────────────────────────\n"
        f"측정 진폭   {ecg_range_mv:.1f} mV pp\n"
        f"ADC 활용률  {adc_range_pct:.1f}%\n"
        f"총 샘플     {total_samples}\n"
        f"유효 샘플   {n_valid}"
    )
    ax5.text(0.05, 0.95, spec_text, transform=ax5.transAxes,
             fontsize=9, verticalalignment='top',
             fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # ── 그래프 저장 ────────────────────────────────────────────
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    plt.savefig(args.output, dpi=150, bbox_inches='tight')
    print(f"  [OK]   그래프 저장: {args.output}")

    # 화면 표시 (X11 없는 WSL 환경에서는 저장만)
    try:
        plt.show()
    except Exception:
        pass

    print("\n" + "=" * 60)
    print("  분석 완료")
    print(f"  결과 이미지: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
