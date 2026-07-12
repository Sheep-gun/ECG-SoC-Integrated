# 통합 보고서 개정 감사 기록

## 상태와 기준

- 개정 상태: `COMPLETE`
- 작업 branch: `main`
- 작업 시작 기준: `caefc8a77fe9b0ed3eda7d810c6442842755f815` (`origin/main`과 일치 확인)
- 고정 upstream: MATLAB `907f7e1f081a9d6a5703a32095d962143315a192`, XMODEL `4756a5086023547328ef44fd5fd87da3c250dc39`, digital `c6b80de19cdcad5b7e43fe7835588b629d847f75`

## 이번 개정 범위

기존 7장 구조와 디지털 RTL 설명의 깊이는 유지하였다. 제4장을 `AFE·ADC 설계`, `MATLAB/XMODEL 검증`, `RTL/IP/FPGA 구현과 End-to-end 검증`으로 재편하고, 앞단 회로를 디지털 설명과 같은 수준으로 확장하였다.

| 항목 | 개정 결과 |
|---|---:|
| 본문 장 | 7 |
| 본문 문자 수 | 50,110 |
| 생성 SVG | 15 |
| 상속 MATLAB PNG | 7 |
| 본문 참조 그림 | 16 |
| Evidence map 행 | 53 |
| Claim registry 행 | 34 |
| Unresolved artifact | 1 |

## AFE·ADC 보강 내용

- ECG→HPF→3-op-amp IA→active Twin-T 60 Hz notch와 buffer→150 Hz LPF→12-bit ADC→offset-binary→signed two's-complement stream을 하나의 신호 흐름으로 설명하였다.
- HPF, IA, notch, LPF와 ADC마다 `왜 필요한가→어떻게 구성했는가→어떤 값인가→무엇을 검증했는가→다음 블록과 어떻게 연결되는가` 순서를 적용하였다.
- IA 수렴 문제, notch 출력 loading, LPF cutoff 수정, CMRR margin, ADC log off-by-one과 passive→active notch 변경을 설계 수정 이력으로 반영하였다.
- MATLAB의 공칭 필터·이득·동적 범위·기준 벡터와 XMODEL의 간섭·mismatch·GBW/VOS·ADC stress·장시간 stream 역할을 분리하였다.
- 주파수응답, 60 Hz notch, headroom, ADC 코드 분포, PLI, R/C mismatch, ADC 비이상성과 SHA256 인계 결과에 직접 evidence path를 연결하였다.

## 그림과 원본 회로도 경계

고정 MATLAB component의 일곱 그림은 내용이나 픽셀을 다시 만들지 않고 `figures/final/MAT-01`~`MAT-07`로 그대로 상속하였다. 추가한 `FIG-15_afe_adc_reconstructed_diagram.svg`는 MATLAB 파라미터 문서와 XMODEL RTL로 재구성한 설명용 블록도다.

고정 component에는 README에서 언급한 LTspice `.asc` 또는 원본 회로 캡처가 존재하지 않았다. 따라서 FIG-15와 본문 caption에서 원본 schematic이 아님을 명시했고, 누락 항목을 `source_of_truth/unresolved_artifacts.csv`의 `UNRES-001`로 기록하였다. Physical PCB, fabricated silicon, post-layout 또는 실제 전극 검증 claim은 추가하지 않았다.

## 유지한 결과와 경계

- 최종 30분 구간 29/36=80.56%, record-majority 16/19=84.21%
- Pure RTL 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns
- AFE 입력 SHA256, canonical AFE→RTL pred/mem, FPGA pred/mem의 각 36/36 범위
- Database–class confounding, physical/clinical/ASIC 한계
- Accelerator benchmark `PENDING_EXTERNAL_BENCHMARK_IMPORT`; 수치 미인용

## 최종 자동 검증

- `tools/generate_integrated_figures.py`: PASS — 15 SVG + 상속 MATLAB PNG 7개
- `tools/check_integrated_technical_report.py`: PASS — 494 rules, 0 conflicts, chars 50,110, figures 16, evidence rows 53
- `tools/check_integrated_repository.py`: PASS — 227 rules, 0 conflicts
- CSV parsing/required columns: PASS
- `git diff --check`: commit 직전 재검증
