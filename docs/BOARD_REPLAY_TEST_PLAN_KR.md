# Board Replay Test Plan

## 1. 목표

현재 repo에는 MicroBlaze smoke bit/XSA, XSDB MMIO transcript, Vitis-built bare-metal ELF, UART PASS transcript가 있다. 다음 단계는 실제 30분 ECG stream을 board에서 replay하고, Python/XSim expected result와 board register output을 비교하는 것이다.

## 2. 권장 단계

```text
PC
-> JTAG/XSDB 또는 UART loader
-> AXI-Lite sample feeder register
-> AXI-Stream ADC sample
-> SNN ECG Accelerator IP
-> STATUS / final_pred / final_mem registers
-> expected-vs-board comparison
```

## 3. 최소 smoke

1. Vitis 2020.2 설치
2. `python scripts\build_microblaze_smoke_app.py --check-tools`
3. `python scripts\build_microblaze_smoke_app.py`
4. `python scripts\run_microblaze_smoke_hardware.py --check`
5. `python scripts\run_microblaze_smoke_hardware.py --uart COMx`

산출물:

- MicroBlaze ELF
- UART transcript
- PASS/FAIL line
- register dump

## 4. full replay 계획

필요 산출물:

- `board_replay_input.mem`
- `expected_result.json`
- `board_transcript.txt`
- `expected_vs_board.csv`
- final class match
- final membrane match 또는 tolerance-free exact match
- cycles/sample board counter

## 5. 현재 제한

Vitis/MicroBlaze GCC 기반 bare-metal smoke는 완료되었고 `uart_transcript.txt`에 `SNN_ECG_MB_SMOKE_PASS`가 남아 있다. 다만 현재 sample feeder는 smoke에 적합한 MMIO feeder이며, full 1.8M sample replay에는 속도/automation 보강이 필요하다.
