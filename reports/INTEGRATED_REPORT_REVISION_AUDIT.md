# Integrated report revision audit

## 상태

- Revision status: `COMPLETE`
- Branch: `codex/deep-reader-centered-report`
- Pre-revision HEAD: `4fbe1a9407b7b5d21decbeb38339aa43e18f049a`
- Fixed upstream: MATLAB `907f7e1f081a9d6a5703a32095d962143315a192`, XMODEL `4756a5086023547328ef44fd5fd87da3c250dc39`, digital `c6b80de19cdcad5b7e43fe7835588b629d847f75`

## 구조 변경

| 항목 | 개정 전 | 개정 후 |
|---|---:|---:|
| 본문 장 | 11 | 7 |
| 번호가 있는 하위 절 | 90개 이상 | 17 |
| 본문 문자 수 | 38,542 | 40,160 |
| 생성 그림 | 12 | 14 |
| 본문 참조 그림 | 12 | 8 |

기존 module별 목차를 연구 배경, 시스템/평가, 디지털 아키텍처, 구현, 결과, 논의/한계, 결론의 일곱 장으로 재구성했다. 제3장은 처음 읽는 독자가 용어를 정의받은 뒤 하나의 신호를 따라 리듬 경로와 파형 경로를 이해하도록 확장했다. 16개 이하 subsection 요구와 지정 구조의 17개 subsection이 충돌하므로, 더 구체적인 일곱 장 지정 구조를 우선하여 17개를 사용했다.

첫 정의 뒤에도 남아 있던 `sample/event/state/window`, `baseline/slope/amplitude/morphology`, `commit/readout/winner/evidence` 등의 일반 서술을 한국어 중심 표현으로 정리했다. RTL 신호명·모듈명·고정 인터페이스 명칭과 필요한 첫 영문 정의는 보존했다. Checker는 코드와 backtick 경로를 제외한 본문에서 불필요 영문 토큰 총량, 기계 치환으로 생길 수 있는 혼합어, 리듬/파형 경로의 통합 해석 경계가 정확히 두 개인지를 검사한다.

## 직접 RTL 감사에서 반영한 핵심

- Event encoder의 직전 표본 차분, one-cycle pulse와 adaptive threshold-bank calibration
- QRS의 old state→leak→event add→threshold→clock commit, refractory와 locked `QRS_LEAK=0`
- PNN의 46 hypothesis 순차 비교, strict `<` tie 처리와 previous-winner predictor
- RDM consecutive-RR 차분, ectopic adaptive reference/early–late state
- DSCR filtered slope sign 보존, RAM predicted window/maximum code/post hold
- QRS MAF pre 120/post 100 sample의 width·complexity·energy·pre-QRS pipeline
- RBBB-like independent onset, observation/terminal window, segment-level repeated evidence
- Snapshot current-next capture와 Final base→structural overlay→strict WTA

## 그림 변경

- FIG-12를 module 나열도에서 한국어 기능 흐름도로 개편했다.
- FIG-13에 old state→next calculation→clock commit timing을 추가했다.
- FIG-14에 DSCR/RAM/QRS MAF/RBBB-like의 finite observation window를 추가했다.
- `figure_data.json`과 `FIGURE_INDEX.md`에 architecture parameter와 직접 RTL source를 등록했다.

## 유지한 결과와 경계

Final 29/36, record-majority 16/19, Pure RTL 자원/WNS, three-way 36/36 evidence와 MATLAB/XMODEL 수치는 바꾸지 않았다. 36/36은 기능 등가성이지 label accuracy가 아니다. Database–class confounding, physical AFE/ADC·임상·ASIC gap을 유지하고 benchmark는 `PENDING_EXTERNAL_BENCHMARK_IMPORT`다. `0.099 W` 등 미수입 benchmark 수치는 본문에 넣지 않았다.

## 최종 검사

- `tools/generate_integrated_figures.py`: PASS — 14 SVG figures generated
- `tools/check_integrated_technical_report.py`: PASS — 289 rules, 0 conflicts, chars 40,160, figures 8, evidence rows 38
- `tools/check_integrated_repository.py`: PASS — 211 rules, 0 conflicts
- `git diff --check`: PASS

Final revision commit은 이 완료 audit를 포함하는 `codex/deep-reader-centered-report` branch HEAD다.
