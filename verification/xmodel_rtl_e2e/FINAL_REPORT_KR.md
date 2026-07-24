# 실제 XMODEL AFE–ADC → 고정 Pure RTL XSim replay 최종 보고

검증 일자: 2026-07-23
최종 판정: **FAIL — 실제 XMODEL full-30분 ADC가 4/36개만 존재하여 36-case PASS 기준 미충족**

## 1. 사용한 고정 RTL commit과 top

- Digital component commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- Top: `snn_ecg_30min_final_top`
- 입력: signed `adc_data[11:0]`, `sample_valid`
- 출력: `final_pred_class`, `final_mem_nsr`, `final_mem_chf`, `final_mem_arr`, `final_mem_aff` (요청서의 `final_mem_af`에 해당)
- 사용 소스: 통합 저장소 `design/digital/rtl/`

통합 저장소 자체의 현재 HEAD는 composite repository commit `0413aaaf...`이고 digital commit 객체를 직접 보유하지 않는다. 따라서 `project_registry/artifact_manifest.csv`가 `c6b80de...`에서 export했다고 기록한 SHA-256과 실제 사용 RTL 17개 파일을 대조했다. 결과는 **17/17 일치**이며 세부값은 `rtl_source_hash_manifest.csv`에 있다. RTL, parameter, weight, threshold는 수정하지 않았다.

## 2. 실제 XMODEL ADC 데이터 위치와 생성 근거

실제 full-30분 XMODEL accepted dump 위치:

```text
datasets/xmodel_afe_adc_outputs/representative_4case/accepted_<case>.mem
```

파일 출처는 이름이 아니라 다음 문서·코드 흐름으로 확인했다.

1. `tb_snn_ecg_30min_mixed_e2e.sv`가 ECG PWL을 `ecg_afe_xmodel`에 입력한다.
2. XMODEL offset-binary `afe_adc[11:0]`를 `{~afe_adc[11], afe_adc[10:0]}`로 signed 12-bit 변환한다.
3. `sample_valid && sample_ready` 때 RTL이 실제 수락한 code를 `%03h`로 dump한다.
4. `run_rep4_full30min.sh`가 `accepted_<case>.mem`을 생성하고, 바로 그 파일을 Pure RTL replay manifest에 넣는다.
5. `integ_<case>.log`의 직접 통합 결과와 `rep4_e2e_verification.csv`의 XMODEL SHA가 존재 파일의 재계산 SHA와 일치한다.

반면 `part1_input_sha256_compare_36case.csv`의 36/36은 `afe_full.py` 계열 Python emulator chunk와 기존 RTL replay 입력의 바이트 무결성 결과다. 실제 XMODEL 출력 36개를 증명하지 않는다. 자세한 분류와 누락 목록은 `ADC_DATA_PROVENANCE_KR.md`에 있다.

## 3. 36개 입력 파일 존재 및 표본 수 확인 결과

실제 XMODEL full-30분 dump는 **4/36개**, 누락은 **32/36개**다. 사용자 홈 전체에서 `accepted_*.mem` 및 `xmodel_chunks`를 검색했지만 추가 full-30분 XMODEL dump는 발견되지 않았다.

| case | samples | invalid token | signed min | signed max | 상태 |
|---|---:|---:|---:|---:|---|
| AFF_afdb_06995_chunk01 | 1,800,000 | 0 | -586 | 371 | PRESENT_VALID |
| ARR_mitdb_102_chunk00 | 1,800,000 | 0 | -359 | 378 | PRESENT_VALID |
| CHF_chfdb_chf06_chunk06 | 1,800,000 | 0 | -333 | 364 | PRESENT_VALID |
| NSR_nsrdb_16272_chunk03 | 1,800,000 | 0 | -293 | 455 | PRESENT_VALID |

모든 존재 파일은 정확히 3 hex digit/표본이고 12-bit 범위 `[-2048, 2047]` 안에 있다. 36개 전체 행은 `input_sha256_manifest_36case.csv`에 있으며 누락 32개는 `MISSING_XMODEL_ADC`로 기록했다.

