# Exact C++ 성능 Benchmark

## 등가성 gate

성능 측정 전에 다음 조건을 통과하였다.

| Gate | 결과 |
|---|---:|
| Exact C++ 최종 예측 | 36/36 |
| 네 최종 막전위 | 144/144 |
| Snapshot 경계 | 1,080/1,080 |
| 대표 accepted-sample 상태 hash | 240,000/240,000 |
| 고정 폭 primitive | 793,595 checks, 0 failure |
| module/adversarial microtrace | 18/18 |
| Debug/Release 출력 동일성 | 36/36 |
| 입력 SHA256 | 36/36 |

## 측정 조건

- 구현: hand-written transaction-level Exact C++
- 실행: single thread, fixed affinity
- build: Release, `-O3 -DNDEBUG -march=native`, trace disabled
- 입력: 36 cases × 1,800,000 samples
- 반복: case별 3 warm-up + 10 measured runs
- kernel-only: 입력 표본은 메모리에 적재된 상태에서 최종 결과까지
- end-to-end: 파일 open 직전부터 result JSON flush 완료까지

## CPU 결과

| 지표 | Kernel-only | End-to-end |
|---|---:|---:|
| 중앙값 | 1777.699800 ms | 2007.549250 ms |
| 평균 | 1782.070826 ms | 1999.155130 ms |
| 표준편차 | 79.435145 ms | 85.839932 ms |
| 중앙 처리량 | 1,012,544.413 samples/s | 896,615.633 samples/s |
| 정확한 출력 | 360/360 | 360/360 |

## FPGA active-core 비교

- accepted samples: 1,800,000
- measured board profile total/input-wait counter: case별 값은 다르지만 차는 36/36 동일
- active cycles: `profile_total - profile_input_wait = 3,601,290`
- implemented clock: 100 MHz
- hardware-counter-derived active-core latency: 36.012900 ms
- active-core throughput: 49,982,089.751172 samples/s

`1777.699800 ms / 36.012900 ms = 49.362861641×`

따라서 이 값의 보고 가능한 명칭은 **single-thread Exact C++ 대비 FPGA active-core speedup**이다. CPU 측은 MEASURED이고 FPGA 측은 두 MEASURED hardware counter의 차에서 DERIVED 되었다. RTL input-wait 정의에 의존하는 core-scope 결과이며 전체 system speedup은 아니다.

canonical `sample_gap_cycles=2`의 gap-inclusive XSim 결과 5,401,260 cycles, 54.012600 ms와 그에 따른 32.912687×는 과거 비교값으로만 보존한다. input-wait 1,799,970 cycles를 제외하면 XSim도 3,601,290 cycles로 실보드 36/36과 정확히 일치한다.

## 실보드 결과와 남은 범위

- Nexys A7-100T active-core latency: `36.012900 ms`, DERIVED from MEASURED counters
- Exact C++ 대비 active-core speedup: `49.362861641×`, DERIVED
- UART-paced raw counter 중앙값: `187144.750920 ms`, MEASURED diagnostic only
- 고정 XSA에 독립 AXI Timer와 preloaded-input 경로가 없어 integrated-system compute latency/speedup/energy는 `NOT_MEASURED`
- host wall-clock transfer latency: 별도 측정하지 않음
- physical board input power/energy: 외부 전력계가 없어 `NOT_MEASURED`
- Pure RTL 1 MHz `0.099 W` and system `0.271 W`: Vivado post-implementation vectorless `ESTIMATED`; real-ECG burst-SAIF 100 MHz accelerator+static/hierarchy dynamic/static `0.149500/0.052500/0.097000 W`: `ESTIMATED`, about 12% routed-net match
- Pure RTL 100 MHz allocated-total/active-dynamic energy `0.005383928550/0.001890677250 J/decision`: clock-matched `DERIVED_ESTIMATE`
