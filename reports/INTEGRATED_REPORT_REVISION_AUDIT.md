# 통합 보고서 개정 감사 기록

## 상태와 기준

- 개정 상태: `COMPLETE`
- 작업 branch: `main`
- 작업 시작 기준: `b0d2f203da7c2ffda9f38a08d9ff8d34e870f3c8` (`origin/main`과 일치 확인)
- 고정 upstream: MATLAB `907f7e1f081a9d6a5703a32095d962143315a192`, XMODEL `4756a5086023547328ef44fd5fd87da3c250dc39`, digital `c6b80de19cdcad5b7e43fe7835588b629d847f75`

## 이번 개정 범위

기존 9장 연구 흐름과 디지털 RTL 설명의 깊이는 유지하면서 제2.1절을 실제 선행연구 인용 기반으로 개정하였다. 개별 심박 SNN, 연속 ECG 사건 구동형 탐지, multiple instance 집계, 가변 길이 CNN/LSTM과 24시간 Holter Transformer 통합을 최종 판정 단위별로 비교하고, 본 연구의 핵심을 특정 60초·30분 숫자가 아닌 간헐적 질환 증거의 순차 포착과 고정 폭 RTL 누적으로 정의하였다.

| 항목 | 개정 결과 |
|---|---:|
| 본문 장 | 9 |
| 본문 문자 수 | 58,948 |
| 생성 SVG | 15 |
| 상속 MATLAB PNG | 7 |
| 본문 참조 그림 | 16 |
| Evidence map 행 | 61 |
| Claim registry 행 | 42 |
| 참고문헌 | 14 |
| Unresolved artifact | 1 |

## AFE·ADC 보강 내용

- ECG→HPF→3-op-amp IA→active Twin-T 60 Hz notch와 buffer→150 Hz LPF→12-bit ADC→offset-binary→signed two's-complement stream을 하나의 신호 흐름으로 설명하였다.
- HPF, IA, notch, LPF와 ADC마다 `왜 필요한가→어떻게 구성했는가→어떤 값인가→무엇을 검증했는가→다음 블록과 어떻게 연결되는가` 순서를 적용하였다.
- IA 수렴 문제, notch 출력 loading, LPF cutoff 수정, CMRR margin, ADC log off-by-one과 passive→active notch 변경을 설계 수정 이력으로 반영하였다.
- MATLAB의 공칭 필터·이득·동적 범위·기준 벡터와 XMODEL의 간섭·mismatch·GBW/VOS·ADC stress·장시간 stream 역할을 분리하였다.
- 주파수응답, 60 Hz notch, headroom, ADC 코드 분포, PLI, R/C mismatch, ADC 비이상성과 SHA256 인계 결과에 직접 evidence path를 연결하였다.

## 장시간 ECG 관련 연구 보강 내용

- Amirshahi–Hashemi의 STDP/R-STDP 논문을 R-peak 주위 개별 심박 분류로 한정하고, 진폭 스파이크 변환·STDP 특징 학습·보상/벌점 출력 학습을 원 논문에서 확인하였다.
- Bauer의 연속 사건 구동형 이상 검출과 Chen의 LC-ADC+SCNN 개별 심박 분류를 기록 단위 다중 질환 누적과 구분하였다.
- Shanmugam의 약 48시간 ECG multiple instance learning이 높은 위험 인스턴스 20%를 환자 단위 이진 예후로 집계한다는 점을 확인하였다.
- Zihlmann의 가변 길이 네 클래스 ECG 분류가 CNN 특징을 평균 또는 양방향 LSTM으로 통합하므로, “4개 클래스” 자체를 차별성으로 주장하지 않았다.
- DeepHHF의 실제 제목·저자·2026년 npj Digital Medicine 정식 출판과 DOI를 확인하고, 24시간 Holter의 30초 인코더 특징을 Transformer로 통합하는 5년 HF 위험 예후 모델로 반영하였다.
- 비교표는 정확도를 넣지 않고 판정 단위·국소 처리·장시간 집계·구현 형태를 비교한다. 최초성은 검토한 여섯 대표 연구 범위의 제한된 문장으로만 표현한다.

## 그림과 원본 회로도 경계

고정 MATLAB component의 일곱 그림은 내용이나 픽셀을 다시 만들지 않고 `figures/final/MAT-01`~`MAT-07`로 그대로 상속하였다. 추가한 `FIG-15_afe_adc_reconstructed_diagram.svg`는 MATLAB 파라미터 문서와 XMODEL RTL로 재구성한 설명용 블록도다.

고정 component에는 README에서 언급한 LTspice `.asc` 또는 원본 회로 캡처가 존재하지 않았다. 따라서 FIG-15와 본문 caption에서 원본 schematic이 아님을 명시했고, 누락 항목을 `source_of_truth/unresolved_artifacts.csv`의 `UNRES-001`로 기록하였다. Physical PCB, fabricated silicon, post-layout 또는 실제 전극 검증 claim은 추가하지 않았다.

## 유지한 결과와 경계

- 24시간 Holter형 관찰은 설계 동기이고, MIT-BIH Arrhythmia의 30분 excerpt를 포함한 서로 다른 길이의 공개 원천을 같은 실제 시간으로 비교하기 위해 현재 공통 창을 30분으로 고정했음을 명시
- 30분 prototype을 임상적 24시간 Holter와 동등하거나 이를 대체하는 결과로 해석하지 않으며, 24시간 확장 시 Final Membrane 누적 폭·문턱값·간헐 사건 영향을 재검증
- 최종 30분 구간 29/36=80.56%, record-majority 16/19=84.21%
- Pure RTL 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns
- AFE 입력 SHA256, canonical AFE→RTL pred/mem, FPGA pred/mem의 각 36/36 범위
- Database–class confounding, physical/clinical/ASIC 한계
- Accelerator benchmark `PENDING_EXTERNAL_BENCHMARK_IMPORT`; 수치 미인용

## 최종 자동 검증

- `tools/generate_integrated_figures.py`: PASS — 15 SVG + 상속 MATLAB PNG 7개
- `tools/check_integrated_technical_report.py`: PASS — 590 rules, 0 conflicts, chars 58,948, figures 16, evidence rows 61
- `tools/check_integrated_repository.py`: PASS — 237 rules, 0 conflicts
- CSV parsing/required columns: PASS
- `git diff --check`: commit 직전 재검증
