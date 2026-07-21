# 통합 가속기 Benchmark 근거

이 디렉터리는 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 실보드·Vivado 검증 commit
`95d7966c32ec0bad7af2dca4aa23e7e638a9103a`에서 보고서에 필요한 정제 결과만 반입한
snapshot이다. 고정 모델·RTL·36개 입력은 변경하지 않았다. raw firmware/schema의 legacy
label은 `AFF`지만 통합 보고서의 의료 표기는 `AF`로 통일한다.

## 핵심 결과

| 항목 | 결과 | 분류 |
|---|---:|---|
| 분류 정확도 | 29/36 (80.56%) | MEASURED |
| 보드–Golden final prediction | 36/36 | MEASURED |
| 보드–Golden Final Membrane | 144/144 | MEASURED |
| FPGA active-core latency | 3,601,290 cycles, 36.012900 ms | DERIVED from two MEASURED counters |
| Active-core throughput / 1 kSPS margin | 49,982,089.751172 samples/s / 49,982.089751× | DERIVED |
| Exact C++ 대비 active-core speedup | 49.362861641× | DERIVED |
| UART-paced raw interval median | 187,144.750920 ms | MEASURED transport diagnostic |
| Integrated-system compute latency/speedup | 미측정 | preload와 독립 timer 필요 |
| Pure RTL power | 0.099 W | ESTIMATED, Vivado post-implementation vectorless |
| MicroBlaze integrated-system power | 0.271 W | ESTIMATED, Vivado post-implementation vectorless |
| Pure RTL active energy | 0.003565277100 J/decision | DERIVED |
| Integrated-system energy | 미측정 | 유효한 system compute latency 없음 |
| Physical board input power | 미측정 | 외부 전력계 없음 |

active-core cycles는 `profile_total - profile_input_wait`다. input-wait counter는 RUN 상태에서
core가 ready이지만 `sample_valid`가 없을 때만 증가하므로, 이 차이는 UART/MicroBlaze 입력
starvation만 제거하고 내부 stall, Snapshot/final-decision 처리와 1,320 control cycles를 유지한다.
36개 실보드 case와 canonical XSim이 모두 3,601,290 cycles로 일치했다. 기존
54.012600 ms/32.912687×는 canonical sample gap을 포함하므로 active-core 성능으로 사용하지
않는다. Live ECG 최종 판정에는 여전히 30분 관찰 창이 필요하다.

두 전력값은 Vivado 2020.2, `xc7a100tcsg324-1`, SAIF/VCD 없는 Medium-confidence
**Post-implementation vectorless Vivado power estimate**다. Pure RTL과 MicroBlaze
통합 system의 범위를 섞지 않는다. 통합 compute latency와 energy는 ECG 사전 적재와 독립
timer가 없어 산출하지 않았고, 물리 보드 전력이나 실측 에너지로 표현하지 않는다.

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
