# Section 4 digital verification summary

This table is the compact result source for items 2-1 through 2-4.  It reports implementation equivalence and control/interface behavior, not classification accuracy.

| Item | Scope and method | Result | Judgment | Primary evidence |
|---|---|---:|---|---|
| 2-1 Python integer reference vs RTL/XSim | Same locked 36-case inputs; compare final class and four Final Membranes | Prediction 36/36; membrane 144/144; mismatch 0 | PASS | `components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv` |
| 2-2 Exact C++ vs RTL/XSim internal state | Exhaustive fixed-width primitives, module microtraces, accepted-sample state hashes, Snapshot boundaries, final outputs | Fixed-width 793,595/793,595; microtrace 18/18; states 240000/240000; Snapshot 1080/1080; prediction 36/36; membrane 144/144 | PASS | `benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json` |
| 2-3 Full-top control flow | 36 complete XSim cases; verify `final_valid`, accepted samples, Snapshot count, and decision count | 36/36; 1,800,000 samples, 30 Snapshots, 1 decision per case; 5,401,260 profiled cycles | PASS | `components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` |
| 2-4 AXI/IP packaging and interface | Rerun packaged accelerator and sample-feeder IP smoke tests in Vivado XSim 2020.2 | 2/2 testbenches PASS; AXI-Lite read/write, AW/W skew, stalled-read stability, AXI-Stream backpressure/TLAST, counters, error clear, done/IRQ | PASS | `validation/digital_section4/axi_ip/axi_ip_smoke_summary.json`; `validation/digital_section4/axi_ip/logs/*.log` |

Notes:

- Exact C++ is an independent handwritten cross-check.  The locked Python integer model and canonical full-top XSim remain the reference/implementation authority for the final design.
- The accelerator smoke test uses a reduced 16-sample, two-Snapshot configuration to exercise the interface quickly; the canonical 1,800,000-sample, 30-Snapshot control flow is covered by item 2-3.
- XSim elaboration retained five pre-existing locked-RTL warnings (four 4-bit-to-8-bit port-width warnings and one unconnected `strong_event` port).  Both testbenches completed with zero smoke-test failures; the warnings are preserved in the log rather than hidden.
