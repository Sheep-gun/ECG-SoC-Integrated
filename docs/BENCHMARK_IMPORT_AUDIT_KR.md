# 가속기 Benchmark 반입 감사

## 원천

- 저장소: `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier`
- 원격 branch: `codex/accelerator-benefit-benchmark`
- 반입 commit: `95d7966c32ec0bad7af2dca4aa23e7e638a9103a`
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

- Pure RTL: 0.099 W, ESTIMATED
- MicroBlaze integrated system: 0.271 W, ESTIMATED
- Pure RTL active energy: 0.003565277100 J/decision, DERIVED
- Integrated-system energy: NOT_MEASURED
- Physical board input power/energy: NOT_MEASURED

두 power는 Vivado 2020.2, `xc7a100tcsg324-1`, SAIF/VCD 없는 Medium-confidence
post-implementation vectorless estimate다. Pure RTL과 MicroBlaze/BRAM/AXI/UART/feeder를
포함한 integrated-system scope를 섞지 않는다.

## 선별 반입 파일

통합 저장소에는 aggregate report, summary CSV/JSON과 source CSV가 있는 figure만 보존한다.
원본 UART transcript와 Vivado `.rpt`는 upstream commit에서 SHA-256과 함께 추적한다.
