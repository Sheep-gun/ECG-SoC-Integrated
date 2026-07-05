# Repo Final Audit

## 1. 조사 범위

이 문서는 제27회 전국 반도체 설계대전 제출 직전 기준으로 `SNN-ECG-4-Class-Classifier` repo에 실제로 존재하는 구현, 검증 결과, 산출물, 그리고 아직 TODO인 항목을 분리해 정리한 최종 감사 요약이다.

## 2. 현재 프로젝트 포지션

현재 repo에서 근거를 확인할 수 있는 프로젝트 포지션은 다음과 같다.

```text
public digitized ECG records
-> analog-equivalent / PWL-equivalent vin reconstruction
-> nominal AFE+ADC XMODEL
-> signed 12-bit .mem stream
-> SNN-inspired ECG Classification Accelerator IP Core
-> Python/XSim/Vivado/IP packaging/Vitis board replay validation
-> NSR / CHF / ARR / AFF classification
```

즉 본 프로젝트는 raw analog ECG acquisition, 실제 전극 측정, physical AFE PCB 검증, ADC silicon measurement, Virtuoso post-layout verification, clinical validation을 완료한 프로젝트가 아니다. 제출 문서에서는 이 경계를 반드시 유지해야 한다.

## 3. 확인된 핵심 결과

| 항목 | 현재 확인된 근거 |
|---|---|
| Chunk-level test accuracy | `results/final_membrane_v2_snn/xsim_snn_ecg_v2_summary.json` 기준 `32/36 = 88.89%` |
| Python-vs-XSim mismatch | final prediction `0/136`, final membrane `0/136` |
| Strict record-wise dataset | seed `20260808`, source/physical overlap 0, class별 train/validation/test chunks `17/8/9` |
| Final Membrane selection protocol | strict train/validation에서 parameter 선택, lock 이후 strict test 최종 1회 평가 |
| Ablation full model | `125/136 = 91.91%` |
| Ablation snapshot majority | `103/136 = 75.74%` |
| Ablation snapshot membrane sum | `101/136 = 74.26%` |
| Ablation feature_sum_zeroed | `84/136 = 61.76%` |
| Vivado board wrapper | LUT/FF/BRAM/DSP `21002 / 2803 / 0 / 0`, WNS `7.873 ns`, estimated power `0.101 W` |
| AXI wrapper OOC | LUT/FF/BRAM/DSP `10773 / 6931 / 0 / 0`, WNS `0.081 ns` |
| MicroBlaze smoke | LUT/FF/BRAM/DSP `12650 / 8746 / 16 / 3`, WNS `0.185 ns`, UART PASS transcript 존재 |
| Full-record board replay system | LUT/FF/BRAM/DSP `12638 / 8745 / 16 / 3`, WNS/WHS `0.192 ns / 0.026 ns` |
| Full-record board replay result | test NSR case 0, `1,800,000` samples, board PASS, expected-vs-board exact match |

## 4. AFE+ADC XMODEL evidence

| 항목 | 현재 확인된 근거 |
|---|---|
| Input scaling | `vin_v = signed_code / 200000` |
| Model chain | HPF `0.482 Hz` -> IA gain `x201` -> 60 Hz notch -> LPF `150 Hz` -> 12-bit ADC |
| Evidence figures | `reports/award_readiness/figures/afe_chain_waveform.png`, `afe_frequency_response.png`, `afe_vin_reconstruction.png`, `adc_quantization_hist.png`, `notch_60hz_effect.png`, `afe_on_off_comparison.png` |
| 한계 | 사용 가능한 signed `.mem` data와 nominal AFE model 기반 figure이며, PCB/silicon/transistor-level post-layout proof가 아님 |

## 5. Vitis/MicroBlaze full-record board replay

| 항목 | 값 |
|---|---|
| Vitis app | `vitis_apps/full_record_replay/src/main.c` |
| PC sender | `tools/board_replay/send_full_record_uart.py` |
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| Transcript | `reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt` |
| Comparison CSV | `reports/board_replay/comparisons/test_case0_nsr_expected_vs_board.csv` |
| Summary | `reports/board_replay/comparisons/test_case0_nsr_summary.md` |
| PASS marker | `SNN_ECG_FULL_REPLAY_BOARD_PASS` |

Board replay raw result:

| Metric | Expected | Board | Match |
|---|---:|---:|---:|
| samples_received | 1,800,000 | 1,800,000 | 1 |
| samples_sent_to_ip | 1,800,000 | 1,800,000 | 1 |
| samples_accepted | 1,800,000 | 1,800,000 | 1 |
| samples_consumed | 1,800,000 | 1,800,000 | 1 |
| snapshot_count | 30 | 30 | 1 |
| decision_count | 1 | 1 | 1 |
| final_valid | 1 | 1 | 1 |
| done | 1 | 1 | 1 |
| final_pred | 0 | 0 | 1 |
| final_mem_NSR/CHF/ARR/AFF | 31 / 0 / 1 / 0 | 31 / 0 / 1 / 0 | 1 |
| snn_error / feeder_error | 0 / 0 | 0 / 0 | 1 |

## 6. 확인한 register map

| Block | Base | 주요 register |
|---|---:|---|
| SNN accelerator | `0x44A00000` | `CONTROL 0x000`, `STATUS 0x004`, `TOTAL_SAMPLES 0x010`, `SAMPLES_ACCEPTED 0x014`, `SAMPLES_CONSUMED 0x018`, `FINAL_MEM_* 0x020..0x02c`, `FINAL_PRED 0x030`, `PROFILE_WINDOWS 0x128`, `PROFILE_DECISIONS 0x130` |
| Sample feeder | `0x44A10000` | `CONTROL 0x00`, `STATUS 0x04`, `SAMPLE 0x10`, `WRITE_COUNT 0x14`, `TX_COUNT 0x18`, `TLAST_COUNT 0x1c` |
| UARTLite | `0x40600000` | MicroBlaze console 및 raw sample transport |
| AXI INTC | `0x41200000` | accelerator done IRQ |

## 7. 남은 TODO

- Non-NSR full-record board replay case.
- Full test split board replay batch.
- AXI DMA/DDR 기반 고속 replay 및 throughput 측정.
- Board-level current/power measurement.
- AFE-off 및 filter-off regenerated full-record `.mem` accuracy.
- Physical AFE PCB / ADC silicon / post-layout verification.
- Strict record-wise protocol을 먼저 고정한 뒤 model/rule search 재수행.

## 8. 피해야 할 과장 표현

- Raw analog ECG acquisition 또는 recovery.
- Actual ECG electrode measurement.
- Physical DAC replay.
- Actual AFE PCB 또는 ADC silicon measurement.
- Virtuoso post-layout verification.
- Clinical diagnosis validation.
- Strict record-wise final accuracy.
- Full dataset board replay completion.
