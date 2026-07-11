# Integrated technical report review checklist

검토 대상: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`

## 처음 읽는 심사자의 이해 흐름

- [x] 본문은 정확히 7개 장이며 module별 목차 대신 기능별 17개 묶음 절을 사용한다.
- [x] 제3장이 가장 긴 기술 핵심 장이다.
- [x] sample, event, membrane, leak, threshold, refractory, beat, RR, Snapshot, Final Membrane을 세부 module 전에 정의한다.
- [x] 하나의 비임상 신호 예시가 event→beat→RR/파형→Snapshot→Final 흐름을 연결한다.
- [x] FIG-12는 한국어 기능명을 1차 label, module명을 2차 label로 사용한다.
- [x] FIG-13은 old state→next calculation→clock commit을, FIG-14는 finite morphology window를 보여준다.

## RTL mechanism 직접 감사

- [x] Event encoder의 signed 차분, one-cycle pulse와 adaptive bank 선택을 설명한다.
- [x] QRS의 leak→event add→threshold→reset/refractory 순서와 locked leak=0을 구분한다.
- [x] PNN의 46-center sequential scan, tie 처리와 previous-winner prediction을 설명한다.
- [x] RDM의 consecutive RR absolute difference와 level/code를 설명한다.
- [x] Ectopic path의 adaptive reference와 early/late 교대 state를 설명한다.
- [x] DSCR의 filtered slope, retained sign과 direction-change pulse를 설명한다.
- [x] RAM의 predicted beat window, maximum amplitude code와 post hold를 설명한다.
- [x] QRS MAF의 pre 120/post 100 sample, width/complexity/energy/pre-QRS 및 pipeline을 설명한다.
- [x] RBBB-like path의 independent onset, observation/terminal window와 repeated segment evidence를 설명한다.
- [x] Snapshot counter의 current `*_next` capture와 Final base/guard/rescue/veto/silent-AFF/WTA를 설명한다.

## 결과와 claim 경계

- [x] Final chunk 29/36=80.56%, record-majority 16/19=84.21%가 source와 일치한다.
- [x] Validation 100%는 model-selection only다.
- [x] Pure RTL 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP와 WNS 8.184 ns를 device/tool-specific 결과로 쓴다.
- [x] Input SHA, AFE→RTL, FPGA의 각 36/36 scope를 분리한다.
- [x] 기능 등가성 36/36을 label accuracy 100%로 표현하지 않는다.
- [x] Database–class confounding, physical/clinical/ASIC gap을 명시한다.
- [x] SNN-inspired를 trained deep SNN, STDP, online learning, biological equivalence와 구분한다.
- [x] Accelerator benchmark는 독립 evidence import 전까지 pending이며 금지 수치를 쓰지 않는다.

## Artifact와 자동 검증

- [x] MATLAB `907f7e1`, XMODEL `4756a508`, digital `c6b80de` provenance를 유지한다.
- [x] 서민우–MATLAB, 이수환–XMODEL, 양건–digital/report ownership을 유지한다.
- [x] Evidence-map CSV의 모든 path와 claim ID가 유효하다.
- [x] `tools/generate_integrated_figures.py`가 14개 SVG와 figure index/data를 생성한다.
- [x] `tools/check_integrated_technical_report.py` PASS
- [x] `tools/check_integrated_repository.py` PASS
- [x] `git diff --check` PASS

## 공식 신청서에서 사람이 편집할 부분

- HWP page/field 제한에 맞춘 축약과 표·그림 재배치
- 독립 benchmark 완료 후 검증된 supporting table만 추가
- 지도교수·소속·개인정보·서명은 private HWP에서만 작성
