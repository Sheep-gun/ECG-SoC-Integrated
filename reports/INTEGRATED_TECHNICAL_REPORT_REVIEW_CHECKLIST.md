# 통합 기술보고서 검토 체크리스트

검토 대상: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`

## 독자가 처음 읽을 때의 이해 흐름

- [x] 초록은 문제·구조·대표 결과·한계만 한 문단으로 요약하고 세부 회로값과 알고리즘 설명은 본문으로 보낸다.
- [x] 제2장은 알고리즘 이름보다 “얼마나 긴 ECG를 보고 마지막에 무엇을 출력하는가”를 먼저 설명한다.
- [x] 성능 수치는 `확인할 질문 → 결과 → 그 결과가 뜻하는 것` 순서로 서술하고, 정밀 원자료는 표와 부록에 남긴다.
- [x] 본문은 9개 장으로 구성하고, 연구 진행 순서가 MATLAB→AFE·ADC/XMODEL→디지털 IP→benchmark→통합 검증→결과→논의·한계로 이어진다.
- [x] MATLAB 공칭 사전검증을 디지털 아키텍처보다 먼저 제시하고, 그 출력 파라미터와 기준 벡터가 AFE·ADC XMODEL의 입력 기준이 됨을 설명한다.
- [x] AFE·ADC XMODEL 검증 뒤에 signed stream을 소비하는 디지털 가속기 IP를 배치하여 아날로그 앞단과 디지털 뒷단의 인과관계를 유지한다.
- [x] 가속기 benchmark와 AFE·디지털 기능 등가성을 같은 장에서 서로 다른 질문으로 분리하고, NO_BOARD 수치와 physical board pending을 구분한다.
- [x] 초록의 대표 수치는 각각 아날로그 인계, 분류 성능, FPGA 재현성이라는 의미가 바로 드러난다.
- [x] 디지털 Figure는 QRS 검출 뒤 rhythm·morphology 경로를 분기하고 class scoring에서 합친 뒤 Snapshot 30개를 Final Membrane으로 누적한다.
- [x] AFE 설명은 필요성→구성→설계값→검증→다음 블록 연결 순서를 각 블록에 적용한다.
- [x] `token age`와 같은 내부 신호명은 직관적인 한국어 기능 설명 뒤에 필요한 경우만 제시한다.
- [x] benchmark는 분류기의 주 기여가 아니라 구현 효과를 보조하는 별도 결과이며, Exact C++ 측정·cycle-derived core·estimated power를 구분한다.

## 장시간 ECG 관련 연구와 본 연구의 위치

- [x] 선행연구 비교축을 세부 신경망·회로 차이가 아니라 “어느 범위의 ECG를 보고 최종적으로 어떤 질문에 답하는가”로 둔다.
- [x] 선행연구를 한 심박 분류, 이상 순간 알림, 미래 위험 예측, 장시간 기록 통합으로 묶어 차이를 짧게 설명한다.
- [x] DeepHHF가 본 연구와 구조적 흐름이 가장 유사함을 인정하되, 미래 위험 예측과 현재 기록 분류라는 질문의 차이를 전면에 둔다.
- [x] 비교표는 서로 다른 과업·데이터셋·판정 단위의 정확도를 직접 순위 비교하지 않는다.
- [x] 본 연구의 핵심을 간헐적 질환 구간을 포착하고 반복 증거를 모아 현재 기록의 네 클래스를 판정하는 흐름으로 설명한다.
- [x] “세계 최초”라고 단정하지 않고, 현재 검증 입력은 30분이며 24시간 성능은 미검증이라는 경계를 유지한다.

## AFE·ADC 설계와 MATLAB/LTspice/XMODEL 근거

- [x] ECG→HPF→3-op-amp IA→active Twin-T 60 Hz notch+buffer→150 Hz LPF→12-bit ADC→offset-binary→signed stream의 전체 흐름을 설명한다.
- [x] HPF 10 MΩ/33 nF와 0.4823 Hz, IA 100 kΩ/1 kΩ와 gain 201, LPF 1 kΩ/1.06 µF와 150.15 Hz를 직접 근거에 연결한다.
- [x] 수동 Twin-T의 넓은 저지대역과 loading 문제, active Twin-T와 buffer를 추가한 이유를 설명한다.
- [x] active Twin-T의 26.526 kΩ/100 nF, 200 nF/13.263 kΩ, k=0.95, Q≈5를 제시한다.
- [x] ADC ±1.65 V, 12 bit, 1 kSPS, 0.80586 mV/LSB와 0 V code mapping을 설명한다.
- [x] MATLAB은 공칭 필터·이득·동적 범위·기준 벡터, LTspice는 실제 schematic·전원·S/H·ADC mapping과 회로 stress, XMODEL은 비이상성·간섭·장시간 stream과 RTL 인계를 담당한다고 구분한다.
- [x] IA 수렴, notch loading, LPF cutoff, CMRR margin, ADC log off-by-one, passive→active notch 변경을 실제 수정 이력으로 기록한다.
- [x] 주파수응답, clipping/headroom, 50/60 Hz PLI, R/C mismatch, GBW/VOS, ADC 비이상성과 장시간 stream 결과를 수치로 제시한다.
- [x] MATLAB 기준→LTspice schematic 검증→XMODEL signed stream→SHA256→RTL handoff를 설명한다.
- [x] XMODEL-aligned LTspice `.asc`·`.net`·전용 op-amp 모델과 실제 회로 캡처를 보존하고, FIG-15 설명용 흐름도와 SPICE-02 실제 schematic을 구분한다.
- [x] 기존 누락 schematic 항목 `UNRES-001`을 `RESOLVED_IMPORTED`로 갱신하고 physical PCB·transistor/post-layout·silicon 경계는 유지한다.
- [x] 기존 MATLAB 그림 7개를 byte-for-byte 상속하고 각각 원본 파일 및 설명 문서로 연결한다.

## 디지털 RTL 메커니즘

- [x] Event encoder의 signed 차분, one-cycle pulse와 adaptive bank 선택을 설명한다.
- [x] QRS의 이전 상태→누설→사건 가산→문턱 비교→reset/refractory 순서와 locked leak=0을 구분한다.
- [x] PNN, RDM, ectopic, DSCR, RAM, QRS MAF와 RBBB-like 경로의 관찰 목적과 상태 갱신을 설명한다.
- [x] Snapshot의 현재 `*_next` 저장과 Final base/guard/rescue/veto/silent-AFF/WTA를 설명한다.
- [x] 디지털 기존 설명의 깊이와 고정 결과를 낮추거나 변경하지 않는다.

## 결과와 claim 경계

- [x] Final chunk 29/36=80.56%, record-majority 16/19=84.21%와 validation 100%의 model-selection 용도를 구분한다.
- [x] Pure RTL 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP와 WNS 8.184 ns를 device/tool-specific 결과로 둔다.
- [x] 입력 SHA, AFE→RTL과 FPGA의 36/36 scope를 분리하고 기능 등가성을 분류 정확도 100%로 표현하지 않는다.
- [x] database–class confounding과 physical PCB/silicon/post-layout/clinical gap을 명시한다.
- [x] `SNN-inspired`를 trained deep SNN, STDP, online learning 또는 생물학적 동일성과 구분한다.
- [x] 24시간 Holter가 설계 동기이지만 MIT-BIH Arrhythmia의 30분 excerpt 때문에 현재 공통 평가 창을 30분으로 고정했다는 선택 근거를 설명한다.
- [x] 30분 prototype 결과를 임상적 24시간 Holter의 대체·동등성으로 해석하지 않고, 24시간 확장 시 Final Membrane 재검증이 필요함을 명시한다.
- [x] accelerator benchmark는 `09e4d840...`의 Exact C++ 1,777.699800 ms, cycle-derived core 54.012600 ms와 32.912687배 추정 비교를 사용한다.
- [x] Exact C++ timing 전에 pred 36/36, membrane 144/144와 Snapshot 1,080/1,080 등가성을 확인한다.
- [x] Python cycle model과 Verilator simulation runtime을 대표 CPU inference 기준선으로 사용하지 않는다.
- [x] 54.012600 ms를 live 30분 판정시간으로 표현하지 않고, 32.912687배를 measured board speedup으로 표현하지 않는다.
- [x] 0.099 W와 0.005347247400 J/decision을 estimated/derived로 표시하고 physical board 측정값과 구분한다.

## Artifact와 자동 검증

- [x] 전체 workflow 그림은 공개 ECG 직후 Record-wise Train·Validation·Locked Test 분할을 표시한다.
- [x] Train·Validation만 MATLAB과 사전 잠금 설계·검증에 사용하고, Locked Test는 Design Lock 뒤 최초 1회 최종시험에만 사용함을 표시한다.
- [x] XMODEL·RTL 병렬 분기, 두 경로가 입력되는 AFE–RTL 통합, RTL 전용 benchmark·FPGA board replay 분기를 교차 배선 없이 표시한다.
- [x] 세 검증 결과를 단일 판단 gate로 모으고, 불충족 loop가 MATLAB이 아니라 XMODEL·RTL 단계로 돌아가도록 표시한다.
- [x] MATLAB `907f7e1`, XMODEL `4756a508`, digital `c6b80de` provenance를 유지한다.
- [x] evidence map의 모든 path와 claim ID가 유효하다.
- [x] figure generator가 통합 SVG, 상속 MATLAB PNG 7개와 immutable team handoff figure 10개를 index에 등록한다.
- [x] 본문은 MATLAB–LTspice–XMODEL 검증 figure와 디지털 구현 figure를 분리하고 caption에 직접 evidence path를 둔다.
- [x] `tools/check_integrated_technical_report.py` PASS
- [x] `tools/check_integrated_repository.py` PASS
- [x] `git diff --check` PASS

## 공식 신청서에서만 사람이 편집할 부분

- HWP page/field 제한에 맞춘 축약과 그림 배치
- physical board timer·idle/active power 측정이 완료된 뒤의 supporting table
- 지도교수·소속·개인정보·서명 등 private 제출 정보
