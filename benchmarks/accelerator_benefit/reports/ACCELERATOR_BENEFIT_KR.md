# SNN ECG FPGA 실보드 성능 및 Vivado 전력 보고서

모든 표의 수치는 `MEASURED`, `ESTIMATED`, `DERIVED` 중 하나로 구분한다. raw firmware/schema의 legacy label `AFF`는 유지하며, 본 보고서의 의료 표기는 `AF`를 사용한다.

| 항목 | 결과 | 근거/분류 |
|---|---:|---|
| 분류 정확도 | 29/36, 80.56% | final-test annotation, MEASURED |
| 보드-Golden final_pred | 36/36 | UART board replay, MEASURED |
| 보드-Golden Final Membrane | 144/144 | UART board replay, MEASURED |
| FPGA core latency median / mean / range | 187144.750920 / 188068.199890 / 186492.781740-191686.150980 ms | hardware cycle counter, MEASURED |
| FPGA system latency median / mean / range | 187144.750920 / 188068.199890 / 186492.781740-191686.150980 ms | transaction counter, MEASURED |
| System throughput / 1 kSPS margin | 9618.223280 samples/s / 9.618223x | DERIVED from measured cycles |
| Exact C++ 대비 core speedup | 0.009499063x | CPU MEASURED / FPGA MEASURED, DERIVED |
| Exact C++ 대비 system speedup | 0.009499063x | CPU MEASURED / FPGA MEASURED, DERIVED |
| Pure RTL power | 0.099000 W | Vivado post-implementation vectorless, ESTIMATED |
| Integrated FPGA system power | 0.271000 W | Vivado post-implementation vectorless, ESTIMATED |
| Pure RTL energy/decision | 18.527330341 J | estimated power x measured core latency, DERIVED |
| Integrated system energy/decision | 50.716227499 J | estimated power x measured system latency, DERIVED |
| Board physical power | 미측정 | 외부 전력계 없음 |

보드는 Nexys A7-100T, UART `COM8`/230400 baud였다. `core_cycles`는 accelerator last-decision counter이고 `system_cycles`는 accelerator total transaction counter다. UART 결과 출력은 counter 정지 후 수행되므로 제외된다. 고정 XSA에는 독립 AXI Timer가 없으므로 두 counter를 host wall latency로 재표기하지 않는다. 이번 workload에서는 두 counter가 동일한 값을 기록했으며, 입력 UART pacing과 accelerator input-wait가 계측 범위에 포함된다. 따라서 기존 32.912687x는 cycle-derived 54.0126 ms에 대한 추정치로만 남기고, 위 표의 실보드 speedup과 분리해 해석한다.

실보드 비율 0.009499063x는 1보다 작으므로 가속을 의미하지 않는다. 반대로 표현하면 FPGA core 계측 구간은 Exact C++ kernel보다 105.273540배 길었고 system 계측 구간은 105.273540배 길었다. 이는 accelerator 연산 자체만의 no-stall 성능이 아니라 230400-baud 입력 대기가 포함된 고정 firmware counter 범위의 실측 결과다.

Pure RTL 전력은 기존 0.099000 W를 동일 RTL/part/clock으로 재현했다. 새 route 자원은 9749 LUT/5045 FF로 과거 9719/5038와 소폭 다르며 route WNS도 새 보고서 값을 사용한다. Integrated system은 MicroBlaze, BRAM, AXI, UART, sample feeder와 accelerator를 모두 포함하므로 Pure RTL 값과 섞지 않는다.

두 전력값 모두 SAIF/VCD 없이 Vivado 기본 vectorless propagation을 사용한 **Post-implementation vectorless Vivado power estimate**다. confidence는 Pure RTL `Medium`, system `Medium`이며 clock은 각각 sys_clk_pin 100.000 MHz, core_clk_1mhz 1.000 MHz; snn_ecg_mb_full_replay_i/mdm_1/U0/Use_E2.BSCAN_I/Use_E2.BSCANE2_I/DRCK 30.000 MHz, snn_ecg_mb_full_replay_i/mdm_1/U0/Use_E2.BSCAN_I/Use_E2.BSCANE2_I/UPDATE 30.000 MHz, sys_clk_pin 100.000 MHz다. 물리 보드 입력 전력과 가속기 실측 에너지는 측정하지 않았다.
