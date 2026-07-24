# SNN ECG 가속기 처리시간과 전력 근거

## 비교 범위

고정 Pure RTL과 동일한 정수 연산 및 판정 절차를 수행하는 단일 thread Exact C++ kernel을 기준으로 비교했다. Exact C++는 최종 클래스 36/36, 네 Final Membrane 144/144, Snapshot 경계 1,080/1,080이 RTL과 일치한 뒤 측정했다.

## 처리시간

- Exact C++ kernel 360회 측정 중앙값: 1,777.6998 ms
- FPGA 가속기 활성시간: 3,601,290 cycles @ 100 MHz = 36.0129 ms
- 동일 kernel 범위의 처리시간 비율: 49.36배

36.0129 ms는 입력 대기시간을 제외하고 저장된 1,800,000표본을 처리한 활성시간이다. 실제 1 kSPS streaming 입력은 30분을 관찰해야 하므로 최종 판정의 관찰시간이 36.0129 ms로 줄어드는 것은 아니다.

## 전력과 에너지

실제 ECG switching activity를 이용한 post-route Vivado 추정에서 Pure RTL 할당전력은 1 kSPS 연속 처리 시 142.0 mW, 100 MHz burst 시 149.5 mW다. 149.5 mW와 36.0129 ms를 곱한 판정당 활성 에너지는 5.3839 mJ다. 30분마다 한 번 burst 처리하고 나머지 시간에는 static power까지 완전히 차단한다고 가정한 이상적 평균은 2.991 µW다.

142.0 mW, 149.5 mW와 2.991 µW는 물리 보드 실측값이 아니라 post-route activity 기반 추정과 그 파생값이다. 특히 2.991 µW는 retention, isolation, wake-up, power switch와 off-state leakage를 제외한 이상적 full power-gating 조건이다.

## 근거

- `models/digital_equivalence/exact_cpp/results/exact_cpp_cpu_summary.csv`
- `models/digital_equivalence/results/board_timing_summary.json`
- `models/digital_equivalence/results/activity_power_summary.json`
- `models/digital_equivalence/results/accelerator_benefit_summary.csv`
- `models/digital_equivalence/results/power_energy_summary.csv`