## 4. Vivado/XSim replay 방법

- Simulator: Vivado Simulator 2020.2 (`xvlog`, `xelab`, `xsim`)
- Testbench: `tb_snn_ecg_30min_chunk_dataset.v`
- `MAX_SAMPLES=1800000`
- `SNAPSHOT_SAMPLES=60000`
- `SNAPSHOTS_PER_CHUNK=30`
- `POST_DONE_TICKS=37`
- `PROFILE_EN=1`
- replay `sample_gap_cycles=2`

한 번의 compile/elaboration 뒤 실제 XMODEL dump 4개만 manifest에 넣어 순차 replay했다. 실행 명령은 `xsim_commands.txt`, compile/elaboration/simulation transcript는 각각 `xvlog.log`, `xelab.log`, `xsim.log`에 있다. 실행기는 `tools/verification/run_xmodel_adc_pure_rtl_replay.py`다.

직접 통합 cadence는 36,000,612 cycles, replay cadence는 5,401,260 cycles였다. 동일 ADC code 순서에서 class와 membrane은 일치했으므로 이 cadence 차이는 기능 실패로 판정하지 않았다.

## 5. 입력 SHA-256 결과

| case | 실제 XMODEL accepted/replay 입력 SHA-256 | 직접 통합 기록과 일치 |
|---|---|---|
| AFF_afdb_06995_chunk01 | `aa1ad761304577bc5b0e155662eae8b3ef92764a8c8a87bb4ec45bc3fde5ac33` | PASS |
| ARR_mitdb_102_chunk00 | `9598048fc02782870d749ae54ceea063e4d08ab3b5e2c844d58046743d0ae6e6` | PASS |
| CHF_chfdb_chf06_chunk06 | `9d87db70fc9224c8fab7f2e035dec32201da14b79b1f61df015937974b221417` | PASS |
| NSR_nsrdb_16272_chunk03 | `71541d54f921632c229570d0b1298ec6d87653eb0b2e85cc1f77217c2723f541` | PASS |

- 존재 파일 기준: **4/4 PASS**
- 요구한 36-case 기준: **4/36 — FAIL**

## 6. 최종 클래스 일치 결과

| case | 직접 통합 | 새 XSim replay | bit-exact |
|---|---:|---:|---|
| AFF_afdb_06995_chunk01 | 3 | 3 | PASS |
| ARR_mitdb_102_chunk00 | 2 | 2 | PASS |
| CHF_chfdb_chf06_chunk06 | 1 | 1 | PASS |
| NSR_nsrdb_16272_chunk03 | 0 | 0 | PASS |

- 존재 파일 기준: **4/4 PASS**
- 요구한 36-case 기준: **4/36 — FAIL**

## 7. Final Membrane 일치 결과

| case | 직접 통합 [NSR, CHF, ARR, AF] | 새 XSim replay | bit-exact |
|---|---|---|---|
| AFF_afdb_06995_chunk01 | [0, 0, 0, 30] | [0, 0, 0, 30] | 4/4 PASS |
| ARR_mitdb_102_chunk00 | [0, 3, 27, 0] | [0, 3, 27, 0] | 4/4 PASS |
| CHF_chfdb_chf06_chunk06 | [0, 33, 0, 7] | [0, 33, 0, 7] | 4/4 PASS |
| NSR_nsrdb_16272_chunk03 | [17, 0, 6, 7] | [17, 0, 6, 7] | 4/4 PASS |

- 존재 파일 기준: **16/16 PASS**
- 요구한 36-case 기준: **16/144 — FAIL**

## 8. accepted sample, Snapshot 및 최종 판정 횟수

4개 모두 직접 통합과 새 replay 양쪽에서 다음을 만족했다.

- accepted samples: **1,800,000**
- Snapshots (`prof_windows`): **30**
- `final_valid`: asserted
- final decisions (`prof_decisions`): **1**

존재 파일 기준 4/4 PASS지만 전체 36-case 기준은 각 항목 **4/36 — FAIL**이다.

