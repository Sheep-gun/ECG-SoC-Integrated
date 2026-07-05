# Board Replay Test Plan

## 1. 현재 상태

repo에는 세 단계의 board evidence가 있다.

| 단계 | 상태 | 주요 evidence |
|---|---|---|
| 16-sample smoke | 완료 | `results/final_membrane_v2_snn/microblaze_smoke/uart_transcript.txt` |
| JTAG/MMIO smoke | 완료 | `results/final_membrane_v2_snn/microblaze_smoke/xsdb_mmio_transcript.txt` |
| 30분 full-record replay 1건 | 완료 | `reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt` |

full-record replay는 Vitis MicroBlaze bare-metal app과 PC UART sender를 사용한다. 입력은 physical AFE/ADC가 아니라 AFE+ADC XMODEL 이후 생성된 signed 12-bit `.mem`이다.

상세 구현과 실행 결과는 [FULL_RECORD_BOARD_REPLAY_VITIS_KR.md](FULL_RECORD_BOARD_REPLAY_VITIS_KR.md)에 정리했다.

## 2. Replay 구조

```text
PC .mem sender
-> UART raw_i16le chunk stream
-> MicroBlaze bare-metal full_record_replay app
-> AXI-Lite sample feeder SAMPLE register
-> AXI4-Stream sample + TLAST
-> SNN ECG Accelerator IP
-> final_pred / final_mem / profile counter readback
-> UART transcript
-> Python/XSim expected comparison
```

단순 raw UART push는 RX FIFO overrun 위험이 있어 최종 flow는 4096-sample chunk ACK 방식으로 고정했다.

## 3. 실행 명령

```powershell
python scripts\build_microblaze_full_replay_system.py --skip-package
python scripts\build_microblaze_full_replay_app.py
python tools\board_replay\send_full_record_uart.py `
  --program `
  --uart COM8 `
  --mem fullrec_afe_30min_annotation_valid_balanced\test\NSR\16786\16786_30min_w035.mem `
  --case-id 0 `
  --case-name test_case0_nsr `
  --ready-timeout 90 `
  --ack-timeout 60 `
  --done-timeout 600
```

## 4. 완료된 full-record replay 결과

| 항목 | 결과 |
|---|---:|
| samples_received | 1,800,000 |
| samples_sent_to_ip | 1,800,000 |
| samples_accepted | 1,800,000 |
| samples_consumed | 1,800,000 |
| snapshot_count | 30 |
| decision_count | 1 |
| final_pred | 0 |
| final_mem NSR/CHF/ARR/AFF | 31 / 0 / 1 / 0 |
| snn_error / feeder_error | 0 / 0 |
| board marker | legacy `SNN_ECG_FULL_REPLAY_BOARD_PASS`, not locked result |
| expected-vs-board | legacy PASS, locked comparison pending |

비교 산출물:

- legacy: `reports/board_replay/comparisons/test_case0_nsr_expected_vs_board.csv`
- locked target: `reports/board_replay/comparisons/locked_model_expected_vs_board.csv`
- `reports/board_replay/comparisons/test_case0_nsr_summary.md`
- `reports/board_replay/comparisons/test_case0_nsr_expected_result.json`

## 5. 남은 검증 계획

현재 locked model 기준 full replay 완료 범위는 bitstream/XSA/ELF build까지이다. actual UART full-record replay transcript와 expected-vs-board comparison은 새 locked bitstream으로 다시 생성해야 한다.

우선순위:

1. non-NSR full board replay 1건 추가
2. test split 대표 case batch replay
3. UART replay time과 profile counter 정리
4. AXI DMA/DDR 기반 faster replay 검토
5. board-level current/power 측정

UART replay는 board integration evidence이며 real-time throughput 검증은 아니다. 물리 AFE/ADC 검증도 아니므로 physical analog validation과는 구분해서 보고해야 한다.
