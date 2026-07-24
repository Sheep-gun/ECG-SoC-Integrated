# Benchmark 반영 감사

최신 benchmark 근거는 디지털 저장소 commit `d44e67517650f1f95ca67b93c2788f41e99f1a5e`에서 `models/digital_equivalence/`로 선별 반영했다. 파일별 출처는 `project_registry/benchmark_import_manifest.csv`에 기록한다.

보고서에 사용하는 값은 다음과 같다.

- Exact C++ 단일 thread 중앙값: 1,777.6998 ms
- FPGA active cycles: 3,601,290 cycles @ 100 MHz
- FPGA active time: 36.0129 ms
- 동일 kernel 범위의 active-time ratio: 49.36배
- 1 kSPS 연속 처리 할당전력 추정: 142.0 mW
- 100 MHz burst 할당전력 추정: 149.5 mW
- 판정당 활성 에너지: 5.3839 mJ
- 완전 power-gating 가정의 30분 주기 평균: 2.991 µW

49.36배는 end-to-end 또는 실시간 관찰시간의 단축이 아니다. 142.0 mW와 149.5 mW는 Vivado activity 기반 할당 추정이며 보드 입력전력 실측이 아니다. 2.991 µW는 leakage, retention, isolation, wake-up과 data movement 비용을 0으로 둔 조건부 산출값이다.
