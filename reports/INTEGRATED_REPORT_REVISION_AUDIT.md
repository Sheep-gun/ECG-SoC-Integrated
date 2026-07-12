# Integrated report revision audit

## 상태

- Revision status: `COMPLETE`
- Branch: `main`
- Current revision base: `6d54a3fde79ccef6d87fb38cc473a7f12d45d88c`
- Original seven-chapter revision base: `4fbe1a9407b7b5d21decbeb38339aa43e18f049a`
- Fixed upstream: MATLAB `907f7e1f081a9d6a5703a32095d962143315a192`, XMODEL `4756a5086023547328ef44fd5fd87da3c250dc39`, digital `c6b80de19cdcad5b7e43fe7835588b629d847f75`

## 구조 변경

| 항목 | 개정 전 | 개정 후 |
|---|---:|---:|
| 본문 장 | 11 | 7 |
| 번호가 있는 하위 절 | 90개 이상 | 17 |
| 본문 문자 수 | 38,542 | 38,901 |
| 생성 그림 | 12 | 14 |
| 본문 참조 그림 | 12 | 8 |

기존 module별 목차를 연구 배경, 시스템/평가, 디지털 아키텍처, 구현, 결과, 논의/한계, 결론의 일곱 장으로 재구성했다. 제3장은 처음 읽는 독자가 용어를 정의받은 뒤 하나의 신호를 따라 리듬 경로와 파형 경로를 이해하도록 확장했다. 16개 이하 subsection 요구와 지정 구조의 17개 subsection이 충돌하므로, 더 구체적인 일곱 장 지정 구조를 우선하여 17개를 사용했다.

첫 정의 뒤에도 남아 있던 `sample/event/state/window`, `baseline/slope/amplitude/morphology`, `commit/readout/winner/evidence` 등의 일반 서술을 한국어 중심 표현으로 정리했다. RTL 신호명·모듈명·고정 인터페이스 명칭과 필요한 첫 영문 정의는 보존했다. Checker는 코드와 backtick 경로를 제외한 본문에서 불필요 영문 토큰 총량, 기계 치환으로 생길 수 있는 혼합어, 리듬/파형 경로의 통합 해석 경계가 정확히 두 개인지를 검사한다.

이번 재개정에서는 제3장뿐 아니라 초록·서론·AFE/FPGA 구현·실험 결과·논의·결론도 처음 보는 심사자의 질문 순서에 맞췄다. 결과 문단은 각 수치가 무엇을 평가하고 무엇을 증명하며 무엇을 증명하지 않는지 설명하도록 고쳤다. DSCR·RAM·QRS MAF·RBBB-like 설명은 모듈명보다 관찰 목적과 계산 과정을 먼저 제시하고, 생성 상태가 Snapshot 및 Final Membrane으로 전달되는 위치를 명시했다.

최종 직관성 개정에서는 ECG 입력을 “시간 순서대로 들어오는 부호 있는 숫자 나열”로 시작하고 `현재값-직전값→강한 사건→QRS 막전위 누적→발화·초기화·불응기` 순서로 다시 썼다. `token age`, 내부 평가 레지스터명과 같은 신호 중심 용어는 “직전 박동 이후 들어온 표본값 개수”, “먼저 저장하고 다음 클록에 비교”처럼 회로 동작으로 풀었다. Strong Event는 뉴런 발화로 해석할 수 있지만 실제 RTL은 별도 막전위가 아닌 차분·절댓값·문턱 비교기임을 명시했고, 일반 LIF 누설 원리와 고정 `QRS_LEAK=0` 설정을 구분했다.

Micromachines 2025 기준 논문 19쪽 전체를 본문 추출과 페이지 렌더링으로 검토했다. 초록은 배경·제안·구조·검증·결과·한계 순서로 다시 구성하고, 제2장은 전체 저장 방식·짧은 구간 회로·학습형 SNN의 한계에서 설계 요구를 도출하도록 바꿨다. 제3장의 박동·리듬·파형·Snapshot/Final 설명은 목적별 3단계 절 번호로 나눴다. 제4장과 제5장에는 각 장이 답하는 질문을 먼저 제시했다. 세부 분석과 적용 기준은 `reports/BASELINE_PAPER_STRUCTURE_REVIEW_KR.md`에 남겼다.

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
- 본문에서 사용하는 FIG-01·02·04·08·10·12·13·14의 제목과 내부 문구를 짧은 한국어 기능 표현으로 통일했다.

## 유지한 결과와 경계

Final 29/36, record-majority 16/19, Pure RTL 자원/WNS, three-way 36/36 evidence와 MATLAB/XMODEL 수치는 바꾸지 않았다. 36/36은 기능 등가성이지 label accuracy가 아니다. Database–class confounding, physical AFE/ADC·임상·ASIC gap을 유지하고 benchmark는 `PENDING_EXTERNAL_BENCHMARK_IMPORT`다. `0.099 W` 등 미수입 benchmark 수치는 본문에 넣지 않았다.

## 최종 검사

- `tools/generate_integrated_figures.py`: PASS — 14 SVG figures generated
- `tools/check_integrated_technical_report.py`: PASS — 337 rules, 0 conflicts, chars 38,901, figures 8, evidence rows 38
- `tools/check_integrated_repository.py`: PASS — 211 rules, 0 conflicts
- `git diff --check`: PASS

Final revision commit은 이 완료 audit를 포함하는 `main` branch HEAD다.
