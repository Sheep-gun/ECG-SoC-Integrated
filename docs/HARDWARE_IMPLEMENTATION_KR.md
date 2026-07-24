# 하드웨어 구현, 가속 성능과 전력

## Pure RTL implementation

- Tool/device: Vivado 2020.2, Artix-7 XC7A100T
- Top: `snn_ecg_30min_final_top`
- Resources: 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP
- Post-route WNS: 8.184 ns

이 수치는 최종 고정 Pure RTL 구현 결과다. benchmark용 profiler가 추가된 build의 9,759 LUT와 5,049 FF는 cycle/power 분석 범위이며 최종 자원 수치와 혼합하지 않는다.

## MicroBlaze 통합 시스템

- 12,494 LUT, 8,494 FF, 16 BRAM, 3 DSP
- setup WNS 0.097 ns
- Nexys A7-100T
- 구성: MicroBlaze, Local Memory, AXI interconnect, Sample Feeder, SNN accelerator, AXI INTC, UARTLite

통합 시스템의 BRAM과 DSP는 processor, memory와 peripheral 자원이며 Pure RTL 분류기 자원이 아니다.

## timing bottleneck와 pipeline 최적화

초기 병목은 `class_score_neurons`의 `rdm_level_spike → pred_class` 경로였다. 약 90 logic levels와 52 CARRY4를 포함한 누산·비교·WTA 경로를 관측한 뒤 clock requirement를 완화하지 않고 구조적으로 분할했다.

주요 변경은 C24 readout과 class WTA 분리, `*_next` counter capture, event/gate/score delta 등록, RDM·RAM exact lookup, Snapshot update–adjust–commit 분리, RBBB gate 정렬, QRS MAF timestamp FIFO, PNN center 등록, Final Membrane pairwise WTA, ARR commit과 flush 정렬이다.

개발 순서는 **critical path 관측 → pipeline 분할 → timing 재검증 → Python/RTL 및 FPGA 기능 등가성 확인**이었다. 상세 commit과 RTL 근거는 `verification/timing_optimization/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md`에 있다.

최적화 전 약 17.5k LUT는 historical OOC hotspot 수치다. 최종 9,719 LUT와 보고 범위가 달라 직접 감소율로 비교하지 않는다.

## 처리시간 benchmark

| 구현 | 범위 | 시간 |
|---|---|---:|
| Exact C++ | preloaded 1,800,000 samples, single thread kernel | 1,777.6998 ms median |
| FPGA core | profile total − input wait, 100 MHz | 36.0129 ms |
| 비율 | C++ / FPGA active time | 49.36배 |

FPGA 활성시간은 3,601,290 cycles이며 36개 board case와 XSim에서 동일했다. UART-paced transaction 시간은 입력 전송 대기가 포함되므로 accelerator speedup에 사용하지 않는다.

## 전력과 에너지

| 조건 | 결과 | 근거 |
|---|---:|---|
| 1 kSPS continuous clocked allocation | 142.0 mW | post-route real-ECG activity estimate |
| 100 MHz burst allocation | 149.5 mW | activity estimate |
| 30분 판정 active energy | 5.3839 mJ | 149.5 mW × 36.0129 ms |
| ideal power-gated average | 2.991 µW | 5.3839 mJ / 1,800 s |

2.991 µW는 현재 FPGA 소비전력이나 ASIC 실측값이 아니다. off leakage, retention, isolation, wake-up, power switch와 data buffering 비용을 0으로 둔 이상적 조건이다. 보드 전체 전력은 측정하지 않았다. 산출 원본과 한계는 `models/digital_equivalence/results/`와 `models/digital_equivalence/reports/POWER_ENERGY_METHODOLOGY.md`에 있다.

## 구현하지 않은 범위

physical AFE PCB, ADC silicon, ASIC, transistor/post-layout, fabricated silicon과 clinical validation은 수행하지 않았다.
