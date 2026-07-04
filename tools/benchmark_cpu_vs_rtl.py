from __future__ import annotations

import argparse
import json
import time

from award_readiness_common import REPORTS, RESULTS, all_chunks, infer_many, md_table, metrics, pct, write_csv, write_json


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark fixed Python golden inference and compare it with RTL cycle evidence.")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    chunks = all_chunks()
    timings = []
    last_metric = None
    for _ in range(args.repeats):
        start = time.perf_counter()
        pred, _ = infer_many(chunks, mode="full")
        elapsed = time.perf_counter() - start
        timings.append(elapsed)
        last_metric = metrics(chunks, pred)

    samples_total = len(chunks) * 1_800_000
    best = min(timings)
    median = sorted(timings)[len(timings) // 2]
    profile = load_json(RESULTS / "xsim_snn_ecg_v2_test_first1_profile.json")
    cycles_total = float(profile["total_cycles"]["median"])
    cycles_per_sample = float(profile["derived"]["cycles_per_sample_total"])
    power_path = RESULTS / "vivado_snn_ecg_v2" / "snn_ecg_v2_vivado_summary.json"
    power = load_json(power_path).get("power", {}) if power_path.exists() else {}
    total_power_w = float(power.get("total_on_chip_power_w", 0.0)) if power else None

    rows = [
        {
            "implementation": "Python golden fixed model",
            "time_per_136_chunks_s": median,
            "time_per_30min_chunk_s": median / len(chunks),
            "chunks_per_sec": len(chunks) / median,
            "equivalent_samples_per_sec": samples_total / median,
            "notes": f"Local Python final-readout inference on precomputed chunk features, {args.repeats} repeats; best={best:.6f}s. Not raw-sample CPU processing.",
        },
        {
            "implementation": "RTL cycle model @ 1 MHz",
            "time_per_136_chunks_s": cycles_total / 1_000_000.0 * len(chunks),
            "time_per_30min_chunk_s": cycles_total / 1_000_000.0,
            "chunks_per_sec": 1.0 / (cycles_total / 1_000_000.0),
            "equivalent_samples_per_sec": 1_000_000.0 / cycles_per_sample,
            "notes": "Derived from PROFILE_EN XSim cycle counters; not wall-clock board replay.",
        },
        {
            "implementation": "RTL cycle model @ 100 MHz",
            "time_per_136_chunks_s": cycles_total / 100_000_000.0 * len(chunks),
            "time_per_30min_chunk_s": cycles_total / 100_000_000.0,
            "chunks_per_sec": 1.0 / (cycles_total / 100_000_000.0),
            "equivalent_samples_per_sec": 100_000_000.0 / cycles_per_sample,
            "notes": "Derived from AXI OOC 10 ns timing feasibility and cycle counters.",
        },
    ]
    write_csv(REPORTS / "cpu_baseline_latency.csv", rows)
    energy_note = "not available"
    if total_power_w:
        energy = total_power_w / (1_000_000.0 / cycles_per_sample)
        energy_note = f"Vivado-estimated @1MHz: {energy*1e9:.2f} nJ/sample using {total_power_w:.3f} W total on-chip power."
    summary = {
        "python_timings_s": timings,
        "python_metric": last_metric,
        "rtl_profile_source": str(RESULTS / "xsim_snn_ecg_v2_test_first1_profile.json"),
        "cycles_per_sample_total": cycles_per_sample,
        "energy_note": energy_note,
        "limitation": "CPU timing is local Python, not optimized C. RTL timing is derived from counters and Vivado reports, not a full 30-minute board replay transcript.",
    }
    write_json(REPORTS / "cpu_vs_rtl_summary.json", summary)
    md = [
        "# CPU vs RTL Baseline",
        "",
        md_table(
            ["implementation", "time/chunk", "chunks/sec", "equiv samples/sec", "notes"],
            [
                [
                    row["implementation"],
                    f"{row['time_per_30min_chunk_s']:.6f} s",
                    f"{row['chunks_per_sec']:.2f}",
                    f"{row['equivalent_samples_per_sec']:.2f}",
                    row["notes"],
                ]
                for row in rows
            ],
        ),
        "",
        f"- Python fixed-model accuracy over all chunks: {last_metric['correct']}/{last_metric['total']} = {pct(last_metric['accuracy'])}",
        f"- RTL cycles/sample total: {cycles_per_sample:.6f}",
        f"- Energy/sample status: {energy_note}",
        "",
        "Limitation: Python timing is final-readout inference on precomputed feature dumps. It is not an end-to-end CPU ECG sample-processing baseline. RTL throughput is derived from counters and Vivado reports, not a board-level full replay measurement.",
    ]
    (REPORTS / "cpu_vs_rtl_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "cpu_vs_rtl_summary.md")


if __name__ == "__main__":
    main()
