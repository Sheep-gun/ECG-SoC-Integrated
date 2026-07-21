# 통합 보고서 개정 감사 기록

## 상태와 기준

- 개정 상태: `COMPLETE`
- 작업 branch: `codex/analog-validation-flow` (검증 후 `main`에 fast-forward push)
- 작업 시작 기준: `35ba5333cfba535ffb04796b62c6cf58e38829d2` (`origin/main`과 일치 확인)
- 고정 upstream: MATLAB `907f7e1f081a9d6a5703a32095d962143315a192`, XMODEL `4756a5086023547328ef44fd5fd87da3c250dc39`, digital `c6b80de19cdcad5b7e43fe7835588b629d847f75`

## 이번 개정 범위

기존 9장 연구 흐름과 디지털 RTL 설명의 깊이를 유지하면서 관련 연구를 거시적 연구 질문 중심으로 정리하고, digital 저장소의 36-case 실보드 accelerator-benefit benchmark와 real-ECG SAIF Vivado power evidence를 제6.1절과 source-of-truth에 반영하였다. 분류기와 RTL authority는 `c6b80de...`로 유지하고 activity-power benchmark evidence commit `d44e675...`을 별도 provenance로 등록하였다.

| 항목 | 개정 결과 |
|---|---:|
| 본문 장 | 9 |
| 본문 문자 수 | 63,017 |
| 통합 생성·보존 SVG | 19 |
| 상속 MATLAB PNG | 7 |
| immutable LTspice handoff 그림 | 10 |
| 본문 참조 그림 | 28 |
| Evidence map 행 | 76 |
| Claim registry 행 | 52 |
| 참고문헌 | 14 |
| Artifact registry | 1 (`RESOLVED_IMPORTED`) |

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
- DeepHHF는 미래 심부전 위험을, 본 연구는 현재 기록의 NSR·CHF·ARR·AF 클래스를 묻는다는 목적 차이를 주 비교축으로 두었다.
- 비교표는 정확도나 미시적 구현 차이 대신 각 연구가 최종적으로 답하는 질문을 비교한다. 최초성은 검토한 여섯 대표 연구 범위의 제한된 문장으로만 표현한다.

## 그림과 원본 회로도 경계

고정 MATLAB component의 일곱 그림은 내용이나 픽셀을 다시 만들지 않고 `figures/final/MAT-01`~`MAT-07`로 그대로 상속하였다. 사용자가 수정한 세 흐름의 구조를 해상도에 독립적인 SVG로 다시 구성해 `FIG-02_research_workflow.svg`, `FIG-15_afe_adc_signal_flow.svg`, `FIG-12_digital_processing_flow.svg`에 반영하였다. Analog Flow는 ECG+·ECG−의 두 HPF 경로가 IA에서 합류하고 `Input Disturbance Injection`, `R/C Mismatch Model`, `Op-Amp GBW / VOS Model`, `ADC Non-Ideality Injection`이 점선 경로로 분리된다. Digital Flow는 rhythm·morphology 경로를 `Feature Accumulation & Class Scoring`에서 합친 뒤 30개 Snapshot을 30분 Final Membrane으로 누적한다. 같은 내용을 반복하던 `FIG-04`, `FIG-13`, `FIG-14`는 보고서와 Figure index에서 제거하였다.

초기 고정 component에는 README에서 언급한 LTspice `.asc` 또는 원본 회로 캡처가 존재하지 않아 `UNRES-001`로 기록했었다. 2026-07-19 팀 handoff에서 XMODEL-aligned graphical `.asc`, generated `.net`, 전용 op-amp 모델, 35-run 실행 근거와 실제 회로 캡처가 제공되어 `validation/afe_ltspice_xmodel_aligned/`에 반입하고 `UNRES-001`을 `RESOLVED_IMPORTED`로 갱신하였다. 설명용 FIG-15와 실제 schematic 캡처 SPICE-02는 명확히 구분한다. Physical PCB, fabricated silicon, transistor/post-layout 또는 실제 전극 검증 claim은 여전히 추가하지 않았다.

