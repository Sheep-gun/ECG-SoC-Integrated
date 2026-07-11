# Accelerator-benefit benchmark

Status: `PENDING_EXTERNAL_BENCHMARK_IMPORT`

The accelerator-benefit benchmark is being completed independently. No integrated latency, throughput, speedup, power, or energy conclusion is available yet.

Future import must verify:

- benchmark repository URL and fixed commit
- input artifact hashes and equality with the locked integration inputs
- software, RTL and board measurement scope
- measured versus cycle-derived versus estimated status
- raw/result CSVs and environment metadata
- corresponding `global_metrics.yaml` and `claim_registry.csv` entries

Until those gates pass, all benchmark fields remain `null`, not zero. Existing resource utilization and timing-closure metrics are implementation evidence and do not fill this benchmark.
