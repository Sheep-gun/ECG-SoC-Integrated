# Future Board Timing Package

Status: **PENDING_BOARD**. No USB/JTAG probing or board execution was performed.

The instrumented application uses existing 64-bit accelerator profile registers. `core_cycles` is the hardware last-decision counter; `system_cycles` is the total transaction counter. UART printing occurs after counters stop. The existing platform has no independent AXI Timer, so scope limitations remain explicit.

Build:

```powershell
python benchmarks/accelerator_benefit/board/build_instrumented_app.py
```

The local Vitis 2020.2 build was attempted but BSP generation failed because the installed toolchain lacks `microblazeeb-xilinx-elf/usr/lib/le/bs/m/libgloss.a`. See `build/build_status.json`.

Future execution after repairing the Vitis installation and connecting a Nexys A7-100T:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port COM5 --program
python benchmarks/accelerator_benefit/board/parse_board_benchmark.py
python benchmarks/accelerator_benefit/tools/generate_benchmark_artifacts.py
```

Dependencies: Python 3, NumPy, Pillow, and pyserial for the existing UART runner.
