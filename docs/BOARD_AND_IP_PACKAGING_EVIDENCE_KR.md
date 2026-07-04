# Board and IP Packaging Evidence

## 1. IP packaging evidence

| Evidence | Path | Status |
|---|---|---|
| AXI accelerator RTL wrapper | `rtl/axi/snn_ecg_axi_lite_stream_top.v` | Done |
| AXI4-Lite + AXI4-Stream feeder | `rtl/axi/axi_lite_axis_sample_feeder.v` | Done |
| Accelerator IP-XACT | `ip_repo/snn_ecg_axi_accelerator/component.xml` | Done |
| Accelerator xgui | `ip_repo/snn_ecg_axi_accelerator/xgui/snn_ecg_axi_lite_stream_top_v1_0.tcl` | Done |
| Feeder IP-XACT | `ip_repo/axi_lite_axis_sample_feeder/component.xml` | Done |
| Feeder xgui | `ip_repo/axi_lite_axis_sample_feeder/xgui/axi_lite_axis_sample_feeder_v1_0.tcl` | Done |
| AXI wrapper smoke testbench | `sim/tb_snn_ecg_axi_smoke.v` | Done |
| Sample feeder smoke testbench | `sim/tb_axi_lite_axis_sample_feeder.v` | Done |

## 2. MicroBlaze smoke evidence

| Artifact | Path | Status |
|---|---|---|
| MicroBlaze bitstream | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.bit` | Present |
| XSA | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.xsa` | Present |
| Block design Tcl | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke_bd.tcl` | Present |
| Address report | `results/final_membrane_v2_snn/microblaze_smoke/reports/system_bd_address.rpt` | Present |
| XSDB MMIO transcript | `results/final_membrane_v2_snn/microblaze_smoke/xsdb_mmio_transcript.txt` | Present |
| UART C app | `sw/microblaze_smoke/src/main.c` | Source present |
| Vitis ELF/UART transcript | `results/final_membrane_v2_snn/microblaze_smoke/vitis_workspace/...elf`, `uart_transcript.txt` | TODO |

MicroBlaze smoke summary 기준:

| 항목 | 값 |
|---|---:|
| LUT / FF / BRAM / DSP | 12650 / 8746 / 16 / 3 |
| WNS / WHS | 0.185 ns / 0.037 ns |
| smoke samples | 16 |
| smoke snapshots | 2 |

BRAM/DSP는 accelerator core가 아니라 MicroBlaze/LMB/UART/system infrastructure가 포함된 system-level resource이다.

## 3. Board replay status

Done:

- Vivado board bitstream generation
- Nexys A7 programming report
- AXI/IP-XACT packaging
- MicroBlaze block design generation
- 16-sample deterministic smoke bit/XSA
- XSDB MMIO smoke transcript

Partial:

- MicroBlaze bare-metal C source exists
- Vitis toolchain 설치 전이라 ELF/UART transcript는 아직 없음

TODO:

- full 30분 record board replay
- UART/JTAG/DMA/DDR 기반 긴 stream feeder
- expected-vs-board CSV comparison
- cycles/sample board transcript

## 4. 안전한 보고 표현

> 현재 board-level evidence는 bitstream programming, packaged IP integration, MicroBlaze smoke system, XSDB MMIO smoke 수준이다. full 30분 ECG replay는 아직 수행하지 않았으며, Vitis toolchain 준비 후 UART bare-metal smoke와 full replay를 보강할 계획이다.
