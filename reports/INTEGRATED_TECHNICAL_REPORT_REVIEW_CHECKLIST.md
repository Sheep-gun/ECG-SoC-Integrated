# Integrated technical report review checklist

검토 대상: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`

## 구조와 서술

- [x] 제목, 900~1,300자 초록, 핵심어, 1~11장, 참고문헌, 부록 A/B/C가 존재한다.
- [x] 요구된 모든 subsection이 outline이 아닌 설명 문단을 포함한다.
- [x] MATLAB, XMODEL, digital architecture, evaluation, RTL/IP/FPGA와 integration evidence가 하나의 연속 narrative로 합성됐다.
- [x] Primary contribution을 long-window Snapshot/Final-Membrane architecture로 두고 speed를 primary novelty로 쓰지 않았다.
- [x] Existing overview figures와 FIG-12 detailed digital architecture를 caption·scope·limitation과 함께 참조한다.
- [x] 목표, interface, dataset/license, split, feature blocks, MATLAB, XMODEL, classification, confusion, integration, resources, streaming, limitations, benchmark 표가 존재한다.
- [x] 제8장은 결과를 종합하는 실질적 논의이고 제9장은 창의성·기술성·완성도를 심사 관점에서 구분한다.
- [x] Final Membrane, guard/rescue/veto/silent-AFF와 deterministic WTA가 중심 구조로 설명된다.

## 수치 일치

- [x] Train `61/68=89.71%`가 `global_metrics.yaml`과 일치한다.
- [x] Validation `32/32=100.00%`를 model-selection only로 한정했다.
- [x] Final-test chunk `29/36=80.56%`, macro F1 `80.44%`가 일치한다.
- [x] Record-majority `16/19=84.21%`, macro F1 `80.80%`가 일치한다.
- [x] `final_test_evaluation_count=1`, `test_used_for_selection=false`를 명시했다.
- [x] MATLAB representative clipping `0%`, minimum headroom 약 `1.0196 V`가 일치한다.
- [x] Emulator–XMODEL mean RMS `1.95 LSB`, lag `0`을 correct scope로 썼다.
- [x] PLI `0.92/118 mV`, mismatch CMRR `100.7/80.0 dB`, ADC stress `15/16`을 CLM-025~027로 분리했다.
- [x] Pure RTL `9719 LUT / 5038 FF / 0 BRAM / 0 DSP / WNS 8.184 ns`가 일치한다.
- [x] MicroBlaze system `12494 LUT / 8494 register / 16 BRAM / 3 DSP / setup WNS 0.097 ns`가 일치한다.
- [x] Input SHA, AFE-to-RTL 및 board equivalence의 각 `36/36` scope를 분리했다.
- [x] `1,800,000×12=21,600,000 bit=2,700,000 byte≈2.7 MB decimal`을 avoided full raw-input window storage로만 표시했다.

## Claim 및 ownership

- [x] SAFE claim은 직접 기술하고 CAREFUL claim은 같은 문단에서 limitation을 제시했다.
- [x] FORBIDDEN claim을 긍정문으로 사용하지 않았다.
- [x] `SNN-inspired event/state architecture`를 trained deep SNN/STDP/online learning과 구분했다.
- [x] 서민우–MATLAB, 이수환–XMODEL/integration, 양건–digital/lead/report ownership을 유지했다.
- [x] Board 36/36 functional equivalence와 label accuracy 29/36을 명시적으로 구분했다.
- [x] Validation 100%를 final generalization result로 승격하지 않았다.

## Dataset 및 검증 경계

- [x] NSR/chf/ARR/AFF가 서로 다른 source database에서 왔음을 밝혔다.
- [x] Record-wise split이 direct leakage를 막지만 database–class confounding을 해결하지 않음을 밝혔다.
- [x] Filename/path/record ID/DB name/split metadata가 classifier feature가 아님을 밝혔다.
- [x] Common signed stream이 domain removal의 증거가 아님을 밝혔다.
- [x] Confounding이 classification generalization을 제한하지만 RTL/IP/board evidence를 무효화하지 않음을 밝혔다.
- [x] MATLAB/XMODEL을 physical, transistor-level, post-layout, silicon validation으로 표현하지 않았다.
- [x] Clinical diagnosis, commercial superiority, fabricated-SoC claim을 하지 않았다.
- [x] CLM-023은 direct RTL/state inventory로 지지하며 BRAM=0 또는 total FF만을 단독 근거로 쓰지 않았다.
- [x] 소비자 ECG 배경은 특정 규제 문서 사례로 한정하고 모든 wearable에 일반화하지 않았다.

## Benchmark·참고문헌·privacy

- [x] Benchmark section은 `PENDING_EXTERNAL_BENCHMARK_IMPORT`와 pending table만 포함한다.
- [x] 금지된 latency/throughput/speedup/power/energy 수치를 삽입하지 않았다.
- [x] 참고문헌은 authoritative product/guideline/dataset/license source와 dataset DOI/citation을 포함한다.
- [x] Raw PhysioNet data 미번들, fixed-version fetch/hash/license policy를 본문에 명시했다.
- [x] Student ID, private email, phone number, address, signature를 포함하지 않았다.
- [x] Official private HWP/application form과 본 integrated technical manuscript를 구분했다.

## Automated validation

- [x] `tools/check_integrated_technical_report.py` PASS
- [x] `tools/check_integrated_repository.py` PASS
- [x] Referenced figures/evidence paths exist
- [x] Report evidence-map CSV parses with required columns
- [x] Integrated Git worktree clean after commit

## Official application에서 사람이 편집할 부분

- Official form의 page/character limit에 맞춘 축약과 표·그림 재배치
- 대회 양식의 연구 배경/목표/방법/결과/창의성/사업성 항목으로 재구성
- 독립 benchmark 완료 후 검증된 supporting table만 추가
- 지도교수·소속·개인정보·서명은 private HWP에서만 작성
- Dataset confounding과 physical/clinical boundary 문구를 최종 심사본에서도 유지
