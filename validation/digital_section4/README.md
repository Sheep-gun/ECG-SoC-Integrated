# Section 4 digital and integration verification evidence

This directory collects report-facing evidence for the contest application's
Section 4, **design-circuit verification**.  Classification accuracy belongs to
Section 5; the evidence here answers whether the implemented digital circuit
reproduces its locked references and whether its control and interfaces work.

## Evidence map

| Item | Verification question | Report artifact | Primary evidence |
|---|---|---|---|
| 2-1 | Does RTL reproduce the locked Python integer reference at the final output? | `tables/section4_digital_validation_summary.md` | `components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv` |
| 2-2 | Does the independent Exact C++ implementation reproduce fixed-width arithmetic and internal states? | `figures/final/VAL-02A_multilevel_digital_equivalence.svg` | `benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json` |
| 2-3 | Does the full top accept the complete stream, create 30 Snapshots, and issue one final decision? | `figures/final/VAL-02B_fulltop_control_timeline.svg` | `components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` |
| 2-4 | Do the AXI-Lite registers and AXI-Stream handshake/backpressure paths behave correctly? | `figures/final/VAL-02C_axi_ip_protocol_waveform.svg` | `axi_ip/logs/*.log`, `axi_ip/traces/*.json` |
| 3-1--3-3 | Is the XMODEL signed stream byte-identical at handoff, and are the final RTL prediction/membranes identical? | `tables/section4_integration_validation_summary.md` | `components/afe_xmodel/docs/integration_latest/*.csv` |

## AXI/IP rerun

Run from PowerShell:

```powershell
.\validation\digital_section4\axi_ip\run_axi_ip_validation.ps1
```

The script compiles the packaged IP RTL and its smoke testbenches with Vivado
2020.2 XSim, checks the PASS markers, captures VCD evidence in a temporary build
directory, and commits only compact selected-signal traces plus logs.  The raw
VCD/WDB files are intentionally excluded because they are regenerable build
products.

The accelerator smoke test uses reduced `SNAPSHOT_SAMPLES=8` and
`SNAPSHOTS_PER_CHUNK=2` so interface behavior can be exercised quickly.  The
canonical 1,800,000-sample, 30-Snapshot behavior is separately proven by the
36-case full-top XSim regression used for item 2-3.
