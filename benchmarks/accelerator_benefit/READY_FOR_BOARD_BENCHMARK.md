# READY FOR BOARD BENCHMARK

Status: **PENDING_BOARD**; deterministic package prepared in NO_BOARD mode.

## 1. Hardware

Nexys A7-100T, USB/JTAG cable, board power, and USB-UART serial connection.

## 2. Software

Vivado/Vitis 2020.2, Digilent cable/UART drivers, Python 3 with NumPy, Pillow, and pyserial.

## 3. Immutable artifacts

- BIT `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`: `61dfb3dddee1f55b9e2ce42009cb9693bb1c8ff9c7b65b71f0d59d6b2a34dd58`
- XSA `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`: `8ff2a1ed537c27bd6d8117313c274aa79de8f11b4e6df54fa1b9fa10ca5942a3`
- existing ELF `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf`: `5bb947f62a322765f79b6bf013da0d70b4c068165b1faaccd59c41264b7e05c3` (functional replay only)
- instrumented ELF: **PENDING_BUILD** after repairing missing Vitis `libgloss.a`
- dataset manifest: `4965b8a098617d6138e4e56e2b45febda20706b031e9bbaa2558d874517dee72`
- locked config: `3ed5fa3399b99cace22a5cd7821be2c598a58ef27012da11a4e213a0f4c5672d`
- locked params file: `e0c1a649515ea50bbccc7c72d2dada9080c136e9d0e23de84dcc07f93744ae53`

## 4. Programming

Repair/reinstall the MicroBlaze Vitis 2020.2 libraries, run:

```powershell
python benchmarks/accelerator_benefit/board/build_instrumented_app.py
```

Then connect one board and run:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port COM5 --program
```

The launcher uses the existing 36-case manifest and programs the immutable BIT plus the newly built instrumented ELF. No model or RTL change is required during execution.

## 5. UART/host command

Replace `COM5` only with the enumerated USB-UART port. Baud is 115200 by default.

## 6. Exact 36-case procedure

Run the launcher once. Do not change cases, cadence, samples, or expected outputs. Use `--resume` only after a transport interruption.

## 7. Transcript schema

Each case must contain exactly one `BOARD_BENCH` line matching `board/transcript_example.txt`, followed by the existing PASS marker.

## 8. Parser

```powershell
python benchmarks/accelerator_benefit/board/parse_board_benchmark.py
```

## 9. Acceptance

36/36 completed; 1,800,000 samples each; 30 snapshots; one decision; final_pred 36/36; final_mem 36/36; nonzero hardware timer cycles for every case.

## 10. Generated files

`board/future_run/transcripts/*.txt`, `board/future_run/parsed/*.json`, `board/board_timing_results.csv`, and updated comparison/figure/report outputs.

## 11. Regeneration

```powershell
python benchmarks/accelerator_benefit/tools/generate_benchmark_artifacts.py
python benchmarks/accelerator_benefit/tools/check_benchmark_integrity.py
```
