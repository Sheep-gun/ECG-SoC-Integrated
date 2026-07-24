# 통합 저장소 감사 기록

## 목적

이 저장소는 장시간 ECG 네 클래스 분류 시스템의 공개 설계 원본, 재현 도구와
검증 근거를 한곳에 정리한 최종 작업공간이다. 대회 참가신청서의 기술설명서
본문을 현재 주장 범위의 기준으로 사용하되, 분량상 생략된 데이터 구성,
사전 특징 분석, RTL timing 병목 개선과 단계별 정합 근거를 함께 보존한다.

## 고정 설계 권한

| 구성 | 고정 commit | 보존 위치 |
|---|---|---|
| MATLAB AFE–ADC 사전 설계 | `907f7e1f081a9d6a5703a32095d962143315a192` | `design/analog/matlab/` |
| AFE–ADC XMODEL | `4756a5086023547328ef44fd5fd87da3c250dc39` | `design/analog/xmodel/` |
| Pure RTL 분류 가속기 | `c6b80de19cdcad5b7e43fe7835588b629d847f75` | `design/digital/` |
| timing pipeline 변경 이력 | `c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa`, `5e2e5d0a46be47d8086b8642e055066079bfa4e6` | `verification/timing_optimization/` |

두 번째 디지털 저장소의 commit 이력은 최종 저장소의 Git history에 병합하여
소스 이동 뒤에도 설계 계보를 추적할 수 있게 한다. 경로별 세부 권한은
`project_registry/upstream_commits.yaml`에 기록한다.

## 공개 범위

- 설계 원본: `design/`
- 기준 모델과 benchmark: `models/`
- 검증 근거: `verification/`
- 두 Vivado project: `vivado/`
- 공개 데이터 출처와 재구성 도구: `datasets/`, `tools/`
- 실제 제출 Figure: `figures/final_submission/`
- claim, 문헌과 artifact registry: `project_registry/`

PhysioNet 원시 waveform, 개인 식별정보, 서명과 제출 원본 PDF/HWP는 공개 Git에
포함하지 않는다. `project_registry/artifact_manifest.csv`는 현재 공개 작업공간의
모든 파일을 SHA-256으로 열거하며 `tools/build_artifact_manifest.py`로 재생성한다.

## 핵심 경계

- 실제 분류 검증 입력은 30분이며 24시간 이상 Holter 분석은 설계 지향점이다.
- 최종 시험 성능은 29/36, 정확도 80.56%, Macro-F1 80.44%이다.
- FPGA 36/36은 최종 클래스와 막전위의 기능 정합이며 분류 정확도 100%가 아니다.
- Pure RTL 구현은 9,719 LUT, 5,038 FF, BRAM 0, DSP 0, WNS 8.184 ns이다.
- 2.991 µW는 완전 power-gating을 가정한 산출값이며 FPGA 또는 ASIC 실측값이 아니다.
- 물리 AFE PCB, ADC silicon, ASIC post-layout와 임상 검증은 수행하지 않았다.

## 검사

`REPRODUCIBILITY_KR.md`의 명령으로 workspace, 보고서와 저장소 checker를 실행한다.
최신 결과는 `reports/clean_workspace_check.md`와
`reports/integrated_repository_check.md`에 요약한다.