## LTspice handoff 반입 보강 (2026-07-19)

- 흐름을 `MATLAB 공칭 사전설계 → LTspice 실제 schematic 구현·검증 → SystemVerilog XMODEL 행동모델·RTL 인계`로 명시하였다.
- XMODEL 계약에 정렬한 ±1.65 V AFE+ADC/S&H schematic, netlist와 전용 op-amp abstraction을 보존하였다.
- nominal/stress 35개 LTspice run이 모두 `EXECUTED`이고 fatal/warning signature가 없음을 execution manifest로 확인하였다.
- 동일 10초 ECG의 10,000개 ADC code에서 LTspice–XMODEL MAE 0.6445 LSB, RMS 1.3020 LSB, zero-lag correlation 0.999518, ±5 LSB 98.74%, ±10 LSB 99.89%, clipping 0을 반영하였다.
- 팀 제공 figure 10종은 원본 SHA256을 provenance manifest와 checker에 고정하였다.
- 수 GB raw waveform은 제외하고 회로, compact vector, 결과표, 로그와 재실행 스크립트를 반입하였다.

## 가속기 Benchmark 반입 내용

- 원천은 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 commit `d44e67517650f1f95ca67b93c2788f41e99f1a5e`으로 고정하였다.
- 대표 CPU 기준선은 hand-written single-thread transaction-level Exact C++로 두고 Python cycle model과 Verilator simulation runtime은 speedup 기준선에서 제외하였다.
- Exact C++ timing 전 pred 36/36, membrane 144/144, Snapshot 1,080/1,080과 post-benchmark equivalence를 확인하였다.
- Exact C++ kernel 1,777.699800 ms, end-to-end 2,007.549250 ms와 `profile_total-profile_input_wait` FPGA active-core 3,601,290 cycles, 36.012900 ms를 반영하였다.
- Exact C++와 FPGA active-core의 비율 49.362861641×를 제시하고, UART-paced raw interval 187,144.750920 ms는 transport diagnostic으로만 유지하였다.
- 1 MHz Pure RTL 0.099 W는 별도 vectorless power-only operating point로 보존하고, performance-matched 100 MHz real-ECG burst-SAIF accelerator+static/hierarchy dynamic/static 0.149500/0.052500/0.097000 W와 system 0.271 W를 분리하였다. 100 MHz allocated-total/active-dynamic energy 0.005383928550/0.001890677250 J/decision은 DERIVED_ESTIMATE다. Allocated active energy를 30분 주기 1,800초로 환산한 2.991071 µW는 완전 power-gating 가정의 연산 코어 평균전력으로만 등록하고, current FPGA·전체 wearable·실측 전력으로 확대하지 않는다. Integrated-system energy와 physical board 입력 전력 및 measured energy는 NOT_MEASURED다.

## 유지한 결과와 경계

- 24시간 Holter형 관찰은 설계 동기이고, MIT-BIH Arrhythmia의 30분 excerpt를 포함한 서로 다른 길이의 공개 원천을 같은 실제 시간으로 비교하기 위해 현재 공통 창을 30분으로 고정했음을 명시
- 30분 prototype을 임상적 24시간 Holter와 동등하거나 이를 대체하는 결과로 해석하지 않으며, 24시간 확장 시 Final Membrane 누적 폭·문턱값·간헐 사건 영향을 재검증
- 최종 30분 구간 29/36=80.56%, record-majority 16/19=84.21%
- Pure RTL 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns
- AFE 입력 SHA256, canonical AFE→RTL pred/mem, FPGA pred/mem의 각 36/36 범위
- Database–class confounding, physical/clinical/ASIC 한계
- Accelerator benchmark는 digital commit `d44e67517650f1f95ca67b93c2788f41e99f1a5e`에서 반입
- Exact C++ kernel 1,777.699800 ms, FPGA active-core 3,601,290 cycles/36.012900 ms, speedup 49.362861641×
- UART-paced raw counter 187,144.750920 ms는 transport diagnostic이며 integrated-system compute timing은 NOT_MEASURED
- Pure RTL 1 MHz 0.099 W는 vectorless power-only, Pure RTL 100 MHz real-ECG burst-SAIF accelerator+static/hierarchy dynamic/static 0.149500/0.052500/0.097000 W와 system 0.271 W는 ESTIMATED, 100 MHz allocated-total/active-dynamic energy 0.005383928550/0.001890677250 J는 DERIVED_ESTIMATE, 완전 power-gating 가정의 30분 평균 연산 코어 전력 2.991071 µW는 DERIVED UPPER_BOUND_ASSUMPTION; system energy와 physical board input power는 NOT_MEASURED

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

