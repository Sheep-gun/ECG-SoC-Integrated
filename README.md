# AFE+ADC XMODEL 연동 SNN 기반 장시간 ECG 4-Class Classification Accelerator IP Core 설계

## 개요

이 repo는 공개 digitized ECG record를 입력으로 사용하는 FPGA/VLSI engineering prototype이다. 공개 ECG record를 analog-equivalent `vin` waveform으로 재구성하고, AFE+ADC XMODEL flow를 통과시켜 signed 12-bit sample stream을 생성한 뒤, SNN-inspired RTL accelerator에서 NSR/CHF/ARR/AFF 4개 class를 분류한다.

디지털 분류기는 60초 Snapshot Readout과 30분 Final Membrane Readout으로 구성된다. 60초마다 ECG event/rhythm/morphology evidence를 만들고, 30분 동안 30개의 snapshot evidence를 class membrane에 누적한 뒤 WTA로 최종 class를 출력한다.

최종 locked model은 `structural_guarded_silent_aff_1008710`이다. Snapshot은 고정하고 Final Membrane만 strict record-wise train/validation 기준으로 lock했으며, final_test는 모델 선택이나 파라미터 탐색에 사용하지 않고 lock 이후 1회만 평가했다. 하드웨어 검증은 Python/XSim 일치, Vivado implementation, IP-XACT packaging, Vitis/MicroBlaze class-wise 30분 board replay까지 포함한다.

본 프로젝트는 직접 전극 측정, physical AFE board 측정, ADC silicon 측정, transistor-level layout 검증, 의료 진단 유효성 검증을 주장하지 않는다.

## 전체 시스템 Flow

```mermaid
flowchart LR
    A["공개 digitized ECG record"] --> B["Analog-equivalent vin reconstruction"]
    B --> C["AFE+ADC XMODEL"]
    C --> D["Signed 12-bit ECG stream"]
    D --> E["60초 Snapshot SNN Readout"]
    E --> F["30분 Final Membrane Readout"]
    F --> G["NSR / CHF / ARR / AFF"]
    F --> H["RTL / XSim / Vivado / IP-XACT / Vitis board replay"]
```

## Feature Evidence 요약

본 분류기는 내부가 보이지 않는 dense neural network가 아니다. 각 60초 snapshot은 ECG-oriented event block으로 구성되고, feature event는 integer class membrane에 signed weight로 누적된다.

| Feature block | 직관적 의미 | RTL 역할 |
|---|---|---|
| Adaptive event encoder + QRS LIF | ECG slope가 갑자기 크게 변하는 `strong_event`를 적분해 beat/QRS spike를 만든다. | downstream rhythm/morphology block의 기준이 되는 `beat_spike` 생성 |
| PNN rhythm predictor | 다음 beat가 이전 rhythm hypothesis가 예상한 위치에 들어오는지 확인한다. | 규칙/불규칙 rhythm에 대한 match/mismatch evidence 생성 |
| RDM variability neuron | 연속 RR interval이 얼마나 변하는지 측정한다. | beat-to-beat variability evidence 누적 |
| DSCR spike counter | waveform slope sign change와 유효 기울기 변화를 센다. | multiplier 없이 morphology complexity evidence 생성 |
| RAM peak accumulator | R-peak amplitude response를 threshold bank로 측정한다. | beat amplitude behavior를 integer evidence code로 변환 |
| Ectopic pair neuron | 단일 short/long RR이 아니라 early/late beat pair pattern을 본다. | ARR-like ectopic rhythm evidence 생성 |
| QRS MAF neuron | QRS width, complexity, energy, pre-QRS bump를 본다. | morphology abnormality evidence 생성 |
| RBBB-like QRS delay bank | wide QRS와 terminal activity를 conduction-delay proxy로 본다. | 반복되는 wide/terminal QRS evidence를 snapshot level에 추가 |
| Class score neurons | fixed signed feature weight를 NSR/CHF/ARR/AFF class membrane에 적용한다. | 60초 snapshot WTA output 생성 |
| Final Membrane Readout | 30개 snapshot output과 evidence counter를 누적한다. | locked 30분 final WTA output 생성 |

