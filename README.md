# SNN ECG 4-Class Classifier

본 저장소는 AFE+ADC를 거친 ECG stream을 입력으로 받아 NSR / CHF / ARR / AFF를
분류하는 SNN-inspired RTL classifier의 최종 정리본이다.

자세한 연구 배경, Holter 방식의 의학적 동기, 데이터셋 구성, AFE+ADC 변환,
Snapshot C24 구조, C01-C32 후보 탐색, Final Membrane Layer 설계, Python 등가모델,
RTL/XSim 검증, 합성 자원, 전력 산출 상태는 아래 최종 보고서에 정리했다.

```text
FINAL_REPORT_KR.md
```

## 최종 시스템 개요

```text
full-record ECG
-> AFE+ADC signed 12-bit stream
-> 60초 Snapshot C24 classifier
-> 30분 chunk-level snapshot vote membrane
-> record-level Final Membrane Layer
-> NSR / CHF / ARR / AFF 최종 판정
```

이 모델은 60초 ECG 하나를 환자 진단으로 단정하는 구조가 아니다. Holter ECG처럼 긴
ECG stream에서 반복적으로 발생하는 snapshot-level class evidence를 누적해 최종
class를 결정하는 계층형 SNN-inspired classifier이다.

## 핵심 결과

| 항목 | 결과 |
| --- | ---: |
| 60초 Snapshot C24 test accuracy | 193 / 240 = 80.42% |
| Final Membrane Python test accuracy | 30 / 36 = 83.33% |
| Final Membrane RTL/XSim test accuracy | 30 / 36 = 83.33% |
| Python-vs-XSim prediction mismatch | 0 / 136 |
| full RTL top resource | 20,256 LUT / 2,259 FF / DSP 0 / BRAM 0 |
| final membrane chain resource | 163 LUT / 157 FF / DSP 0 / BRAM 0 |

정량 전력 소모량은 아직 최종 측정하지 않았다. 현재 저장소에는 synthesis resource
결과만 남아 있으며, mW 단위 전력 보고는 Vivado implementation, clock constraint,
switching activity 기반 `report_power`가 추가로 필요하다.

## 최종 데이터셋

최종 검증 데이터셋:

```text
fullrec_afe_30min_annotation_valid_balanced/
```

구성:

| Split | NSR | CHF | ARR | AFF | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 17 | 17 | 17 | 17 | 68 |
| val | 8 | 8 | 8 | 8 | 32 |
| test | 9 | 9 | 9 | 9 | 36 |
| all | 34 | 34 | 34 | 34 | 136 |

원천 DB:

| Class | Source DB |
| --- | --- |
| NSR | MIT-BIH Normal Sinus Rhythm Database |
| CHF | BIDMC Congestive Heart Failure Database |
| ARR | MIT-BIH Arrhythmia Database |
| AFF | MIT-BIH Atrial Fibrillation Database |

## 주요 파일

```text
FINAL_REPORT_KR.md

rtl/
  final_membrane_layer.v
  record_level_final_membrane_layer.v
  snn_ecg_30min_final_top.v
  core/*.v

sim/
  tb_snn_ecg_30min_record_level_dataset.v

scripts/
  snapshot_c24_rtl_exact.py
  final_membrane_30min_recordwise_pipeline.py
  search_final_membrane_30min_recordwise.py
  search_final_membrane_30min_recordwise_recordlevel.py
  search_final_membrane_30min_recordwise_recordlevel_strict.py
  run_record_level_strict_xsim.py

results/final_membrane_30min_recordwise/
  no_oracle_record_level_strict_selected_params.json
  xsim_record_level_strict_*_metrics.json
  xsim_record_level_strict_*_predictions.csv
  python_vs_xsim_record_level_strict_compare.csv
  record_level_strict_rtl_xsim_report.md
  synth/final_membrane_resource_report.md
```

## XSim 재검증

test split 실행:

```powershell
python scripts/run_record_level_strict_xsim.py --split test
```

전체 split 실행:

```powershell
python scripts/run_record_level_strict_xsim.py --split all
```

정리 후 test split을 다시 실행했으며 결과는 다음과 같았다.

```text
test: 30 / 36 = 83.33%
Python-vs-XSim mismatch: 0 / 36
```

전체 보존 결과 기준 combined compare는 136 rows, mismatch 0이다.