## 독자 중심 서술 간결화 (2026-07-19)

- 초록을 완성된 통합 시스템의 구성, 동작과 대표 성능만 남긴 한 문단으로 축약하였다.
- 제2장은 세부 기술 나열을 줄이고 `선행연구가 답하는 질문 → 전체 시스템 흐름 → 데이터와 평가 원칙` 순서로 재구성하였다.
- MATLAB·LTspice·XMODEL·RTL·FPGA가 각각 무엇을 확인하고 다음 단계에 무엇을 넘기는지 질문형 표로 정리하였다.
- 본문 성능 서술은 `확인하려는 질문 → 수치 → 독자에게 의미하는 바` 순서로 바꾸었다. 예를 들어 −83.557 dB는 60 Hz 진폭 약 1/15,000, 0.6445 LSB는 평균적으로 ADC 한 단계 미만, 29/36은 7개 오류, 36/36은 정확도가 아닌 구현 등가성으로 해석하였다.
- 재현에 필요한 정밀 수치는 결과표와 부록에 유지하고, 결론에서는 세부 소자값과 내부 블록 설명의 반복을 제거하였다.

## 완성 시스템 중심 논문 시점 정리 (2026-07-19)

- 초록에서 개발 순서, 남은 과제와 미래 검증 계획을 제거하고 AFE–ADC–RTL–FPGA 통합 시스템의 구조와 결과만 제시하였다.
- 본문에서 `원래 설계 목표`, `초기 버전`, `정본`, `무엇을 수정했는가`, `pre-alignment` 등 개발일지형 표현을 제거하였다.
- AFE는 최종 HPF·IA·active Twin-T·LPF·S/H·ADC 구성과 검증 결과만 설명하도록 정리하였다.
- RTL timing 절은 과거 병목 수치 대신 구현된 pipeline 단계, 최종 WNS와 36/36 기능 등가성만 제시한다.
- 제8장을 `시스템 특성과 적용 범위`로 바꾸고 향후 과제 목록 대신 완성된 결과와 각 수치의 적용 범위를 표로 정리하였다.
- 결론은 후속 작업을 열거하지 않고 통합 시스템이 달성한 아날로그 정합, 분류, FPGA 구현과 처리 결과로 끝맺었다.
- 30분 입력은 연구자가 서로 다른 데이터베이스를 임의로 조합한 결과가 아니라, 사용 가능한 공개 ECG 데이터셋의 서로 다른 기록 길이에 공통 적용할 수 있는 실제 관찰 길이라는 인과관계로 바로잡았다.

## 최종 자동 검증

- `tools/generate_integrated_figures.py`: PASS — 26개 생성(19 SVG+7 MATLAB PNG), LTspice handoff 10개 보존, FIG-P05 포함 37개 index
- `tools/check_integrated_technical_report.py`: PASS — 814 rules, 0 conflicts, chars 63,017, figures 28, evidence rows 76
- `tools/check_integrated_repository.py`: PASS — 533 rules, 0 conflicts
- CSV parsing/required columns: PASS
- `git diff --check`: commit 직전 재검증