Feature별 상세 직관 설명은 `FINAL_REPORT_KR.md`와 `docs/SYSTEM_ARCHITECTURE_KR.md`에 정리되어 있다.

## 최종 Locked 모델 및 결과

| 항목 | 결과 |
|---|---|
| 최종 모델 | `structural_guarded_silent_aff_1008710` |
| 프로토콜 | fully blind strict record-wise locked final holdout |
| Train | 61/68 = 89.71% |
| Validation | 32/32 = 100.00% |
| Final test 30분 청크 | 29/36 = 80.56% |
| Final test record-majority | 16/19 = 84.21% |
| Test evaluation count | 1 |
| Test used for selection | No |

Validation 100%는 model-selection 단계의 결과이며, 최종 일반화 성능 주장은 locked final_test 결과를 기준으로 한다.

## 하드웨어 구현 및 검증

| 항목 | 결과 |
|---|---|
| Locked final-layer XSim | 36개 final_test case에서 final_pred mismatch 0, final_mem mismatch 0 |
| Pure RTL Vivado | LUT/FF/BRAM/DSP 9719/5038/0/0, WNS 8.184 ns, power estimate 0.099 W |
| OOC/profile Vivado | LUT/FF/BRAM/DSP 9905/5769/0/0, WNS 0.471 ns |
| IP packaging | AXI accelerator IP와 MMIO-to-AXIS sample feeder IP-XACT package |
| MicroBlaze full replay build | bitstream/XSA/ELF 생성, timing met |
| Board replay | NSR/CHF/ARR/AFF 각 1개 30분 case, final_pred/final_mem exact 4/4 |

Board replay evidence는 `reports/final/board_replay_result.md`에 요약되어 있으며, raw UART transcript와 comparison CSV는 `reports/final/board_replay/` 아래에 있다.

## Repo 구조

| 경로 | 역할 |
|---|---|
| `FINAL_REPORT_KR.md` | 한국어 최종 보고서 |
| `docs/PAPER_SUMMARY_KR.md` | 제출용 짧은 요약 |
| `docs/SYSTEM_ARCHITECTURE_KR.md` | AFE+ADC XMODEL 및 accelerator architecture |
| `docs/STRICT_RECORDWISE_PROTOCOL_KR.md` | locked dataset/model protocol |
| `docs/HARDWARE_VALIDATION_KR.md` | RTL/XSim/Vivado/IP/Vitis 검증 evidence |
| `docs/LIMITATIONS_KR.md` | 주장 범위와 한계 |
| `configs/final_submission_locked_model.json` | 최종 모델, 수치, 주장 범위 source of truth |
| `reports/final/` | 최종 metrics, evidence summary, figure, board replay transcript |
| `rtl/`, `sim/` | 최종 RTL 및 simulation source |
| `ip_repo/` | packaged AXI accelerator 및 sample feeder IP source |
| `vitis_apps/full_record_replay/` | MicroBlaze full-record replay application |
| `tools/` | 최종 재현 및 consistency check script |

## 한계

- Source ECG record는 이미 digitized public dataset이다.
- `vin`은 analog-equivalent/PWL-equivalent reconstruction이며, 원래 sensor waveform을 복원한 것이 아니다.
- AFE+ADC 검증은 XMODEL/nominal-model 기반이며, board-level AFE 또는 ADC silicon 측정이 아니다.
- Transistor-level layout 검증은 주장하지 않는다.
- 의료 진단 유효성 검증은 주장하지 않는다.
- Board replay는 class별 대표 30분 case 검증이며, 모든 final_test case의 full board batch replay는 아니다.

## 최종 보고서

전체 한국어 최종 보고서는 `FINAL_REPORT_KR.md`를 보면 된다.
