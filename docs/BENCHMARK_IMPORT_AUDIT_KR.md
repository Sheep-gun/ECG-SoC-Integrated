# 가속기 Benchmark 반입 감사

## 원천

- 저장소: `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier`
- 원격 branch: `codex/accelerator-benefit-benchmark`
- 반입 commit: `46f90224fca0dea3a592049a5e14b97680d529e0`
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
| Pure RTL no-stall | 54.012600 ms | DERIVED from canonical cycles |
| FPGA board core counter | 187,144.750920 ms | MEASURED |
| FPGA board system counter | 187,144.750920 ms | MEASURED |

Measured CPU / measured board 비율은 core/system 모두 0.009499063×다. 1보다 작으므로
가속이 아니며, 역수로는 board counter interval이 Exact C++보다 105.273540배 길다.
고정 XSA에는 독립 AXI Timer가 없고, 230400-baud UART-paced input wait가 계측 interval의
약 99.98%를 차지한다. 기존 32.912687×는 measured CPU / cycle-derived 54.012600 ms의
별도 no-stall 추정치이며 measured-board speedup으로 승격하지 않는다.

## 전력과 에너지

- Pure RTL: 0.099 W, ESTIMATED
- MicroBlaze integrated system: 0.271 W, ESTIMATED
- Pure RTL energy: 18.527330341 J/decision, DERIVED
- Integrated-system energy: 50.716227499 J/decision, DERIVED
- Physical board input power/energy: NOT_MEASURED

두 power는 Vivado 2020.2, `xc7a100tcsg324-1`, SAIF/VCD 없는 Medium-confidence
post-implementation vectorless estimate다. Pure RTL과 MicroBlaze/BRAM/AXI/UART/feeder를
포함한 integrated-system scope를 섞지 않는다.

## 선별 반입 파일

통합 저장소에는 aggregate report, summary CSV/JSON과 source CSV가 있는 figure만 보존한다.
원본 UART transcript와 Vivado `.rpt`는 upstream commit에서 SHA-256과 함께 추적한다.
