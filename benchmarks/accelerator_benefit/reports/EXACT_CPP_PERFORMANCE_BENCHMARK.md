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

## FPGA-core 비교

- accepted samples: 1,800,000
- canonical `sample_gap_cycles`: 2
- profile total cycles: 5,401,260
- implemented clock: 100 MHz
- cycle-derived accelerator-core latency: 54.012600 ms

`1777.699800 ms / 54.012600 ms = 32.912687×`

따라서 이 값의 보고 가능한 명칭은 **single-thread Exact C++ versus cycle-derived FPGA-core speedup estimate**다. 실제 보드에서 측정한 speedup이나 전체 system speedup이 아니다.

## 후속 실보드 결과와 남은 범위

- Nexys A7-100T core/system hardware-counter 중앙값: `187144.750920 ms`, MEASURED
- Exact C++ 대비 measured-board ratio: `0.009499063×`, DERIVED; 가속이 아님
- counter interval에는 약 99.98%의 UART-paced input wait가 포함됨
- 고정 XSA에 독립 AXI Timer가 없어 core와 system counter가 36개 모두 동일함
- host wall-clock transfer latency: 별도 측정하지 않음
- physical board input power/energy: 외부 전력계가 없어 `NOT_MEASURED`
- Pure RTL/system `0.099/0.271 W`: Vivado post-implementation vectorless `ESTIMATED`
