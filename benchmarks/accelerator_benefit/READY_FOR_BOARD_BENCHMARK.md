# Board Benchmark Completion Record

Status: **COMPLETED**, Nexys A7-100T, `COM8`, 230400 baud.

## Immutable artifacts

- BIT `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`: `61dfb3dddee1f55b9e2ce42009cb9693bb1c8ff9c7b65b71f0d59d6b2a34dd58`
- XSA `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`: `8ff2a1ed537c27bd6d8117313c274aa79de8f11b4e6df54fa1b9fa10ca5942a3`
- instrumented ELF `benchmarks/accelerator_benefit/board/build/snn_ecg_mb_full_replay_benchmark.elf`: `c61d53e33fb9824f1b6bdc27e14ce7209a9d377b271ec398fa91da0c52a05b16`
- dataset manifest: `4965b8a098617d6138e4e56e2b45febda20706b031e9bbaa2558d874517dee72`
- locked config: `3ed5fa3399b99cace22a5cd7821be2c598a58ef27012da11a4e213a0f4c5672d`
- locked parameter file: `e0c1a649515ea50bbccc7c72d2dada9080c136e9d0e23de84dcc07f93744ae53`

## Acceptance

- completed: 36/36
- samples: 1,800,000 per case
- snapshots/decisions: 30/1 per case
- board vs Golden final prediction: 36/36
- board vs Golden Final Membrane: 144/144 values
- annotation accuracy: 29/36 (80.56%)
- every transcript: exactly one `BOARD_BENCH` and one board PASS marker
- every core/system counter: greater than zero
- active-core metric: `profile_total - profile_input_wait` = 3601290 cycles = 36.012900 ms in 36/36 cases
- Exact C++ kernel / FPGA active-core speedup: 49.362862x
- integrated-system compute latency/speedup/energy: not measured; requires preloaded input and an independent timer

Raw evidence is in `benchmarks/accelerator_benefit/board/future_run`. Use `--resume` only after a transport interruption; completed transcript/parsed pairs are retained. The immutable UARTLite configuration is 230400 baud.
