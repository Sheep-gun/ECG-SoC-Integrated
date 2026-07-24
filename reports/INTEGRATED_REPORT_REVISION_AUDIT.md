# 통합 보고서 개정 감사

## 2026-07-24 본문 통합 개정

- `INTEGRATED_TECHNICAL_REPORT_KR.md`는 2026년 7월 23일 제출 기술내용을 중심으로 공개 보고서를 구성했다.
- 편집 방침을 설명하던 원문 보존 안내와 별도 부록을 제거했다.
- 개인정보, 서명, 신청 행정 정보와 권리보호 양식은 공개 저장소에서 제외했다.
- 사전 annotation 분석은 창작 과정, 선행연구는 알고리즘 비교, timing 병목 해결은 구현 결과, 재현성과 한계는 검증 및 목표 비교 절에 통합했다.
- 본문에서 인용한 여덟 문헌을 `[1]`부터 `[8]`까지 번호로 연결했다.

## 기준

- 대회 설계기술설명서의 공개 가능한 기술 내용
- MATLAB fixed commit `907f7e1f081a9d6a5703a32095d962143315a192`
- XMODEL fixed commit `4756a5086023547328ef44fd5fd87da3c250dc39`
- Digital fixed commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- 최신 benchmark evidence `d44e67517650f1f95ca67b93c2788f41e99f1a5e`

## 주요 개정

1. 공개 클래스명을 NSR, CHF, ARR, AF로 통일했다. legacy model ID, RTL port와 raw artifact의 `AFF`는 재현성을 위해 보존했다.
2. `SNN-inspired`를 `SNN 기반`으로 교체하고 event, LIF firing과 membrane accumulation의 구현 근거를 연결했다.
3. 사전 annotation 분석은 feature 선택에 사용되지만 최종 RTL 추론 입력에는 사용되지 않음을 명시했다.
4. 30분은 현재 검증 조건, 24시간 이상 Holter는 설계 지향점으로 분리했다.
5. RDM-to-prediction critical path 관측, pipeline 분할, timing 재검증과 기능 정합의 개발 이력을 추가했다.
6. 최종 구현 9,719 LUT와 5,038 FF를 profiler build 9,759 LUT와 5,049 FF에서 분리했다.
7. benchmark를 36.0129 ms, 49.36배, 142.0 mW와 조건부 2.991 µW의 최신 근거로 갱신했다.
8. 36-case compact acceptance와 저장소가 보유한 4-case raw-dump 재실행 범위를 분리했다.

## 유지한 한계

- database–class confounding
- 실제 24시간 정확도, 처리시간과 전력 미검증
- physical AFE PCB, ADC silicon, ASIC/post-layout와 clinical validation 미수행
- FPGA 전력은 activity 기반 추정이며 2.991 µW는 완전 power-gating 조건의 산출값

문장별 근거는 `INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv`에 있다.
