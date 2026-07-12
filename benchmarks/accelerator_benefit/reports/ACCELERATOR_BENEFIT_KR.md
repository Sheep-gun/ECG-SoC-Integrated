# SNN ECG Accelerator Benefit (KR)

## 1. 벤치마크 목적
Locked SNN ECG 4-class IP의 실행 이점을 모델 변경 없이 정량화한다.

## 2. NO_BOARD 실행 조건
물리 Nexys A7 보드는 연결되지 않았다. 보드 latency/power는 PENDING_BOARD이다.

## 3. Locked-model 보호
시작 commit과 config/RTL/dataset/BIT/XSA/ELF/transcript SHA256를 고정했다. 분류 지표 29/36 및 16/19는 변경하지 않았다.

## 4. 공통 데이터와 functional equivalence
동일한 36개 1,800,000-sample stream을 사용했다. Canonical RTL 및 기존 board replay는 final_pred/final_mem 36/36 일치한다. 이는 accuracy 100%가 아니라 기능 동등성이다.

## 5. CPU 방법
Benchmark-scoped Python 정수 clock model은 delayed valid/data staging을 locked RTL과 동일하게 복원하여 pred/mem 36/36 동등성을 통과했다. 1 process/1 thread, 3 warm-up, case당 10회 측정의 kernel per-case median 중앙값은 123621.089625 ms이며, 동일한 stored-data scope에서 RTL speedup은 2288.75×이다.

Hand-written single-thread transaction-level Exact C++는 final prediction 36/36, final membrane 144/144, Snapshot boundary 1080/1080 동등성 검증 후 측정했다. Kernel 360-run median은 1777.699800 ms이고, measured CPU와 cycle-derived FPGA core를 결합한 명시적 scope의 speedup estimate는 32.912687x이다.

Verilator-generated RTL simulation은 36/36 출력 동등성 검증 후 host runtime을 별도 측정했다. Per-case median의 중앙값은 2456.708125 ms이다. 이는 Exact C++ native CPU baseline이 아니라 RTL simulation/verification runtime이다.

## 6. RTL cycle 방법
sample_gap_cycles=2, 100 MHz, committed profile counters를 사용했다. XSim host wall-clock은 사용하지 않았다.

## 7. 기존 board 기능 증거
36 transcripts, 1,800,000 samples, 30 snapshots, 1 decision, pred/mem 36/36를 audit했다.

## 8. 향후 board timing
기존 64-bit hardware profile counter를 읽고 timing 종료 후 UART를 출력하는 instrumented source와 parser를 준비했다.

## 9. Latency 결과
저장된 30분 ECG stream의 pure RTL cycle-derived 처리 latency는 54.012600 ms이다.

## 10. Throughput
33.325557 MSamples/s, 1 kSPS 대비 33325.56× margin이다.

## 11. Real-time 해석
저장 데이터 처리 시간과 live 관찰 시간을 구분한다. Live ECG 최종 판단은 30분 observation window에 의해 제한된다.

## 12. Streaming memory
2.7 MB decimal full raw buffer를 저장하지 않는다. Pure RTL은 BRAM 0, DSP 0이다.

## 13. Resource
Pure RTL 9719 LUT/5038 FF와 MicroBlaze system 12494 LUT/8494 FF/16 BRAM/3 DSP는 scope가 다르다.

## 14. Estimated power/energy
0.099 W는 Vivado estimate이다. **Vivado-estimated power × cycle-derived stored-data processing latency**는 0.005347247400 J/decision이며 board 측정값이 아니다.

## 15. Board pending
core/system/host latency 및 physical power는 모두 PENDING_BOARD이다.

## 16. 대회 보고서용 문구
“저장된 30분 ECG stream의 accelerator processing latency는 canonical RTL cycle count와 실제 구현 clock으로부터 산출했다. Live operation의 최종 decision latency는 30분 observation window에 의해 제한된다.”

## 17. Board 확보 후 절차
`READY_FOR_BOARD_BENCHMARK.md`의 build, program, 36-case run, parser, integrity 명령을 그대로 실행한다.
