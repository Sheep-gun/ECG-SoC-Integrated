# 가속기 Benchmark 반입 감사

## 원천

- 저장소: `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier`
- 원격 branch: `codex/accelerator-benefit-benchmark`
- 반입 commit: `d44e67517650f1f95ca67b93c2788f41e99f1a5e`
- 고정 분류기·RTL·36-case 입력은 변경하지 않았다.
- raw/internal legacy label `AFF`는 upstream에 유지하고 report-facing 표기는 `AF`를 사용한다.

## 실보드 acceptance

- Nexys A7-100T, COM8, 230400 baud
- 36/36 completed and BOARD_PASS
- case당 1,800,000 samples, Snapshot 30회, decision 1회
- Board–Golden final prediction 36/36
- Board–Golden Final Membrane 144/144
- 분류 정확도 29/36=80.56%
- 모든 transcript에서 `BOARD_BENCH`와 PASS marker 각각 1개
- 모든 core/system cycle counter 양수

## 속도 결과

| 범위 | 중앙값 | 분류 |
|---|---:|---|
| Exact C++ kernel | 1,777.699800 ms | MEASURED |
| FPGA active-core | 36.012900 ms | DERIVED from two MEASURED board counters |
| UART-paced raw interval | 187,144.750920 ms | MEASURED diagnostic |
| Integrated-system compute | NOT_MEASURED | preload와 독립 timer 필요 |

FPGA active-core는 `profile_total-profile_input_wait=3,601,290 cycles`이며 Exact C++ 대비
49.362861641×다. input-wait counter는 RUN 상태에서 core가 ready이지만 `sample_valid`가
없을 때만 증가하므로 입력 starvation만 제외한다. 내부 stall, Snapshot/final-decision 처리와
1,320 control cycles는 유지한다. 이 차이는 보드 36/36과 XSim에서 동일하다. 기존
54.012600 ms/32.912687×는 sample gap을 포함하므로 active-core 성능으로 사용하지 않는다.

## 전력과 에너지

- Pure RTL, 1 MHz core: 0.099 W, ESTIMATED power-only operating point
- Pure RTL, direct 100 MHz core: four-class real-ECG burst SAIF accelerator+static/hierarchy dynamic/device static 0.149500/0.052500/0.097000 W, ESTIMATED
- Literal 1 kS/s 100-sample prefix: accelerator+static/hierarchy dynamic 0.142000/0.045000 W, ESTIMATED
- MicroBlaze integrated system: 0.271 W, ESTIMATED
- Pure RTL 100 MHz allocated total energy: 0.005383928550 J/decision, DERIVED_ESTIMATE
- Pure RTL 100 MHz active dynamic energy: 0.001890677250 J/decision, DERIVED_ESTIMATE
- 30분 주기 완전 power-gating 가정의 연산 코어 평균전력: 2.991071 µW, DERIVED UPPER_BOUND_ASSUMPTION
- 1 MHz 0.099 W는 100 MHz active latency와 결합하지 않음, NOT_DERIVED_CLOCK_MISMATCH
- Integrated-system energy: NOT_MEASURED
- Physical board input power/energy: NOT_MEASURED

1 MHz Pure RTL과 integrated system은 Vivado 2020.2 `xc7a100tcsg324-1`의 Medium-confidence
vectorless estimate다. 100 MHz 가속기 대표값은 실제 ECG SAIF 기반이지만 routed-net match가 약
12%라서 미매칭 net에는 vectorless propagation이 남는다. 2.991071 µW는 5.383929 mJ를 1,800초로 나눈 값으로 계산 근거는 명확하지만, 유휴 정적전력을 완전히 제거하는 가정이며 입력 메모리·상태 유지·전원 제어·기동·누설과 나머지 wearable 부품 전력을 제외한다. Pure RTL과 MicroBlaze/BRAM/AXI/UART/feeder를 포함한 integrated-system scope를 섞지 않는다. 물리 보드 rail 전력과 ASIC post-layout PPA도 별도 미측정·미완료 항목이다.

## 선별 반입 파일

통합 저장소에는 aggregate report, summary CSV/JSON, source CSV가 있는 figure와 새 100 MHz
Pure RTL build manifest 및 wrapper/XDC/Tcl을 보존한다. `source_of_truth/benchmark_import_manifest.csv`의
17개 항목 중 16개 복사본은 clean upstream checkout과 통합 파일의 SHA-256 byte identity를 검사한다.
Exact C++ 보고서 한 개는 과거 gap-inclusive 설명을 현재 measured-counter-derived active-core 결과로
정리한 `CURATED_ACTIVE_CORE_SUMMARY`이며 해당 측정 CSV/JSON 값은 별도 규칙으로 검증한다. raw
power/timing/utilization `.rpt`와 환경 파일에는 로컬 절대경로가 있어 공개 통합 저장소에 중복
반입하지 않고, 원본 저장소 commit과 `power_summary.json`/build manifest의 SHA-256으로 추적한다.
기존 UART transcript와 1 MHz/system raw report도 같은 정책으로 원본 저장소에서 보존한다.
