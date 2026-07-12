# 통합 보고서 개정 감사 기록

## 상태와 기준

- 개정 상태: `COMPLETE`
- 작업 branch: `main`
- 작업 시작 기준: `f756bcf84dd6f15476bf347b2791a3ba9a64e6f5` (`origin/main`과 일치 확인)
- 고정 upstream: MATLAB `907f7e1f081a9d6a5703a32095d962143315a192`, XMODEL `4756a5086023547328ef44fd5fd87da3c250dc39`, digital `c6b80de19cdcad5b7e43fe7835588b629d847f75`

## 이번 개정 범위

기존 9장 연구 흐름과 디지털 RTL 설명의 깊이를 유지하면서 관련 연구를 거시적 연구 질문 중심으로 정리하고, digital `main`의 완료된 NO_BOARD accelerator-benefit benchmark를 제6.1절과 source-of-truth에 반영하였다. 분류기와 RTL authority는 `c6b80de...`로 유지하고 benchmark evidence commit `09e4d840...`을 별도 provenance로 등록하였다.

| 항목 | 개정 결과 |
|---|---:|
| 본문 장 | 9 |
| 본문 문자 수 | 62,448 |
| 생성 SVG | 15 |
| 상속 MATLAB PNG | 7 |
| 본문 참조 그림 | 16 |
| Evidence map 행 | 66 |
| Claim registry 행 | 47 |
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
- 사건 구동형을 “파형이 기준보다 크게 변한 순간을 사건으로 만들어 처리하는 방식”으로 풀고, Bauer의 이상 구간 알림과 본 연구의 기록 단위 네 클래스 판정을 거시적으로 구분하였다.
- Chen의 LC-ADC+SCNN은 변화 순간을 이용하지만 최종 질문이 개별 심박의 N·SVEB·VEB·F 분류임을 분명히 하였다.
- Shanmugam의 약 48시간 ECG multiple instance learning이 높은 위험 인스턴스 20%를 환자 단위 이진 예후로 집계한다는 점을 확인하였다.
- Zihlmann의 가변 길이 네 클래스 ECG 분류가 CNN 특징을 평균 또는 양방향 LSTM으로 통합하므로, “4개 클래스” 자체를 차별성으로 주장하지 않았다.
- DeepHHF를 24시간 ECG→30초 구간→구간별 요약→Transformer→5년 HF 위험으로 풀어 설명하고, 본 연구와 장시간 구간 통합 흐름이 가장 유사함을 명시하였다.
- DeepHHF는 미래 심부전 위험을, 본 연구는 현재 기록의 NSR·CHF·ARR·AFF 클래스를 묻는다는 목적 차이를 주 비교축으로 두었다.
- 비교표는 정확도나 미시적 구현 차이 대신 각 연구가 최종적으로 답하는 질문을 비교한다. 최초성은 검토한 여섯 대표 연구 범위의 제한된 문장으로만 표현한다.

## 그림과 원본 회로도 경계

고정 MATLAB component의 일곱 그림은 내용이나 픽셀을 다시 만들지 않고 `figures/final/MAT-01`~`MAT-07`로 그대로 상속하였다. 보고서 그림 7은 캐시된 이전 Figure와 구분되도록 `FIG-15_analog_signal_flow_nonideal_models.svg`를 직접 참조한다. ECG+·ECG−의 두 HPF 경로가 IA에서 합류하고 비이상성 주입은 점선 경로로 분리되도록 구성하였다. 상단 비이상성 블록은 `Input Disturbance Injection`, `R/C Tolerance & Op-Amp Error Model`, `ADC Error Model`로 통일하고 하단 한 줄 범례에서 실선과 점선의 의미를 정의하였다. `FIG-12_digital_signal_flow.svg`는 Strong-Event와 QRS LIF의 feature 출력을 별도 선으로 유지하고, rhythm·morphology 경로를 `Feature Accumulation & Class Scoring`에서 합친 뒤 30개 Snapshot을 30분 Final Membrane으로 누적하도록 수정하였다.

고정 component에는 README에서 언급한 LTspice `.asc` 또는 원본 회로 캡처가 존재하지 않았다. 따라서 analog signal flow와 본문 caption에서 원본 schematic이 아님을 명시했고, 누락 항목을 `source_of_truth/unresolved_artifacts.csv`의 `UNRES-001`로 기록하였다. Physical PCB, fabricated silicon, post-layout 또는 실제 전극 검증 claim은 추가하지 않았다.

## 가속기 Benchmark 반입 내용

