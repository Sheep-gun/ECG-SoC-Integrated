# SNN ECG FPGA 실보드 성능 및 Vivado 전력 보고서

모든 표의 수치는 `MEASURED`, `ESTIMATED`, `DERIVED` 중 하나로 구분한다. raw firmware/schema의 legacy label `AFF`는 유지하며, 본 보고서의 의료 표기는 `AF`를 사용한다.

| 항목 | 결과 | 근거/분류 |
|---|---:|---|
| 분류 정확도 | 29/36, 80.56% | final-test annotation, MEASURED |
| 보드-Golden final_pred | 36/36 | UART board replay, MEASURED |
| 보드-Golden Final Membrane | 144/144 | UART board replay, MEASURED |
| FPGA core active latency median / mean / range | 36.012900 / 36.012900 / 36.012900-36.012900 ms | 두 hardware counter의 차, DERIVED |
| FPGA core active cycles | 3601290 cycles, 36/36 동일 | `profile_total - profile_input_wait`, DERIVED from MEASURED counters |
| FPGA core throughput / 1 kSPS margin | 49982089.751172 samples/s / 49982.089751x | DERIVED |
| Exact C++ 대비 core speedup | 49.362861641x | CPU MEASURED / FPGA counter-derived, DERIVED |
| UART-paced raw interval median | 187144.750920 ms | transport diagnostic, MEASURED |
| Integrated-system compute latency/speedup | 미측정 | DDR 사전 적재와 독립 timer 필요 |
| Pure RTL 1 MHz power | 0.099000 W | 저속 구성 Vivado post-implementation vectorless, ESTIMATED; energy 미산출 |
| Pure RTL 100 MHz accelerator+static / hierarchy dynamic / static power | 0.149500 / 0.052500 / 0.097000 W | real-ECG SAIF, ESTIMATED |
| Integrated FPGA system power | 0.271000 W | Vivado post-implementation vectorless, ESTIMATED |
| Pure RTL 100 MHz total energy/decision | 0.005383928550 J | clock-matched estimated total power x counter-derived latency, DERIVED ESTIMATE |
| Pure RTL 100 MHz active dynamic energy/decision | 0.001890677250 J | clock-matched estimated dynamic power x counter-derived latency, DERIVED ESTIMATE |
| Integrated system energy/decision | 미측정 | 유효한 integrated compute latency 없음 |
| Board physical power | 미측정 | 외부 전력계 없음 |

보드는 Nexys A7-100T, UART `COM8`/230400 baud였다. 코어 성능은 `profile_total_cycles - profile_input_wait_cycles`로 산출했다. 두 피연산자는 모두 실보드 100 MHz hardware counter에서 MEASURED 되었고, latency·throughput·speedup은 그 차로부터 DERIVED 되었다. RTL에서 input-wait counter는 RUN 상태에서 코어가 입력을 받을 준비가 되었지만 `sample_valid`가 없을 때만 증가한다. 따라서 이 계산은 UART/MicroBlaze 입력 starvation만 제거하며 내부 back-pressure, snapshot/final-decision 처리와 1320 control cycles를 유지한다.

36개 보드 case의 UART-paced raw interval은 서로 달랐지만 active-cycle 차는 모두 정확히 3601290 cycles였다. canonical XSim에서도 `5,401,260 - 1,799,970 = 3,601,290 cycles`로 동일해 36/36 교차 검증되었다. 과거 54.0126 ms와 32.912687x는 canonical sample gap을 포함한 값이므로 no-stall 코어 성능으로 사용하지 않는다. 현재 코어 결과는 36.012900 ms 및 49.362861641x다.

원시 `core_cycles/system_cycles` 구간은 입력 대기를 포함하므로 UART-paced transport diagnostic으로만 보존한다. 이를 integrated-system 속도나 energy로 사용하지 않는다. 진짜 통합 시스템 계측에는 ECG를 DDR2 등에 먼저 적재하고 독립 AXI Timer로 feeder 시작부터 최종 decision까지 측정해야 한다.

기존 0.099000 W는 `CORE_DIV_HALF=50`과 `core_clk_1mhz`를 사용한 1 MHz Pure RTL 저속 구성의 유효한 전력 추정치로 보존한다. 하지만 100 MHz active latency와 결합하지 않는다. 새 성능 대응 Pure RTL top은 분주기나 generated core clock 없이 가속기를 직접 100 MHz로 구동하며, route WNS 0.035 ns로 timing을 통과했다. 이 구성의 자원은 9759 LUT/5049 FF/0 BRAM/0 DSP다. 종전 mixed-clock energy 계산은 최종 성능값에서 철회했다. Integrated system은 MicroBlaze, BRAM, AXI, UART, sample feeder와 accelerator를 모두 포함하므로 Pure RTL 값과 섞지 않는다.

1 MHz Pure RTL과 통합 MicroBlaze 범위는 vectorless 추정으로 남는다. 보고 가능한 100 MHz 가속기 값은 네 class의 실제 ECG burst SAIF 중앙값이며, routed-net match는 약 12%라서 미매칭 net에는 vectorless propagation이 적용되고 confidence는 `Medium`이다. literal 1 kS/s trace는 별도로 보고한다. 물리 보드 입력 전력과 가속기 실측 에너지는 측정하지 않았다.
