# MicroBlaze SNN ECG Smoke

This smoke target validates the packaged `snn_ecg_axi_accelerator` as a
MicroBlaze-controlled IP with a small MMIO-to-AXIS sample feeder.

## Hardware Build

```powershell
python scripts\build_microblaze_smoke_system.py
```

Outputs:

- `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.bit`
- `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.xsa`
- routed timing/CDC/clock/DRC/IO reports under `reports/`

Smoke address map:

- `0x44a00000`: `snn_ecg_axi_accelerator`
- `0x44a10000`: `axi_lite_axis_sample_feeder`
- `0x40600000`: `axi_uartlite`
- `0x41200000`: `axi_intc`

## Bare-Metal App

The app in `src/main.c` prints `SNN_ECG_MB_SMOKE_PASS` or
`SNN_ECG_MB_SMOKE_FAIL` over UART. It checks:

- accelerator CONFIG/STATUS and TOTAL_SAMPLES
- feeder prefill, TLAST count, and TX count
- START/done/interrupt pending
- final prediction and final membranes against the profile-smoke golden
- profile accepted/windows/decisions counters

Golden for the deterministic 16-sample all-zero stream:

- `final_pred = 0`
- `final_mem_NSR/CHF/ARR/AFF = 2/2/0/0`
- `accepted = 16`, `windows = 2`, `decisions = 1`

Build status helper:

```powershell
python scripts\build_microblaze_smoke_app.py --check-tools
python scripts\build_microblaze_smoke_app.py
```

`xsct` and a MicroBlaze bare-metal GCC toolchain are required to produce the ELF.

## Program And Capture

After the ELF exists, program the board and capture UART:

```powershell
python scripts\run_microblaze_smoke_hardware.py --check
python scripts\run_microblaze_smoke_hardware.py --uart COM5
```

The UART transcript is written to:

```text
results/final_membrane_v2_snn/microblaze_smoke/uart_transcript.txt
```

## XSDB MMIO Fallback

If Vivado `xsdb` is available but Vitis/SDK is not installed, this fallback can
exercise the same accelerator and feeder registers over JTAG without an ELF:

```powershell
python scripts\run_microblaze_smoke_xsdb_mmio.py --check
python scripts\run_microblaze_smoke_xsdb_mmio.py
```

It writes a transcript to:

```text
results/final_membrane_v2_snn/microblaze_smoke/xsdb_mmio_transcript.txt
```

`JTAG_MMIO_SMOKE_PASS` validates the packaged accelerator, feeder, AXI-Lite,
AXI-Stream handoff, final registers, profile counters, and INTC pending bit via
XSDB memory accesses. It does not replace the UART C smoke, because it does not
build or execute the MicroBlaze ELF and does not validate UART stdout routing.
