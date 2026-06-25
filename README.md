# SNN ECG Model S RTL Classifier

SNN-inspired ECG 4-class RTL classifier 프로젝트입니다. ECG 원파형을 1 kSPS, signed 12-bit stream으로 입력받아 NSR / CHF / ARR / AFF 네 클래스를 분류합니다.

이 저장소는 최종 채택된 Model S RTL, strict record-wise 검증 자료, Nexys A7 FPGA smoke test 자료, AFE/mixed-signal 연동 문서를 한 곳에 정리한 GitHub 배포용 패키지입니다.

## 최종 모델

**Model S = Model A+ + EERG**

Model A+는 Model A에 RBBB QRS Delay Bank를 추가한 구조이고, EERG는 Episodic Ectopic Rescue Gate입니다. EERG는 PAC 전용 검출기가 아니라, 경계성 또는 간헐성 ectopic ARR segment를 보조적으로 구제하는 readout gate로 해석합니다.

활성 feature 경로는 다음과 같습니다.

~~~text
1 kSPS signed 12-bit ECG adc_data
-> event encoder
-> QRS LIF detector
-> pNN125 / RDM / DSCR / RAM / ECP / QRS MAF / RBBB evidence
-> 60초 local class neuron membrane
-> segment-level class membrane 누적
-> RBBB/EERG readout 보강
-> 4-class WTA
-> pred_class
~~~

분류기는 fixed signed synaptic weight, counter, comparator, shift/add 기반으로 구현됩니다. DSP multiplier, floating point, STDP, backpropagation은 사용하지 않습니다.

## Strict Record-Wise RTL 검증 결과

| split | segment accuracy | record accuracy | macro-F1 | balanced accuracy |
|---|---:|---:|---:|---:|
| train | 313/400 = 78.25% | 41/50 = 82.00% | 78.19% | 78.25% |
| validation | 136/160 = 85.00% | 18/20 = 90.00% | 84.91% | 85.00% |
| test | 131/160 = 81.88% | 18/19 = 94.74% | 81.93% | 81.88% |

### Test Class별 결과

| class | correct / total | recall |
|---|---:|---:|
| NSR | 31/40 | 77.50% |
| CHF | 37/40 | 92.50% |
| ARR | 28/40 | 70.00% |
| AFF | 35/40 | 87.50% |

### Test Segment Confusion Matrix

| Actual \ Pred | NSR | CHF | ARR | AFF |
|---|---:|---:|---:|---:|
| NSR | 31 | 0 | 9 | 0 |
| CHF | 0 | 37 | 3 | 0 |
| ARR | 6 | 0 | 28 | 6 |
| AFF | 0 | 3 | 2 | 35 |

### Test Record Confusion Matrix

| Actual \ Pred | NSR | CHF | ARR | AFF |
|---|---:|---:|---:|---:|
| NSR | 3 | 0 | 0 | 0 |
| CHF | 0 | 3 | 0 | 0 |
| ARR | 0 | 0 | 8 | 1 |
| AFF | 0 | 0 | 0 | 4 |

## FPGA 검증

Nexys A7-100T 보드에서 board smoke top을 통해 버튼 기반 예시 segment 입력 및 7-segment 결과 표시를 검증했습니다.

- Top module: `nexys_a7_model_s_smoke_top`
- Device: `xc7a100tcsg324-1`
- Timing: WNS 4.242 ns, failing endpoints 0
- Power estimate: 0.104 W
- DRC violation: 0

Board smoke design은 데모용 wrapper와 예시 segment ROM을 포함하므로 BRAM/IO 사용량은 실제 classifier core resource와 다릅니다. 최종 자원 평가는 core 기준 보고서를 우선합니다.

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `SNN_ECG.srcs/` | Vivado source tree 형식 RTL, testbench, constraints |
| `rtl/` | 주요 RTL 파일 모음 |
| `sim/` | strict record-wise testbench 및 board smoke testbench |
| `constraints/` | Nexys A7 XDC |
| `scripts/` | XSim, synthesis, Vivado 재생성 스크립트 |
| `reports/` | 최종 Model S metric, synthesis, FPGA 검증 보고서 |
| `datasets/` | strict split 증빙 및 데모용 segment 자료 |
| `docs/` | 구조, feature, 데이터셋, FPGA, AFE 문서 |
| `analog/` | AFE/mixed-signal 연동 자료 |
| `bitstreams/` | Nexys A7 board smoke bitstream |
| `vivado_project/` | 재생성된 통합 Vivado 프로젝트 |

## Vivado 사용

Vivado 2020.2 기준으로 다음 프로젝트를 열 수 있습니다.

~~~text
vivado_project/SNN_ECG_ModelS_Unified/SNN_ECG_ModelS_Unified.xpr
~~~

보드 데모 bitstream은 다음 위치에 있습니다.

~~~text
bitstreams/nexys_a7_model_s_smoke_top.bit
~~~

## 핵심 문서

- [전체 구조](docs/architecture.md)
- [Feature neuron 설명](docs/feature_neurons.md)
- [데이터셋 및 평가 방식](docs/dataset_and_evaluation.md)
- [FPGA 검증 보고](docs/fpga_verification.md)
- [AFE 및 mixed-signal 연동](docs/analog_mixed_signal.md)
- [재현 절차](docs/reproduction.md)
- [최종 의사결정](docs/final_decisions.md)

## 라이선스 및 데이터 주의

이 저장소는 대회 제출 및 팀 협업용 기술 정리 저장소입니다. 외부 공개 시 ECG 원본 데이터의 출처, 라이선스, 재배포 가능 여부를 별도로 확인해야 합니다.
