# Python Baseline Not Completed

The final repository does not contain a current Python sample-stream inference path. Git history contains `scripts/snapshot_c24_rtl_exact.py`, but it predates the final locked `class_score_neurons.v`. A benchmark-scoped reconstruction was tested on `AFF_afdb_06995_chunk10`:

- historical/no-idle reconstruction: final_pred 0, final_mem 14/0/4/12;
- canonical-idle reconstruction: final_pred 2, final_mem 0/5/25/0;
- locked canonical RTL expected: final_pred 0, final_mem 17/0/8/5.

Therefore the functional-equivalence gate failed. No latency, throughput, or speedup is reported for Python. Empty required run CSVs retain the schema without inventing measurements. The reconstruction sources are retained under `benchmarks/accelerator_benefit/tools/` solely as audit evidence.
