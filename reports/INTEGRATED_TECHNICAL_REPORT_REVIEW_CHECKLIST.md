# 통합 기술보고서 검토 체크리스트

검토 대상: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`

## 독자가 처음 읽을 때의 이해 흐름

- [x] 본문은 7개 장을 유지하고, 부품별 나열보다 설계 목적과 신호 흐름을 중심으로 구성한다.
- [x] 초록은 배경→문제→제안 구조→검증→결과→한계 순서로 전개한다.
- [x] 디지털 설명은 전압 숫자열→차분 사건→QRS 누적·발화→리듬·파형 증거→Snapshot→Final Membrane 순서로 읽힌다.
- [x] AFE 설명은 필요성→구성→설계값→검증→다음 블록 연결 순서를 각 블록에 적용한다.
- [x] `token age`와 같은 내부 신호명은 직관적인 한국어 기능 설명 뒤에 필요한 경우만 제시한다.
- [x] benchmark는 분류기의 주 기여가 아니라 구현 효과를 보조하는 별도 결과이며, 외부 근거 반입 전까지 pending으로 유지한다.

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
