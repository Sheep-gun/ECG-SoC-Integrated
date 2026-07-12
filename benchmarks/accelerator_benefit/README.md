# 통합 가속기 Benchmark 근거

이 디렉터리는 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 benchmark 완료 커밋 `09e4d840827ad20856f5e23be4743ddd01565e30`에서 최종 보고서에 필요한 근거만 선별해 가져온 snapshot이다. 분류 모델·RTL·최종 시험 결과의 정본은 계속 `c6b80de19cdcad5b7e43fe7835588b629d847f75`이며, benchmark 커밋은 그 고정 설계를 변경하지 않고 실행 성능을 측정한 후속 근거다.

## 보고 가능한 핵심 결과

- Exact C++ 단일 스레드 kernel 중앙값: `1777.699800 ms`
- Exact C++ end-to-end 중앙값: `2007.549250 ms`
- Pure RTL 저장 데이터 처리 지연시간: `54.012600 ms` (`5,401,260 cycles`, `100 MHz`, cycle-derived)
- Pure RTL 처리량: `33,325,557.369947 samples/s`
- 1 kSPS 입력 대비 처리 여유: `33,325.557370×`
- Exact C++ 대 FPGA-core 처리시간 비율: `32.912687×` 추정
- Vivado 추정 전력: `0.099 W`
- 추정 에너지: `0.005347247400 J/decision`

## 반드시 함께 읽을 경계

- `32.912687×`는 측정한 Exact C++ kernel과 cycle-derived FPGA accelerator-core 지연시간을 결합한 비교다. 보드에서 측정한 speedup이 아니다.
- `54.012600 ms`는 메모리에 저장된 30분 ECG를 가속기 코어가 처리하는 active compute time이다. 실제 ECG가 들어오는 live 환경에서는 최종 판정까지 30분 관찰이 필요하다.
- host 전송, MicroBlaze, UART와 board system 지연시간은 포함하지 않는다.
- `0.099 W`는 Vivado 추정값이고 물리 보드 전력 측정값이 아니다.
- 물리 보드 지연시간·전력·에너지는 `PENDING_BOARD`다.
- Python cycle model의 2,288.745397×는 느린 검증 모델과의 비교이므로 대표 CPU 가속비로 사용하지 않는다.
- Verilator host runtime은 RTL simulation 시간이며 native CPU inference 기준선이 아니다.

## 선별 근거

- `reports/ACCELERATOR_BENEFIT_KR.md`
- `reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md`
- `reports/BENCHMARK_LIMITATIONS.md`
- `results/integrated_benchmark_summary.csv`
- `results/cpu_fpga_comparison.csv`
- `results/rtl_cycle_summary.json`
- `results/power_energy_summary.csv`
- `results/post_benchmark_equivalence.json`

전체 실행 코드·원시 720-run 결과·보드 실행 준비 패키지는 원본 저장소의 지정 커밋이 정본이다. 통합 저장소는 대회 보고서에 직접 연결되는 결과와 claim 경계만 보존한다.
