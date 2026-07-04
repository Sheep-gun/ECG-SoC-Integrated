# Final Submission Figure Index

이 폴더는 최종 제출 문서에 넣을 핵심 figure를 모아 두거나, Mermaid diagram이 들어 있는 원문 문서를 가리킨다.

## 1. 복사된 PNG figure

| figure | source | 역할 |
|---|---|---|
| `afe_vin_reconstruction.png` | `reports/award_readiness/figures/afe_vin_reconstruction.png` | analog-equivalent `vin` reconstruction evidence |
| `afe_chain_waveform.png` | `reports/award_readiness/figures/afe_chain_waveform.png` | AFE+ADC XMODEL waveform flow |
| `afe_frequency_response.png` | `reports/award_readiness/figures/afe_frequency_response.png` | HPF/notch/LPF frequency response |
| `notch_60hz_effect.png` | `reports/award_readiness/figures/notch_60hz_effect.png` | 60 Hz notch effect |
| `adc_quantization_hist.png` | `reports/award_readiness/figures/adc_quantization_hist.png` | 12-bit ADC quantization distribution |
| `afe_on_off_comparison.png` | `reports/award_readiness/figures/afe_on_off_comparison.png` | model-stage comparison figure |
| `ablation_accuracy_bar.png` | `reports/award_readiness/figures/ablation_accuracy_bar.png` | full/final/snapshot ablation comparison |

## 2. Mermaid diagram source

아래 diagram은 별도 PNG를 새로 만들지 않고 Markdown 문서 안의 Mermaid source를 유지한다. 실제 생성되지 않은 이미지 파일을 evidence처럼 보이지 않게 하기 위한 처리이다.

| diagram | document |
|---|---|
| Overall system flow | `README.md`, `docs/FINAL_SUBMISSION_SUMMARY_KR.md` |
| SNN Accelerator IP architecture | `docs/Accelerator IP Core.md` |
| Board full-record replay flow | `docs/FULL_RECORD_BOARD_REPLAY_RESULT_KR.md`, `docs/FULL_RECORD_BOARD_REPLAY_VITIS_KR.md` |
| Expected-vs-board result table | `reports/final_submission/board_replay_final_summary.md` |

## 3. 해석 경계

AFE figure는 nominal XMODEL evidence figure이며, physical PCB/silicon/post-layout measurement plot이 아니다.
