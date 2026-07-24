# 36-case compact AFE–RTL acceptance evidence

이 폴더는 고정 AFE 생성 final-test chunk와 digital board-replay input의 SHA-256 36/36 동일성, canonical `sample_gap_cycles=2`에서 Pure RTL의 class 36/36과 four Final Membrane 144/144 일치를 기록한 compact CSV 및 XSim harness를 보존한다.

## 포함 근거

- `input_sha256_36case.csv`: AFE 생성 chunk와 replay input의 byte identity
- `output_equivalence_36case.csv`: predicted class, four membranes, accepted samples, Snapshots와 decision count
- `xsim_results_36case.csv`: XSim raw summary
- `harness/`: 당시 재현에 사용한 source list, testbench와 compare script
- `LEGACY_ACCEPTANCE_REPORT_KR.md`: 원래 전달 보고서. 과거 path와 표현은 provenance를 위해 그대로 보존

## 범위

이 결과는 **고정 통합 acceptance**이며 현재 저장소에 36개 full raw XMODEL `accepted_*.mem`을 모두 포함한다는 뜻은 아니다. raw accepted dump의 현재 보존·재감사 범위는 `verification/xmodel_rtl_e2e/`에서 별도로 관리한다.

또한 36/36 equivalence는 label accuracy가 아니다. ground-truth 기준 final-test accuracy는 29/36이다.
