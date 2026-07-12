# 통합 기술보고서 검토 체크리스트

검토 대상: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`

## 독자가 처음 읽을 때의 이해 흐름

- [x] 본문은 9개 장으로 구성하고, 연구 진행 순서가 MATLAB→AFE·ADC/XMODEL→디지털 IP→benchmark→통합 검증→결과→논의·한계로 이어진다.
- [x] MATLAB 공칭 사전검증을 디지털 아키텍처보다 먼저 제시하고, 그 출력 파라미터와 기준 벡터가 AFE·ADC XMODEL의 입력 기준이 됨을 설명한다.
- [x] AFE·ADC XMODEL 검증 뒤에 signed stream을 소비하는 디지털 가속기 IP를 배치하여 아날로그 앞단과 디지털 뒷단의 인과관계를 유지한다.
- [x] 가속기 benchmark와 AFE·디지털 기능 등가성을 같은 장에서 서로 다른 질문으로 분리하고, 정량 benchmark는 외부 근거 반입 전까지 pending으로 둔다.
- [x] 초록은 배경→문제→제안 구조→검증→결과→한계 순서로 전개한다.
- [x] 디지털 설명은 전압 숫자열→차분 사건→QRS 누적·발화→리듬·파형 증거→Snapshot→Final Membrane 순서로 읽힌다.
- [x] AFE 설명은 필요성→구성→설계값→검증→다음 블록 연결 순서를 각 블록에 적용한다.
- [x] `token age`와 같은 내부 신호명은 직관적인 한국어 기능 설명 뒤에 필요한 경우만 제시한다.
- [x] benchmark는 분류기의 주 기여가 아니라 구현 효과를 보조하는 별도 결과이며, 외부 근거 반입 전까지 pending으로 유지한다.

## 장시간 ECG 관련 연구와 본 연구의 위치

- [x] 개별 심박 SNN, 연속 ECG 사건 탐지, multiple instance 집계, 가변 길이 CNN/LSTM, 24시간 Holter temporal model을 최종 판정 단위별로 구분한다.
- [x] Amirshahi–Hashemi 연구를 R-peak 주위 개별 심박의 진폭 spike encoding, STDP 특징 학습, reward/punishment R-STDP 분류로 설명하고 장시간 기록 집계 연구로 확대 해석하지 않는다.
- [x] Bauer 연구의 비동기 사건·recurrent SNN·binary trigger와 Chen 연구의 LC-ADC·SCNN·개별 심박 분류 범위를 공식 출판본 또는 저자 원고로 확인한다.
- [x] Shanmugam 연구의 약 48시간 ECG, 일부 고위험 instance 상위 20% 집계와 환자 단위 이진 예후 범위를 구분한다.
- [x] Zihlmann 연구의 9–61초 가변 길이 네 클래스 기록 분류와 CNN 특징의 평균/LSTM 통합을 반영하여 “4개 클래스” 자체를 최초 차별성으로 주장하지 않는다.
- [x] DeepHHF의 정식 제목·저자·2026년 npj Digital Medicine 출판·DOI를 재검증하고, 24시간 Holter의 30초 encoder 특징을 Transformer로 통합하는 이진 HF 예후 모델임을 명시한다.
- [x] 비교표는 서로 다른 과업·데이터셋·판정 단위의 정확도를 직접 순위 비교하지 않는다.
- [x] 본 연구의 핵심을 특정 60초·30분 수치가 아니라 간헐적 질환 증거의 강도·빈도·반복성과 장시간 일관성을 고정 폭 RTL 상태에 누적하는 streaming architecture로 설명한다.
- [x] “세계 최초”와 문헌 전체에 동일 연구가 없다는 단정을 사용하지 않고, 검토한 대표 선행연구 범위의 제한된 비교로만 위치를 설명한다.
- [x] 현재 검증 입력은 30분이고 24시간 정확도·처리시간·전력은 미검증이라는 경계를 유지한다.

## AFE·ADC 설계와 MATLAB/XMODEL 근거

- [x] ECG→HPF→3-op-amp IA→active Twin-T 60 Hz notch+buffer→150 Hz LPF→12-bit ADC→offset-binary→signed stream의 전체 흐름을 설명한다.
- [x] HPF 10 MΩ/33 nF와 0.4823 Hz, IA 100 kΩ/1 kΩ와 gain 201, LPF 1 kΩ/1.06 µF와 150.15 Hz를 직접 근거에 연결한다.
- [x] 수동 Twin-T의 넓은 저지대역과 loading 문제, active Twin-T와 buffer를 추가한 이유를 설명한다.
- [x] active Twin-T의 26.526 kΩ/100 nF, 200 nF/13.263 kΩ, k=0.95, Q≈5를 제시한다.
- [x] ADC ±1.65 V, 12 bit, 1 kSPS, 0.80586 mV/LSB와 0 V code mapping을 설명한다.
- [x] MATLAB은 공칭 필터·이득·동적 범위·기준 벡터, XMODEL은 비이상성·간섭·mismatch·GBW/VOS·ADC stress·장시간 stream을 담당한다고 구분한다.
- [x] IA 수렴, notch loading, LPF cutoff, CMRR margin, ADC log off-by-one, passive→active notch 변경을 실제 수정 이력으로 기록한다.
- [x] 주파수응답, clipping/headroom, 50/60 Hz PLI, R/C mismatch, GBW/VOS, ADC 비이상성과 장시간 stream 결과를 수치로 제시한다.
- [x] MATLAB 기준 벡터→XMODEL signed stream→SHA256→RTL handoff를 설명한다.
- [x] 고정 component에 원본 LTspice `.asc`/회로 캡처가 없음을 확인하고, FIG-15를 원본이 아닌 설명용 재구성도로 표시한다.
- [x] 누락 원본 schematic을 `source_of_truth/unresolved_artifacts.csv`에 unresolved artifact로 기록한다.
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
- [x] accelerator benchmark 수치는 `PENDING_EXTERNAL_BENCHMARK_IMPORT` 상태를 유지한다.

## Artifact와 자동 검증

- [x] MATLAB `907f7e1`, XMODEL `4756a508`, digital `c6b80de` provenance를 유지한다.
- [x] evidence map의 모든 path와 claim ID가 유효하다.
- [x] figure generator가 15개 SVG와 상속 MATLAB PNG 7개, index와 data를 생성한다.
- [x] 본문은 16개 그림을 사용하고 AFE·ADC 관련 9개 그림 caption에 직접 evidence path를 둔다.
- [x] `tools/check_integrated_technical_report.py` PASS
- [x] `tools/check_integrated_repository.py` PASS
- [x] `git diff --check` PASS

## 공식 신청서에서만 사람이 편집할 부분

- HWP page/field 제한에 맞춘 축약과 그림 배치
- 검증된 외부 benchmark 산출물이 들어온 뒤의 supporting table
- 지도교수·소속·개인정보·서명 등 private 제출 정보