## 9. 기존 emulator 입력과 실제 XMODEL 입력의 차이

실제 XMODEL 4개 SHA는 해당 기존 emulator SHA와 **4/4 모두 다르다**. 전달 문서의 60초 36-window spot check에서도 XMODEL과 emulator의 표본 exact 일치율은 53.21%였다.

기존 emulator 입력 기반 Vivado 값과 비교하면 최종 클래스는 대표 4개에서 유지됐지만 membrane은 다음과 같다.

| case | 실제 XMODEL 기준 membrane | 기존 emulator/Vivado membrane | 동일 |
|---|---|---|---|
| AFF | [0, 0, 0, 30] | [0, 0, 0, 30] | 예 |
| ARR | [0, 3, 27, 0] | [0, 1, 29, 0] | 아니오 |
| CHF | [0, 33, 0, 7] | [0, 35, 2, 3] | 아니오 |
| NSR | [17, 0, 6, 7] | [24, 0, 4, 2] | 아니오 |

이 차이는 이번 실패 사유가 아니다. 이번 기능 비교는 같은 실제 XMODEL accepted code를 사용한 직접 통합과 새 Pure RTL replay 사이에서만 수행했다.

## 10. 최종 PASS/FAIL

**최종 FAIL**이다.

검증 가능한 실제 XMODEL 4개에 대해서는 핵심 가설이 성립했다. 즉 cadence가 달라도 동일 signed 12-bit code 순서를 고정 Pure RTL에 넣으면 직접 통합의 class와 네 Final Membrane이 bit-exact하게 재현됐다.

그러나 공식 PASS 기준은 입력 36/36, class 36/36, membrane 144/144, 각 case의 1.8M/30/1이다. 실제 XMODEL ADC가 32개 누락되어 결과는 각각 4/36, 4/36, 16/144, 4/36이므로 전체 PASS를 선언할 수 없다.

## 11. 남은 누락 또는 한계

1. `ADC_DATA_PROVENANCE_KR.md`에 열거된 32 case의 실제 XMODEL full-30분 accepted dump와 직접 통합 로그가 없다.
2. 재생성에는 원본 WFDB→PWL, XMODEL 2025.12, Questa/XMODEL 라이선스 환경이 필요하다. `prepare_pwl.py` 후 `optionB_gen_xmodel_chunks.sh` 또는 `run_e2e_all.sh`로 32개를 생성하고, 각 dump가 1,800,000 samples인지 검증한 뒤 같은 runner를 재실행해야 한다.
3. XSim elaboration에는 고정 RTL에 이미 존재하는 width/unconnected-port warning 5개가 있었다. RTL을 변경하지 않았으며 simulation은 정상 완료했다.
4. 공간이 포함된 현재 작업 경로 때문에 Xilinx WebTalk telemetry 종료 단계에서 path parsing 메시지가 발생했지만 snapshot은 이미 정상 build됐고 `xsim`은 return code 0으로 4-case를 완주했다. 기능 결과와 무관한 telemetry 메시지이며 `xsim.log`에는 simulation error/timeout이 없다.

## 산출물 색인

- `case_comparison_36case.csv`: 36개 사례별 직접 통합–replay 비교
- `overall_summary.csv`: 전체 PASS 기준 요약
- `input_sha256_manifest_36case.csv`: 입력 존재·표본·범위·SHA manifest
- `xsim_replay_results_present_cases.csv`: 실제 실행된 4개 XSim raw 결과
- `rtl_source_hash_manifest.csv`: 고정 digital commit source hash 검증
- `ADC_DATA_PROVENANCE_KR.md`: ADC 출처와 누락 목록
- `PASS_FAIL_SUMMARY_KR.md`: 짧은 판정 요약
- `xvlog.log`, `xelab.log`, `xsim.log`: Vivado/XSim 실행 로그
- `xsim_commands.txt`: 실행 명령
- `tools/verification/run_xmodel_adc_pure_rtl_replay.py`: 재현 runner
