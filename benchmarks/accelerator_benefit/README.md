# 통합 가속기 Benchmark 근거

이 디렉터리는 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 실보드·Vivado 검증 commit
`46f90224fca0dea3a592049a5e14b97680d529e0`에서 보고서에 필요한 정제 결과만 반입한
snapshot이다. 고정 모델·RTL·36개 입력은 변경하지 않았다. raw firmware/schema의 legacy
label은 `AFF`지만 통합 보고서의 의료 표기는 `AF`로 통일한다.

## 핵심 결과

| 항목 | 결과 | 분류 |
|---|---:|---|
| 분류 정확도 | 29/36 (80.56%) | MEASURED |
| 보드–Golden final prediction | 36/36 | MEASURED |
| 보드–Golden Final Membrane | 144/144 | MEASURED |
| FPGA core/system latency median | 187,144.750920 ms | MEASURED |
| System throughput / 1 kSPS margin | 9,618.223280 samples/s / 9.618223× | DERIVED |
| Exact C++ 대비 보드 core/system 비율 | 0.009499063× | DERIVED from MEASURED latencies |
| Pure RTL power | 0.099 W | ESTIMATED, Vivado post-implementation vectorless |
| MicroBlaze integrated-system power | 0.271 W | ESTIMATED, Vivado post-implementation vectorless |
| Pure RTL / integrated energy | 18.527330341 / 50.716227499 J/decision | DERIVED |
| Physical board input power | 미측정 | 외부 전력계 없음 |

0.009499063×는 가속을 뜻하지 않는다. 역수로는 UART-paced input wait를 포함한 보드
counter interval이 Exact C++ kernel보다 105.273540배 길다. 기존 32.912687×는 measured
CPU를 no-stall cycle-derived RTL 54.012600 ms로 나눈 별도 추정치이며 실보드 속도비로
사용하지 않는다. Live ECG 최종 판정에는 여전히 30분 관찰 창이 필요하다.

두 전력값은 Vivado 2020.2, `xc7a100tcsg324-1`, SAIF/VCD 없는 Medium-confidence
**Post-implementation vectorless Vivado power estimate**다. Pure RTL과 MicroBlaze
통합 system의 범위를 섞지 않으며, 물리 보드 전력이나 실측 에너지로 표현하지 않는다.

## 정제 근거

- `reports/ACCELERATOR_BENEFIT_KR.md`
- `reports/ACCELERATOR_BENEFIT_EN.md`
- `reports/POWER_ENERGY_METHODOLOGY.md`
- `reports/BENCHMARK_LIMITATIONS.md`
- `results/integrated_benchmark_summary.csv`
- `results/board_timing_summary.json`
- `results/power_summary.json`
- `results/power_energy_summary.csv`
- `figures/01_cpu_vs_rtl_latency.png`
- `figures/02_throughput_realtime_margin.png`
- `figures/05_power_energy_status.png`

원본 UART transcript와 Vivado `.rpt`는 upstream commit에 보존되며, 이 통합 저장소에는
보고서에 필요한 aggregate와 source CSV만 반입한다.