- 원천은 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 `main` commit `09e4d840827ad20856f5e23be4743ddd01565e30`으로 고정하였다.
- 대표 CPU 기준선은 hand-written single-thread transaction-level Exact C++로 두고 Python cycle model과 Verilator simulation runtime은 speedup 기준선에서 제외하였다.
- Exact C++ timing 전 pred 36/36, membrane 144/144, Snapshot 1,080/1,080과 post-benchmark equivalence를 확인하였다.
- Exact C++ kernel 1,777.699800 ms, end-to-end 2,007.549250 ms와 cycle-derived FPGA core 54.012600 ms를 반영하였다.
- 같은 저장 데이터 kernel 범위의 처리시간 비율 32.912687배를 `speedup estimate`로 제한하고 measured board speedup으로 표현하지 않았다.
- 0.099 W와 0.005347247400 J/decision은 estimated/derived로, physical board timing·power·energy는 `PENDING_BOARD`로 분리하였다.

## 유지한 결과와 경계

- 24시간 Holter형 관찰은 설계 동기이고, MIT-BIH Arrhythmia의 30분 excerpt를 포함한 서로 다른 길이의 공개 원천을 같은 실제 시간으로 비교하기 위해 현재 공통 창을 30분으로 고정했음을 명시
- 30분 prototype을 임상적 24시간 Holter와 동등하거나 이를 대체하는 결과로 해석하지 않으며, 24시간 확장 시 Final Membrane 누적 폭·문턱값·간헐 사건 영향을 재검증
- 최종 30분 구간 29/36=80.56%, record-majority 16/19=84.21%
- Pure RTL 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns
- AFE 입력 SHA256, canonical AFE→RTL pred/mem, FPGA pred/mem의 각 36/36 범위
- Database–class confounding, physical/clinical/ASIC 한계
- Accelerator benchmark는 digital `main` commit `09e4d840827ad20856f5e23be4743ddd01565e30`에서 반입
- Exact C++ kernel 1,777.699800 ms, cycle-derived FPGA core 54.012600 ms, 처리시간 비율 32.912687배
- 32.912687배는 measured board speedup이 아니며 live 판정은 여전히 30분 관찰 필요
- 0.099 W와 0.005347247400 J/decision은 estimated/derived; physical board timing·power·energy는 `PENDING_BOARD`

## Vivado 물리 구현 그림 보강

- Vivado 2020.2와 `xc7a100tcsg324-1`에서 기존 BD/IP/constraints/run strategy로 MicroBlaze 통합 구현을 재생성했다.
- 잘린 저해상도 Device View 캡처와 자동 GUI 캡처 도구를 제거한 뒤, 사용자가 Vivado `Open Implemented Design → Device`에서 확보한 전체 Device View를 원본으로 고정했다.
- 고정 routed checkpoint에서 accelerator, MicroBlaze, local memory, sample feeder, AXI·UART·interrupt hierarchy의 placed primitive 좌표를 다시 추출하고 원본 Device View와 정합해 reader-facing Figure를 생성했다.
- IP Integrator Block Design은 `write_bd_layout`, worst setup Schematic은 `write_schematic`의 Vivado native PDF/SVG로 다시 export했다.
- 최악 setup path의 startpoint, endpoint, path delay 9.810 ns, requirement 10.000 ns, slack 0.097 ns를 원본 report와 함께 기록했다.
- pure RTL 9,719 LUT/5,038 FF/0 BRAM/0 DSP/WNS 8.184 ns와 MicroBlaze system 12,494 LUT/8,494 FF/16 BRAM/3 DSP/WNS 0.097 ns를 서로 다른 구현 범위로 유지했다.
- 승인된 reader-facing Figure는 실제 Device View, `SNN accelerator에 속한 배치 셀만 분리 표시`, hierarchy 범례와 자원·timing 요약을 한 페이지에 결합한다. 기존 3페이지 vector package는 보조 evidence로 유지한다.

## 전체 연구·검증 workflow 정리

- 전체 workflow는 공개 ECG 직후 Record-wise Train·Validation·Locked Test 분할을 표시하고, Train·Validation만 MATLAB과 사전 잠금 설계·검증 단계에 들어가도록 정리하였다.
- XMODEL과 Digital SNN RTL은 병렬로 분기한다. AFE–RTL 통합 검증은 두 경로를 함께 받고, Accelerator Benchmark와 FPGA Implementation & Board Replay는 Digital RTL에서만 분기한다.
- 세 검증 결과는 하나의 설계·통합 판단 마름모로 모인다. 불충족 시 MATLAB이 아니라 XMODEL·RTL 수정 단계로 돌아가며, 충족 시 Design Lock을 거쳐 격리된 Locked Test를 최초 1회만 사용한다.
- final-test 재튜닝 금지, physical AFE, 24시간 성능과 clinical validation 경계는 본문과 caption에 유지하였다.

## 최종 자동 검증

- `tools/generate_integrated_figures.py`: PASS — 22개 생성, FIG-P05를 포함해 23개 index
- `tools/check_integrated_technical_report.py`: PASS — 704 rules, 0 conflicts, chars 64,969, figures 19, evidence rows 68
- `tools/check_integrated_repository.py`: PASS — 294 rules, 0 conflicts
- CSV parsing/required columns: PASS
- `git diff --check`: commit 직전 재검증
