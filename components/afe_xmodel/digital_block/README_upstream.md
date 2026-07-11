# AFE+ADC XMODEL 연동 SNN 기반 장시간 ECG 4-Class Classification Accelerator IP Core 설계

## 1. Abstract

본 프로젝트는 공개 digitized ECG record를 analog-equivalent `vin`으로 재구성하고, AFE+ADC XMODEL을 통과시켜 signed 12-bit ECG stream을 만든 뒤, 이를 SNN-inspired ECG Classification Accelerator IP Core에 입력하여 NSR/CHF/ARR/AFF를 분류하는 FPGA/VLSI engineering prototype이다.

디지털 분류기는 CNN/RNN/MLP처럼 weight memory와 MAC을 크게 쓰는 구조가 아니라, ECG domain event를 spike/counter evidence로 압축하고 60초 Snapshot Readout과 30분 Final Membrane Readout으로 장시간 evidence를 누적한다. 최종 모델은 `structural_guarded_silent_aff_1008710`이며, Snapshot Readout은 고정하고 Final Membrane만 strict record-wise train/validation 기준으로 lock했다.

본 repo는 raw electrode acquisition, physical AFE PCB measurement, ADC silicon measurement, Virtuoso post-layout 검증, clinical validation을 주장하지 않는다. 핵심 주장은 AFE+ADC XMODEL과 RTL/IP accelerator를 연결한 model-based mixed-signal-to-digital FPGA prototype이다.

## 2. System Flow

![Final system architecture](reports/final/figures/final_system_architecture.png)

```mermaid
flowchart LR
    A["Public digitized ECG record"] --> B["analog-equivalent vin reconstruction"]
    B --> C["AFE+ADC XMODEL"]
    C --> D["signed 12-bit ECG stream"]
    D --> E["60 s Snapshot SNN Readout"]
    E --> F["30 min Final Membrane Readout"]
    F --> G["NSR / CHF / ARR / AFF"]
    F --> H["RTL / XSim / Vivado / IP-XACT / Vitis board replay"]
```

입력은 공개 ECG database의 이미 digitized된 sample이다. 이 값을 `code / 200000` 기준의 voltage-equivalent waveform으로 해석하고, HPF, IA gain x201, 60 Hz notch, LPF 150 Hz, 12-bit ADC quantization으로 구성된 AFE+ADC XMODEL flow를 통과시킨다.

그 결과 생성된 signed 12-bit `.mem` stream이 RTL/IP의 실제 입력이 된다. 60초마다 Snapshot Readout이 event, rhythm, morphology, variability evidence를 만들고, 30개 snapshot을 Final Membrane Readout이 누적하여 최종 class를 출력한다.

## 3. Final Locked Model and Results

![Final result summary](reports/final/figures/final_result_summary.png)

| 항목 | 결과 |
|---|---:|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Train | 61 / 68 = 89.71% |
| Validation | 32 / 32 = 100.00% |
| Final test 30분 chunk | 29 / 36 = 80.56% |
| Final test 30분 chunk macro F1 / balanced accuracy | 80.44% / 80.56% |
| Final test 30분 chunk class recall | NSR 100.00%, CHF 66.67%, ARR 77.78%, AFF 77.78% |
| Final test record-majority | 16 / 19 = 84.21% |
| Final test record-majority macro F1 / balanced accuracy | 80.80% / 88.19% |
| Final test record-majority class recall | NSR 100.00%, CHF 75.00%, ARR 77.78%, AFF 100.00% |
| Test evaluation count | 1 |
| Test used for selection | false |

Validation 100.00%는 model-selection 성능으로만 해석한다. 최종 held-out 성능 주장은 locked final_test의 accuracy, macro F1, balanced accuracy, class별 recall을 기준으로 한다. Chunk 기준 weakest class는 CHF recall 66.67%이다.

## 4. Hardware Implementation

| 항목 | 결과 |
|---|---:|
| Locked final-layer XSim | final_pred mismatch 0, final_mem mismatch 0 over 36 final_test cases |
| Pure RTL Vivado | LUT 9719, FF 5038, BRAM 0, DSP 0, WNS 8.184 ns |
| Pure RTL estimated power | 0.099 W |
| OOC/profile Vivado | LUT 9905, FF 5769, BRAM 0, DSP 0, WNS 0.471 ns |
| MicroBlaze full replay system | LUT 12494, FF 8494, BRAM 16, DSP 3, setup WNS 0.097 ns |
| IP packaging | AXI accelerator IP + MMIO-to-AXIS sample feeder IP-XACT |
| Full-top RTL XSim final_test | 36 full-record cases, 29/36 = 80.56% |
| Board replay | strict final_test 36-case full-record batch, final_pred 36/36, final_mem exact 36/36 |

MicroBlaze system resource는 CPU, LMB/BRAM, UART, AXI interconnect, sample feeder, accelerator를 모두 포함한다. 따라서 pure RTL resource와 직접 비교하지 않고 integration proof로 분리해서 해석한다.

## 5. Repository Structure

| 경로 | 역할 |
|---|---|
| `FINAL_REPORT_KR.md` | 최종 보고서 본문 |
| `docs/PAPER_SUMMARY_KR.md` | 제출용 핵심 요약 |
| `docs/SYSTEM_ARCHITECTURE_KR.md` | AFE+ADC XMODEL 및 accelerator architecture |
| `docs/STRICT_RECORDWISE_PROTOCOL_KR.md` | strict record-wise locked model protocol |
| `docs/HARDWARE_VALIDATION_KR.md` | RTL/XSim/Vivado/IP/Vitis/board evidence |
| `docs/LIMITATIONS_KR.md` | 주장 범위와 한계 |
| `configs/final_submission_locked_model.json` | 최종 모델과 수치의 source of truth |
| `reports/final/` | final metrics, evidence summary, board replay transcript, figures |
| `rtl/`, `sim/` | 최종 RTL 및 simulation source |
| `ip_repo/` | packaged AXI accelerator 및 sample feeder IP |
| `vitis_apps/full_record_replay/` | MicroBlaze full-record replay application |
| `tools/` | 재현, figure 생성, consistency check script |

## 6. Limitations

- Source ECG는 public digitized record이며 raw analog acquisition이 아니다.
- `vin`은 analog-equivalent/PWL-equivalent reconstruction이며 원래 sensor waveform의 완전 복원이 아니다.
- AFE+ADC는 XMODEL/nominal model 기반이며 physical AFE PCB 또는 ADC silicon 측정이 아니다.
- CMOS/transistor-level layout 및 post-layout verification은 수행하지 않았다.
- Clinical diagnosis validation은 수행하지 않았으며, 본 결과는 engineering validation 범위에 머문다.
- Board replay는 strict final_test 36개 30분 case 전체에 대해 수행했지만, physical analog validation은 아니며 final_pred/final_mem exact match는 모두 36/36으로 보고한다.

## 7. Main Report Link

전체 최종 보고서는 [FINAL_REPORT_KR.md](FINAL_REPORT_KR.md)를 기준 문서로 본다. Figure source와 생성 목록은 [reports/final/figures/FIGURE_INDEX.md](reports/final/figures/FIGURE_INDEX.md)에 정리되어 있다.
