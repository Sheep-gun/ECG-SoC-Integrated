#!/usr/bin/env python3
"""Generate all artifact-derived NO_BOARD benchmark deliverables."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "benchmarks" / "accelerator_benefit"
RESULTS = BENCH / "results"
REPORTS = BENCH / "reports"
FIGURES = BENCH / "figures"
BOARD = BENCH / "board"
REFERENCE = BENCH / "reference"
CASES_CSV = REPO / "reports" / "final" / "board_replay_36_cases.csv"
BOARD_CSV = REPO / "reports" / "final" / "board_replay_36_expected_vs_board.csv"
XSIM_CSV = REPO / "reports" / "final" / "fulltop_xsim_final_test_36" / "locked_class_cases_fulltop_xsim_predictions.csv"
LOCKED_CONFIG = REPO / "configs" / "final_submission_locked_model.json"
LOCKED_PARAMS = REPO / "configs" / "recordwise_resplit_seed20260808" / "best_final_membrane_structural_grid_locked.json"
FINAL_METRICS = REPO / "reports" / "final" / "final_metrics.json"
HISTORICAL_PYTHON = REPO / "reports" / "final" / "strict_recordwise" / "structural_final_test_predictions.csv"
CLOCK_HZ = 100_000_000
START_COMMIT = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
CLASSES = ("NSR", "CHF", "ARR", "AFF")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO.resolve()).as_posix()


def git(*args: str) -> str:
    exe = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
    return subprocess.check_output([str(exe), *args], cwd=REPO, text=True).strip()


def quantile(values: list[float], q: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), q))


def generate_protocol() -> str:
    text = """# Frozen Accelerator-Benefit Benchmark Protocol

- Mode: **NO_BOARD**
- Starting commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- Branch: `codex/accelerator-benefit-benchmark`
- Locked model: `structural_guarded_silent_aff_1008710`
- Cases: the 36 rows in `reports/final/board_replay_36_cases.csv`
- Input: signed 12-bit, 1,800,000 samples per case
- Canonical RTL cadence: `sample_gap_cycles=2`
- Clock: 100 MHz, verified by the 10.000 ns constraints and implemented-system timing report
- CPU validity gate: timing is reportable only after current locked Python output matches canonical RTL `final_pred` and all four `final_mem` values 36/36.
- RTL scope: cycle-derived stored-data processing latency; XSim host wall time is forbidden.
- Board timing and physical power: `PENDING_BOARD` until new hardware-timer transcripts or measurement records exist.
- Live interpretation: a 30-minute final decision still requires a 30-minute observation window at 1 kSPS.
- No model, threshold, feature, class-weight, Snapshot, Final Membrane, RTL datapath, dataset, prediction, or metric change is permitted.
"""
    write_text(REPORTS / "BENCHMARK_PROTOCOL.md", text)
    return sha256(REPORTS / "BENCHMARK_PROTOCOL.md")


def generate_hashes(protocol_hash: str) -> None:
    cases = read_csv(CASES_CSV)
    dataset_rows = []
    for row in cases:
        path = REPO / row["mem_path"]
        actual = sha256(path)
        if actual != row["mem_sha256"]:
            raise SystemExit(f"dataset hash mismatch: {row['case_id']}")
        dataset_rows.append({
            "case_id": row["case_id"], "sample_count": row["sample_count_expected"],
            "path": row["mem_path"], "sha256": actual,
        })
    write_csv(RESULTS / "benchmark_dataset_manifest.csv", dataset_rows, ["case_id", "sample_count", "path", "sha256"])

    paths = [LOCKED_CONFIG, LOCKED_PARAMS, FINAL_METRICS, CASES_CSV, XSIM_CSV, BOARD_CSV, HISTORICAL_PYTHON]
    paths += sorted((REPO / "rtl").glob("*.v"))
    paths += sorted((REPO / "rtl/core").glob("*.v"))
    paths += sorted((REPO / "rtl/axi").glob("*.v"))
    paths += [
        REPO / "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit",
        REPO / "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa",
        REPO / "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf",
    ]
    if (BOARD / "build/snn_ecg_mb_full_replay_benchmark.elf").exists():
        paths.append(BOARD / "build/snn_ecg_mb_full_replay_benchmark.elf")
    paths += sorted((REPO / "reports/final/board_replay_36/transcripts").glob("*.txt"))
    paths += [path for path in (
        BENCH / "tools/cpp/cpp_baseline.cpp",
        BENCH / "tools/cpp/build_cpp_baseline.py",
        BENCH / "tools/cpp/run_cpp_benchmark.py",
        BENCH / "tools/cpp/cpp_build_environment.json",
        BENCH / "tools/cpp/bin/cpp_baseline.exe",
        BENCH / "tools/snapshot_c24_rtl_exact.py",
        BENCH / "tools/locked_integer_inference.py",
        BENCH / "tools/run_python_benchmark.py",
        BENCH / "tools/check_python_equivalence.py",
    ) if path.exists()]
    rows = [{"artifact": repo_rel(path), "sha256": sha256(path), "bytes": path.stat().st_size} for path in paths]
    rows.append({"artifact": repo_rel(RESULTS / "benchmark_dataset_manifest.csv"), "sha256": sha256(RESULTS / "benchmark_dataset_manifest.csv"), "bytes": (RESULTS / "benchmark_dataset_manifest.csv").stat().st_size})
    rows.append({"artifact": repo_rel(REPORTS / "BENCHMARK_PROTOCOL.md"), "sha256": protocol_hash, "bytes": (REPORTS / "BENCHMARK_PROTOCOL.md").stat().st_size})
    write_csv(RESULTS / "immutable_artifact_hashes.csv", rows, ["artifact", "sha256", "bytes"])
    write_json(RESULTS / "repository_start_state.json", {
        "starting_commit_sha": START_COMMIT,
        "branch": "codex/accelerator-benefit-benchmark",
        "mode": "NO_BOARD",
        "protocol_sha256": protocol_hash,
        "locked_config_sha256": sha256(LOCKED_CONFIG),
        "locked_params_file_sha256": sha256(LOCKED_PARAMS),
        "locked_params_payload_sha256": json.loads(LOCKED_PARAMS.read_text(encoding="utf-8-sig"))["selected_candidate_params_hash"],
        "dataset_manifest_sha256": sha256(RESULTS / "benchmark_dataset_manifest.csv"),
    })


def summarize_host_runs(path: Path, stem: str, scope: str) -> dict[str, Any]:
    rows = read_csv(path)
    case_ids = sorted({row["case_id"] for row in rows})
    if len(rows) != 360 or len(case_ids) != 36:
        raise SystemExit(f"incomplete {stem} result set: {len(rows)} rows across {len(case_ids)} cases")
    per_case = []
    for case_id in case_ids:
        case_rows = [row for row in rows if row["case_id"] == case_id]
        if len(case_rows) != 10 or any(row["output_match"].lower() != "true" for row in case_rows):
            raise SystemExit(f"invalid {stem} repetitions/equivalence for {case_id}")
        values = [float(row["elapsed_ms"]) for row in case_rows]
        rates = [float(row["samples_per_second"]) for row in case_rows]
        per_case.append({
            "case_id": case_id, "repetitions": len(values),
            "latency_ms_median": f"{statistics.median(values):.6f}",
            "latency_ms_mean": f"{statistics.mean(values):.6f}",
            "latency_ms_std": f"{statistics.pstdev(values):.6f}",
            "latency_ms_min": f"{min(values):.6f}", "latency_ms_max": f"{max(values):.6f}",
            "latency_ms_q1": f"{quantile(values, 0.25):.6f}", "latency_ms_q3": f"{quantile(values, 0.75):.6f}",
            "latency_ms_iqr": f"{quantile(values, 0.75) - quantile(values, 0.25):.6f}",
            "throughput_samples_per_s_median": f"{statistics.median(rates):.6f}", "output_equivalence": "true",
        })
    write_csv(RESULTS / f"{stem}_summary.csv", per_case, list(per_case[0]))
    all_values = [float(row["elapsed_ms"]) for row in rows]
    all_rates = [float(row["samples_per_second"]) for row in rows]
    case_medians = [float(row["latency_ms_median"]) for row in per_case]
    summary = {
        "status": "MEASURED_NOW", "scope": scope, "warmups_per_case": 3,
        "measured_repetitions_per_case": 10, "case_count": 36, "measured_run_count": 360,
        "sample_count_per_case": 1_800_000,
        "all_run_latency_ms": {
            "median": statistics.median(all_values), "mean": statistics.mean(all_values),
            "std": statistics.pstdev(all_values), "min": min(all_values), "max": max(all_values),
            "q1": quantile(all_values, 0.25), "q3": quantile(all_values, 0.75),
            "iqr": quantile(all_values, 0.75) - quantile(all_values, 0.25),
        },
        "per_case_median_latency_ms": {
            "median": statistics.median(case_medians), "mean": statistics.mean(case_medians),
            "std": statistics.pstdev(case_medians), "min": min(case_medians), "max": max(case_medians),
            "q1": quantile(case_medians, 0.25), "q3": quantile(case_medians, 0.75),
            "iqr": quantile(case_medians, 0.75) - quantile(case_medians, 0.25),
        },
        "throughput_samples_per_s_median": statistics.median(all_rates),
        "output_equivalence": "36/36 final_pred; 36/36 all four final_mem", "run_evidence": repo_rel(path),
    }
    write_json(RESULTS / f"{stem}_summary.json", summary)
    return summary


def generate_cpu_status() -> dict[str, Any] | None:
    try:
        cpu = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
            text=True, timeout=15,
        ).strip()
    except Exception:
        cpu = platform.processor() or "UNKNOWN"
    default_env = {
        "environment_id": "windows_no_board_2026-07-12",
        "cpu_model": cpu,
        "os": platform.platform(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "numpy_version": np.__version__,
        "processes": 1,
        "thread_environment": {name: os.environ.get(name, "1 (benchmark-required)") for name in (
            "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"
        )},
        "status": "NOT_COMPLETED_NO_CURRENT_EXACT_PYTHON_PATH",
        "evidence": "reports/PYTHON_BASELINE_NOT_COMPLETED.md",
    }
    env_path = RESULTS / "cpu_environment.json"
    existing_env = json.loads(env_path.read_text(encoding="utf-8")) if env_path.exists() else {}
    fields = [
        "case_id", "repeat_id", "sample_count", "elapsed_ns", "elapsed_ms",
        "samples_per_second", "final_pred", "final_mem_NSR", "final_mem_CHF",
        "final_mem_ARR", "final_mem_AFF", "output_match", "environment_id",
    ]
    kernel_path = RESULTS / "cpu_python_kernel_runs.csv"
    e2e_path = RESULTS / "cpu_python_end_to_end_runs.csv"
    historical = {row["case_id"]: row for row in read_csv(HISTORICAL_PYTHON)}
    audit_rows = []
    for case in read_csv(CASES_CSV):
        old = historical[case["source_prediction_case_id"]]
        pred_match = int(old["pred_class"]) == int(case["expected_final_pred"])
        mem_match = all(int(old[f"final_mem_{cls}"]) == int(case[f"expected_final_mem_{cls}"]) for cls in CLASSES)
        audit_rows.append({
            "case_id": case["case_id"], "source_prediction_case_id": case["source_prediction_case_id"],
            "historical_pred": old["pred_class"], "canonical_pred": case["expected_final_pred"],
            **{f"historical_mem_{cls}": old[f"final_mem_{cls}"] for cls in CLASSES},
            **{f"canonical_mem_{cls}": case[f"expected_final_mem_{cls}"] for cls in CLASSES},
            "pred_match": str(pred_match).lower(), "mem_match": str(mem_match).lower(),
        })
    write_csv(RESULTS / "historical_python_equivalence_audit.csv", audit_rows, list(audit_rows[0]))
    pred_mismatches = sum(row["pred_match"] == "false" for row in audit_rows)
    mem_mismatches = sum(row["mem_match"] == "false" for row in audit_rows)
    completed = existing_env.get("status") == "COMPLETED"
    if completed:
        kernel = summarize_host_runs(kernel_path, "cpu_python_kernel", "samples already loaded in RAM through final result")
        e2e = summarize_host_runs(e2e_path, "cpu_python_end_to_end", "file open/read/parse through final result")
        write_text(REPORTS / "PYTHON_BASELINE_MEASURED.md", f"""# Exact Python Baseline

Status: **MEASURED_NOW**. The benchmark-scoped Python clock model holds the delayed accepted sample exactly as the locked RTL pipeline does and uses canonical `sample_gap_cycles=2`.

- Functional gate: 36/36 `final_pred` and 36/36 all four `final_mem` values.
- Timing: one process, forced one-thread numerical environment, 3 warmups and 10 measured repetitions per case using `time.perf_counter_ns()`.
- Kernel per-case-median aggregate: median {kernel['per_case_median_latency_ms']['median']:.6f} ms, mean {kernel['per_case_median_latency_ms']['mean']:.6f} ms, population standard deviation {kernel['per_case_median_latency_ms']['std']:.6f} ms, min {kernel['per_case_median_latency_ms']['min']:.6f} ms, max {kernel['per_case_median_latency_ms']['max']:.6f} ms, IQR {kernel['per_case_median_latency_ms']['iqr']:.6f} ms.
- End-to-end per-case-median aggregate: median {e2e['per_case_median_latency_ms']['median']:.6f} ms, mean {e2e['per_case_median_latency_ms']['mean']:.6f} ms, population standard deviation {e2e['per_case_median_latency_ms']['std']:.6f} ms, min {e2e['per_case_median_latency_ms']['min']:.6f} ms, max {e2e['per_case_median_latency_ms']['max']:.6f} ms, IQR {e2e['per_case_median_latency_ms']['iqr']:.6f} ms.
""")
        stale = REPORTS / "PYTHON_BASELINE_NOT_COMPLETED.md"
        if stale.exists():
            stale.unlink()
        return {"kernel": kernel, "end_to_end": e2e, "environment": existing_env}

    if existing_env.get("status") not in {"RUNNING", "PARTIAL"}:
        write_json(env_path, default_env)
        write_csv(kernel_path, [], fields)
        write_csv(e2e_path, [], fields)
    mismatch = f"""# Python Baseline Not Completed

The final repository does not contain a current Python sample-stream inference path. Git history contains `scripts/snapshot_c24_rtl_exact.py`, but it predates the final locked `class_score_neurons.v`. A benchmark-scoped reconstruction was tested on `AFF_afdb_06995_chunk10`:

- historical/no-idle reconstruction: final_pred 0, final_mem 14/0/4/12;
- canonical-idle reconstruction: final_pred 2, final_mem 0/5/25/0;
- locked canonical RTL expected: final_pred 0, final_mem 17/0/8/5.

Therefore the functional-equivalence gate failed. No latency, throughput, or speedup is reported for Python. Empty required run CSVs retain the schema without inventing measurements. The reconstruction sources are retained under `benchmarks/accelerator_benefit/tools/` solely as audit evidence.

Across the committed 36-row historical Python result set, {pred_mismatches} final predictions and {mem_mismatches} final-membrane vectors differ from the canonical locked result. See `results/historical_python_equivalence_audit.csv`.
"""
    write_text(REPORTS / "PYTHON_BASELINE_NOT_COMPLETED.md", mismatch)
    return None


def generate_cpp_status() -> dict[str, Any] | None:
    runs_path = RESULTS / "cpu_cpp_kernel_runs.csv"
    if not runs_path.exists():
        write_text(REPORTS / "CPP_BASELINE_NOT_COMPLETED.md", """# C/C++ Baseline Not Completed

The optional exact C/C++ baseline has not been run. No approximate translation or timing is reported.
""")
        return None
    rows = read_csv(runs_path)
    if not rows:
        write_text(REPORTS / "CPP_BASELINE_NOT_COMPLETED.md", """# C/C++ Baseline Not Completed

The optional exact C/C++ baseline has not been run. No approximate translation or timing is reported.
""")
        return None
    case_ids = sorted({row["case_id"] for row in rows})
    if len(rows) != 360 or len(case_ids) != 36:
        raise SystemExit(f"incomplete C++ result set: {len(rows)} rows across {len(case_ids)} cases")
    per_case = []
    for case_id in case_ids:
        case_rows = [row for row in rows if row["case_id"] == case_id]
        if len(case_rows) != 10 or any(row["output_match"].lower() != "true" for row in case_rows):
            raise SystemExit(f"invalid C++ repetitions/equivalence for {case_id}")
        values = [float(row["elapsed_ms"]) for row in case_rows]
        rates = [float(row["samples_per_second"]) for row in case_rows]
        per_case.append({
            "case_id": case_id, "repetitions": len(values),
            "latency_ms_median": f"{statistics.median(values):.6f}",
            "latency_ms_mean": f"{statistics.mean(values):.6f}",
            "latency_ms_std": f"{statistics.pstdev(values):.6f}",
            "latency_ms_min": f"{min(values):.6f}",
            "latency_ms_max": f"{max(values):.6f}",
            "latency_ms_q1": f"{quantile(values, 0.25):.6f}",
            "latency_ms_q3": f"{quantile(values, 0.75):.6f}",
            "latency_ms_iqr": f"{quantile(values, 0.75) - quantile(values, 0.25):.6f}",
            "throughput_samples_per_s_median": f"{statistics.median(rates):.6f}",
            "output_equivalence": "true",
        })
    write_csv(RESULTS / "cpu_cpp_kernel_summary.csv", per_case, list(per_case[0]))
    all_values = [float(row["elapsed_ms"]) for row in rows]
    all_rates = [float(row["samples_per_second"]) for row in rows]
    case_medians = [float(row["latency_ms_median"]) for row in per_case]
    summary = {
        "status": "MEASURED_NOW",
        "implementation": "Verilator exact cycle-accurate C++ translation of locked RTL",
        "scope": "loaded samples to final result; single generated model; host wall time",
        "warmups_per_case": 3, "measured_repetitions_per_case": 10,
        "case_count": 36, "measured_run_count": 360, "sample_count_per_case": 1_800_000,
        "all_run_latency_ms": {
            "median": statistics.median(all_values), "mean": statistics.mean(all_values),
            "std": statistics.pstdev(all_values), "min": min(all_values), "max": max(all_values),
            "q1": quantile(all_values, 0.25),
            "q3": quantile(all_values, 0.75), "iqr": quantile(all_values, 0.75) - quantile(all_values, 0.25),
        },
        "per_case_median_latency_ms": {
            "median": statistics.median(case_medians), "mean": statistics.mean(case_medians),
            "std": statistics.pstdev(case_medians), "min": min(case_medians), "max": max(case_medians),
            "q1": quantile(case_medians, 0.25),
            "q3": quantile(case_medians, 0.75), "iqr": quantile(case_medians, 0.75) - quantile(case_medians, 0.25),
        },
        "throughput_samples_per_s_median": statistics.median(all_rates),
        "output_equivalence": "36/36 final_pred; 36/36 all four final_mem",
        "build_evidence": "benchmarks/accelerator_benefit/tools/cpp/cpp_build_environment.json",
        "run_evidence": "benchmarks/accelerator_benefit/results/cpu_cpp_kernel_runs.csv",
    }
    write_json(RESULTS / "cpu_cpp_kernel_summary.json", summary)
    write_text(REPORTS / "CPP_BASELINE_MEASURED.md", f"""# Exact C/C++ Baseline

Status: **MEASURED_NOW**.

This is a Verilator-generated, cycle-accurate C++ translation of the unchanged locked RTL. It is not a hand-optimized algorithmic implementation and is not used as a substitute for the required Python reference path.

- Functional gate: 36/36 `final_pred` and 36/36 all four `final_mem` values.
- Timing: 3 untimed warmups followed by 10 measured runs per case (360 measured runs).
- Scope: samples already loaded in memory through final result, one model instance, one host thread.
- Per-case-median aggregate latency: median {summary['per_case_median_latency_ms']['median']:.6f} ms, mean {summary['per_case_median_latency_ms']['mean']:.6f} ms, population standard deviation {summary['per_case_median_latency_ms']['std']:.6f} ms, IQR {summary['per_case_median_latency_ms']['iqr']:.6f} ms.
- Median measured throughput: {summary['throughput_samples_per_s_median'] / 1e6:.6f} MSamples/s.

This host timing is reported independently. It is not combined with the RTL's cycle-derived stored-data latency to claim a Python speedup.
""")
    stale = REPORTS / "CPP_BASELINE_NOT_COMPLETED.md"
    if stale.exists():
        stale.unlink()
    return summary


def generate_rtl() -> dict[str, Any]:
    cases = read_csv(CASES_CSV)
    xsim = {row["case_id"]: row for row in read_csv(XSIM_CSV)}
    fields = [
        "case_id", "sample_gap_cycles", "clock_frequency_hz", "prof_total_cycles",
        "prof_run_cycles", "prof_input_wait_cycles", "accepted_samples", "windows",
        "decisions", "total_latency_ms", "run_latency_ms", "input_wait_latency_ms",
        "throughput_samples_per_s", "realtime_margin", "final_pred_match", "final_mem_match",
    ]
    rows = []
    for case in cases:
        src = xsim[case["source_prediction_case_id"]]
        memories = all(int(src[f"final_mem_{cls}"]) == int(case[f"expected_final_mem_{cls}"]) for cls in CLASSES)
        pred_match = int(src["final_pred_class"]) == int(case["expected_final_pred"])
        total = int(src["prof_total_cycles"])
        run = int(src["prof_run_cycles"])
        wait = int(src["prof_input_wait_cycles"])
        accepted = int(src["prof_accepted_samples"])
        row = {
            "case_id": case["case_id"], "sample_gap_cycles": 2, "clock_frequency_hz": CLOCK_HZ,
            "prof_total_cycles": total, "prof_run_cycles": run, "prof_input_wait_cycles": wait,
            "accepted_samples": accepted, "windows": int(src["prof_windows"]),
            "decisions": int(src["prof_decisions"]),
            "total_latency_ms": f"{total * 1000 / CLOCK_HZ:.9f}",
            "run_latency_ms": f"{run * 1000 / CLOCK_HZ:.9f}",
            "input_wait_latency_ms": f"{wait * 1000 / CLOCK_HZ:.9f}",
            "throughput_samples_per_s": f"{accepted * CLOCK_HZ / total:.6f}",
            "realtime_margin": f"{accepted * CLOCK_HZ / total / 1000:.6f}",
            "final_pred_match": str(pred_match).lower(), "final_mem_match": str(memories).lower(),
        }
        if accepted != 1_800_000 or row["windows"] != 30 or row["decisions"] != 1 or not pred_match or not memories:
            raise SystemExit(f"RTL acceptance failed: {case['case_id']}")
        rows.append(row)
    write_csv(RESULTS / "rtl_cycle_benchmark.csv", rows, fields)
    latencies = [float(row["total_latency_ms"]) for row in rows]
    throughput = [float(row["throughput_samples_per_s"]) for row in rows]
    summary = {
        "status": "CYCLE_DERIVED", "case_count": 36, "sample_gap_cycles": 2,
        "clock_frequency_hz": CLOCK_HZ,
        "clock_evidence": [
            "constraints/snn_ecg_axi_ooc.xdc: create_clock period 10.000 ns",
            "constraints/nexys_a7_microblaze_full_replay.xdc: create_clock period 10.000 ns",
            "results/board_replay/microblaze_full_replay/reports/system_timing_summary.rpt: 100.000 MHz",
        ],
        "total_latency_ms": {"median": statistics.median(latencies), "mean": statistics.mean(latencies), "std": statistics.pstdev(latencies), "min": min(latencies), "max": max(latencies), "iqr": quantile(latencies, .75) - quantile(latencies, .25)},
        "throughput_samples_per_s": statistics.mean(throughput),
        "throughput_msamples_per_s": statistics.mean(throughput) / 1e6,
        "realtime_margin_vs_1ksps": statistics.mean(throughput) / 1000,
        "active_snapshot_latency_ms": int(xsim[cases[0]["source_prediction_case_id"]]["prof_last_window_latency"]) * 1000 / CLOCK_HZ,
        "active_decision_latency_ms": int(xsim[cases[0]["source_prediction_case_id"]]["prof_last_decision_latency"]) * 1000 / CLOCK_HZ,
        "maximum_validated_stream_acceptance_rate_samples_per_s": statistics.mean(throughput),
        "equivalence": "final_pred 36/36; final_mem 36/36",
    }
    write_json(RESULTS / "rtl_cycle_summary.json", summary)
    write_text(REPORTS / "RTL_CYCLE_METHODOLOGY.md", f"""# RTL Cycle Methodology

The committed full-top XSim profile is used at canonical `sample_gap_cycles=2`. Host simulator wall time is not used. The implemented clock is 100 MHz from the 10.000 ns XDC constraint and the committed Vivado timing report.

For each case: latency = cycles / 100,000,000; throughput = 1,800,000 / latency; real-time margin = throughput / 1,000. All 36 rows validate 1,800,000 accepted samples, 30 windows, one decision, final_pred exact, and final_mem exact.

Stored-data processing latency is {summary['total_latency_ms']['median']:.6f} ms. Live ECG still requires 30 minutes to observe the decision window.
""")
    return summary


def generate_board_audit() -> None:
    rows = read_csv(BOARD_CSV)
    out = []
    for row in rows:
        transcript = REPO / row["transcript_path"]
        item = {
            "case_id": row["case_id"], "transcript_exists": str(transcript.exists()).lower(),
            "transcript_sha256": sha256(transcript), "samples_sent": row["samples_sent"],
            "samples_accepted": row["samples_accepted"], "snapshot_count": row["snapshot_count"],
            "decision_count": "1" if row["done"] == "1" else "0",
            "final_pred_match": row["pred_match"], "final_mem_match": row["final_mem_exact_match"],
            "label_correct": row["board_correct_vs_label"], "status": row["status"],
            "timing_measurement_present": "false",
            "evidence_path": row["transcript_path"],
        }
        out.append(item)
    if len(out) != 36 or sum(int(r["final_pred_match"]) for r in out) != 36 or sum(int(r["final_mem_match"]) for r in out) != 36:
        raise SystemExit("board audit acceptance failed")
    write_csv(RESULTS / "existing_board_functional_audit.csv", out, list(out[0]))
    write_text(REPORTS / "EXISTING_BOARD_EVIDENCE_AUDIT.md", """# Existing Board Evidence Audit

All 36 committed transcripts exist and hash successfully. Each case reports 1,800,000 samples, 30 snapshots, one completed decision, final_pred 36/36 exact, and final_mem 36/36 exact. Label accuracy remains 29/36 (80.56%); 36/36 is functional equivalence, not classification accuracy.

The transcripts contain accelerator profile values but no documented independent hardware-timer board benchmark protocol. They are retained as existing functional evidence and are not used to claim measured board latency.
""")


def generate_memory_power(rtl: dict[str, Any]) -> None:
    memory = [
        {"item": "hypothetical_full_30min_raw_input", "category": "avoided_input_buffer", "bits": 21_600_000, "bytes": 2_700_000, "status": "derived", "evidence": "1800000 samples * 12 bits", "notes": "not instantiated"},
        {"item": "pure_rtl_total_flip_flops", "category": "all_sequential_state_upper_bound", "bits": 5038, "bytes": 629.75, "status": "synthesis_reported", "evidence": "reports/final/vivado_locked_model_metrics.md", "notes": "includes persistent, pipeline, control, and interface state; not exact inference memory"},
        {"item": "persistent_inference_state", "category": "persistent_state", "bits": "<=5038", "bytes": "<=629.75", "status": "upper_bound", "evidence": "pure RTL FF count plus RTL inspection", "notes": "exact post-synthesis category split unavailable"},
        {"item": "pipeline_control_interface_state", "category": "nonpersistent_or_control", "bits": "included_in_5038", "bytes": "included_in_629.75", "status": "not_separately_quantified", "evidence": "RTL declarations and synthesis total", "notes": "not misreported as inference memory"},
        {"item": "BRAM", "category": "resource", "bits": 0, "bytes": 0, "status": "synthesis_reported", "evidence": "reports/final/vivado_locked_model_metrics.md", "notes": "pure RTL"},
        {"item": "DSP", "category": "resource", "bits": "N/A", "bytes": "N/A", "status": "synthesis_reported", "evidence": "reports/final/vivado_locked_model_metrics.md", "notes": "0 DSP"},
    ]
    write_csv(RESULTS / "state_memory_inventory.csv", memory, ["item", "category", "bits", "bytes", "status", "evidence", "notes"])
    write_text(REPORTS / "STREAMING_MEMORY_ANALYSIS.md", """# Streaming Memory Analysis

The accelerator updates state sample by sample and does not instantiate a 1,800,000-sample input buffer. Raw full-window storage would be 21,600,000 bits = 2,700,000 bytes (2.7 MB decimal).

Pure RTL uses 0 BRAM and 0 DSP. The 5,038 implementation FFs provide a conservative 5,038-bit (629.75-byte) upper bound on all sequential storage, but this is deliberately not called exact inference-state memory: it includes persistent inference state, pipeline registers, counters, control, and interface state. A post-synthesis per-category split is unavailable.
""")
    latency_s = rtl["total_latency_ms"]["median"] / 1000
    energy = 0.099 * latency_s
    rows = [
        {"implementation": "Pure RTL", "power_w": "0.099", "energy_per_decision_j": f"{energy:.12f}", "status": "ESTIMATED_DERIVED", "evidence_type": "Vivado-estimated power * cycle-derived stored-data processing latency", "scope": "accelerator implementation estimate", "evidence_path": "reports/final/vivado_locked_model_metrics.md; benchmarks/accelerator_benefit/results/rtl_cycle_summary.json"},
        {"implementation": "Physical FPGA board", "power_w": "PENDING_BOARD", "energy_per_decision_j": "PENDING_BOARD", "status": "PENDING_BOARD", "evidence_type": "pending physical measurement", "scope": "board-level idle/active/active-minus-idle", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md"},
        {"implementation": "CPU", "power_w": "N/A", "energy_per_decision_j": "N/A", "status": "N/A_NO_DEFENSIBLE_COUNTER", "evidence_type": "none", "scope": "CPU", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md"},
    ]
    write_csv(RESULTS / "power_energy_summary.csv", rows, list(rows[0]))
    write_text(REPORTS / "POWER_ENERGY_METHODOLOGY.md", f"""# Power and Energy Methodology

- Pure RTL: 0.099 W is a Vivado estimate, not board-measured power. Estimated energy is exactly labeled **Vivado-estimated power × cycle-derived stored-data processing latency**: 0.099 W × {latency_s:.9f} s = {energy:.12f} J/decision.
- Physical board: PENDING_BOARD. Use a calibrated bench supply or inline USB power analyzer at the board power input. Record instrument model/range/accuracy, sample interval no slower than 1 s, ambient conditions, and cable configuration. Measure at least 60 s of programmed idle power, then active continuous 36-case replay power. Report mean, standard deviation, instrument accuracy, and active-minus-idle power. This is board-level scope, not accelerator-core power.
- CPU: N/A because no RAPL/powercap or equivalent defensible counter is available.

Runtime alone is never converted into energy-efficiency speedup.
""")


def generate_comparison(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None) -> None:
    fields = ["implementation", "measurement_scope", "status", "evidence_type", "sample_count", "latency_ms_median", "latency_ms_mean", "latency_ms_std", "throughput_samples_per_s", "realtime_margin_vs_1ksps", "speedup_vs_python_kernel", "power_w", "power_evidence", "energy_per_decision_j", "energy_evidence", "LUT", "FF", "BRAM", "DSP", "full_input_buffer_required", "output_equivalence", "evidence_path", "notes"]
    na_cpu = {
        "sample_count": 1_800_000, "latency_ms_median": "N/A", "latency_ms_mean": "N/A", "latency_ms_std": "N/A",
        "throughput_samples_per_s": "N/A", "realtime_margin_vs_1ksps": "N/A", "speedup_vs_python_kernel": "N/A",
        "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A",
        "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "NOT_VERIFIED",
    }
    measured_python_rows = ([
        {"implementation": "Python integer kernel", "measurement_scope": "loaded samples to final result", "status": "MEASURED_NOW", "evidence_type": "perf_counter_ns after exact 36/36 equivalence", "sample_count": 1_800_000, "latency_ms_median": f"{python['kernel']['per_case_median_latency_ms']['median']:.6f}", "latency_ms_mean": f"{python['kernel']['per_case_median_latency_ms']['mean']:.6f}", "latency_ms_std": f"{python['kernel']['per_case_median_latency_ms']['std']:.6f}", "throughput_samples_per_s": f"{python['kernel']['throughput_samples_per_s_median']:.6f}", "realtime_margin_vs_1ksps": f"{python['kernel']['throughput_samples_per_s_median'] / 1000:.6f}", "speedup_vs_python_kernel": "1.000000", "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "36/36 pred; 36/36 mem", "evidence_path": "benchmarks/accelerator_benefit/results/cpu_python_kernel_summary.json", "notes": "one process; one thread; canonical sample_gap_cycles=2"},
        {"implementation": "Python end-to-end", "measurement_scope": "file parse plus inference", "status": "MEASURED_NOW", "evidence_type": "perf_counter_ns after exact 36/36 equivalence", "sample_count": 1_800_000, "latency_ms_median": f"{python['end_to_end']['per_case_median_latency_ms']['median']:.6f}", "latency_ms_mean": f"{python['end_to_end']['per_case_median_latency_ms']['mean']:.6f}", "latency_ms_std": f"{python['end_to_end']['per_case_median_latency_ms']['std']:.6f}", "throughput_samples_per_s": f"{python['end_to_end']['throughput_samples_per_s_median']:.6f}", "realtime_margin_vs_1ksps": f"{python['end_to_end']['throughput_samples_per_s_median'] / 1000:.6f}", "speedup_vs_python_kernel": "N/A", "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "36/36 pred; 36/36 mem", "evidence_path": "benchmarks/accelerator_benefit/results/cpu_python_end_to_end_summary.json", "notes": "includes file open/read/parse"},
    ] if python else [
        {"implementation": "Python integer kernel", "measurement_scope": "loaded samples to final result", "status": "NOT_COMPLETED_EQUIVALENCE_FAILED", "evidence_type": "audit", **na_cpu, "evidence_path": "benchmarks/accelerator_benefit/reports/PYTHON_BASELINE_NOT_COMPLETED.md", "notes": "No speedup claimed"},
        {"implementation": "Python end-to-end", "measurement_scope": "file parse plus inference", "status": "NOT_COMPLETED_EQUIVALENCE_FAILED", "evidence_type": "audit", **na_cpu, "evidence_path": "benchmarks/accelerator_benefit/reports/PYTHON_BASELINE_NOT_COMPLETED.md", "notes": "No latency claimed"},
    ])
    py_kernel_ms = python["kernel"]["per_case_median_latency_ms"]["median"] if python else None
    rows = [
        *measured_python_rows,
        ({"implementation": "C/C++ exact RTL translation", "measurement_scope": "loaded samples to final result", "status": "MEASURED_NOW", "evidence_type": "host steady-clock timing after exact 36/36 equivalence", "sample_count": 1_800_000, "latency_ms_median": f"{cpp['per_case_median_latency_ms']['median']:.6f}", "latency_ms_mean": f"{cpp['per_case_median_latency_ms']['mean']:.6f}", "latency_ms_std": f"{cpp['per_case_median_latency_ms']['std']:.6f}", "throughput_samples_per_s": f"{cpp['throughput_samples_per_s_median']:.6f}", "realtime_margin_vs_1ksps": f"{cpp['throughput_samples_per_s_median'] / 1000:.6f}", "speedup_vs_python_kernel": (f"{py_kernel_ms / cpp['per_case_median_latency_ms']['median']:.6f}" if py_kernel_ms else "N/A"), "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "36/36 pred; 36/36 mem", "evidence_path": "benchmarks/accelerator_benefit/results/cpu_cpp_kernel_summary.json", "notes": "Verilator-generated cycle-accurate RTL translation; not a hand-optimized algorithm and not Python"} if cpp else
         {"implementation": "C/C++ integer kernel", "measurement_scope": "loaded samples to final result", "status": "NOT_COMPLETED", "evidence_type": "blocker", **na_cpu, "evidence_path": "benchmarks/accelerator_benefit/reports/CPP_BASELINE_NOT_COMPLETED.md", "notes": "Approximate translation forbidden"}),
        {"implementation": "Pure RTL canonical cycle-derived", "measurement_scope": "stored-data accelerator start to final decision", "status": "CYCLE_DERIVED", "evidence_type": "validated RTL cycle counters", "sample_count": 1_800_000, "latency_ms_median": f"{rtl['total_latency_ms']['median']:.9f}", "latency_ms_mean": f"{rtl['total_latency_ms']['mean']:.9f}", "latency_ms_std": f"{rtl['total_latency_ms']['std']:.9f}", "throughput_samples_per_s": f"{rtl['throughput_samples_per_s']:.6f}", "realtime_margin_vs_1ksps": f"{rtl['realtime_margin_vs_1ksps']:.6f}", "speedup_vs_python_kernel": (f"{py_kernel_ms / rtl['total_latency_ms']['median']:.6f}" if py_kernel_ms else "N/A"), "power_w": "0.099", "power_evidence": "Vivado estimated", "energy_per_decision_j": f"{0.099 * rtl['total_latency_ms']['median'] / 1000:.12f}", "energy_evidence": "estimated power * cycle-derived latency", "LUT": 9719, "FF": 5038, "BRAM": 0, "DSP": 0, "full_input_buffer_required": "no", "output_equivalence": "36/36 pred; 36/36 mem", "evidence_path": "benchmarks/accelerator_benefit/results/rtl_cycle_benchmark.csv", "notes": "Stored-data processing scope aligned to Python kernel; live observation remains 30 minutes"},
        {"implementation": "Existing FPGA functional replay", "measurement_scope": "functional board replay only", "status": "EXISTING_FUNCTIONAL_EVIDENCE", "evidence_type": "UART transcript functional audit", "sample_count": 1_800_000, "latency_ms_median": "N/A", "latency_ms_mean": "N/A", "latency_ms_std": "N/A", "throughput_samples_per_s": "N/A", "realtime_margin_vs_1ksps": "N/A", "speedup_vs_python_kernel": "N/A", "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": 12494, "FF": 8494, "BRAM": 16, "DSP": 3, "full_input_buffer_required": "host streamed", "output_equivalence": "36/36 pred; 36/36 mem", "evidence_path": "benchmarks/accelerator_benefit/results/existing_board_functional_audit.csv", "notes": "Resources are complete MicroBlaze system, not bare core"},
    ]
    for name, scope in [
        ("Future board accelerator-core timing", "hardware profile counter"),
        ("Future MicroBlaze board-system kernel timing", "MicroBlaze feed start to final_valid"),
        ("Future host-to-board timing", "host transfer start to host final result"),
    ]:
        rows.append({"implementation": name, "measurement_scope": scope, "status": "PENDING_BOARD", "evidence_type": "PENDING_BOARD", "sample_count": 1_800_000, "latency_ms_median": "PENDING_BOARD", "latency_ms_mean": "PENDING_BOARD", "latency_ms_std": "PENDING_BOARD", "throughput_samples_per_s": "PENDING_BOARD", "realtime_margin_vs_1ksps": "PENDING_BOARD", "speedup_vs_python_kernel": "N/A", "power_w": "PENDING_BOARD", "power_evidence": "PENDING_BOARD", "energy_per_decision_j": "PENDING_BOARD", "energy_evidence": "PENDING_BOARD", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "scope-dependent", "output_equivalence": "PENDING_BOARD", "evidence_path": "benchmarks/accelerator_benefit/READY_FOR_BOARD_BENCHMARK.md", "notes": "Pending is never represented as zero"})
    write_csv(RESULTS / "accelerator_benefit_summary.csv", rows, fields)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def figure(name: str, title: str, lines: list[str], boxes: list[tuple[str, str, str]]) -> None:
    img = Image.new("RGB", (1800, 1050), "#f7f9fc")
    draw = ImageDraw.Draw(img)
    draw.text((80, 55), title, fill="#10233f", font=font(48, True))
    draw.line((80, 125, 1720, 125), fill="#4c78a8", width=5)
    y = 175
    for label, value, status in boxes:
        color = {"CYCLE_DERIVED": "#4c78a8", "ESTIMATED": "#f28e2b", "PENDING_BOARD": "#b0b7c3", "AUDIT": "#59a14f", "N/A": "#d9dce2"}.get(status, "#76b7b2")
        draw.rounded_rectangle((90, y, 1710, y + 125), radius=18, fill="white", outline=color, width=5)
        draw.text((125, y + 20), label, fill="#15263c", font=font(30, True))
        draw.text((920, y + 20), value, fill=color, font=font(30, True))
        draw.text((125, y + 72), status, fill="#4f5b6b", font=font(22))
        y += 145
    y = max(y + 10, 770)
    for line in lines:
        draw.text((90, y), line, fill="#3f4b5c", font=font(22))
        y += 32
    png = FIGURES / f"{name}.png"
    pdf = FIGURES / f"{name}.pdf"
    FIGURES.mkdir(parents=True, exist_ok=True)
    img.save(png, dpi=(180, 180))
    img.save(pdf, "PDF", resolution=180.0)


def generate_figures(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None) -> None:
    cpu_boxes = ([
        ("Python integer kernel", f"{python['kernel']['per_case_median_latency_ms']['median']:.3f} ms", "MEASURED_NOW"),
    ] if python else [("Python integer kernel", "NOT COMPLETED (equivalence gate)", "AUDIT")])
    if cpp:
        cpu_boxes.append(("C++ exact RTL translation", f"{cpp['per_case_median_latency_ms']['median']:.3f} ms", "MEASURED_NOW"))
    cpu_boxes.append(("Pure RTL", f"{rtl['total_latency_ms']['median']:.6f} ms", "CYCLE_DERIVED"))
    specs = [
        ("01_cpu_vs_rtl_latency", "Host and RTL stored-data latency", cpu_boxes, ("Python and RTL stored-data scopes are compared; C++ remains a generated RTL translation." if python else "Python latency and Python speedup remain absent.")),
        ("02_throughput_realtime_margin", "Throughput and real-time margin", [("Pure RTL acceptance", f"{rtl['throughput_msamples_per_s']:.6f} MSamples/s", "CYCLE_DERIVED"), ("Margin versus 1 kSPS", f"{rtl['realtime_margin_vs_1ksps']:.2f}x", "CYCLE_DERIVED")], "Stored-data processing; live final decision still needs 30 minutes."),
        ("03_resource_scope", "Resource scope comparison", [("Pure RTL accelerator", "9719 LUT / 5038 FF / 0 BRAM / 0 DSP", "AUDIT"), ("MicroBlaze replay system", "12494 LUT / 8494 FF / 16 BRAM / 3 DSP", "AUDIT")], "Scopes differ: the latter includes CPU, memory, UART, interconnect, and feeder."),
        ("04_streaming_memory", "Streaming-memory benefit", [("Full raw window avoided", "2,700,000 bytes", "CYCLE_DERIVED"), ("All pure-RTL FF state upper bound", "<=629.75 bytes", "AUDIT")], "The FF upper bound includes pipeline, control, and interface state."),
        ("05_power_energy_status", "Power and energy evidence status", [("Pure RTL power", "0.099 W Vivado estimate", "ESTIMATED"), ("Estimated energy", f"{0.099 * rtl['total_latency_ms']['median'] / 1000:.9f} J", "ESTIMATED"), ("Physical board", "PENDING_BOARD", "PENDING_BOARD"), ("CPU energy", "N/A", "N/A")], "No estimated value is presented as measured."),
        ("06_benchmark_scope_diagram", "Benchmark scopes remain separate", [("CPU kernel", "loaded samples -> result", "AUDIT"), ("RTL cycles", "accelerator start -> final_valid", "CYCLE_DERIVED"), ("Existing board", "functional equivalence only", "AUDIT"), ("Future board", "timer-based scopes", "PENDING_BOARD")], "No cross-scope speedup is calculated."),
        ("07_future_board_completion", "Future board measurement completion", [("1. Program immutable BIT/ELF", "prepared", "AUDIT"), ("2. Execute 36 streams", "PENDING_BOARD", "PENDING_BOARD"), ("3. Parse hardware counters", "parser ready", "AUDIT"), ("4. Regenerate reports", "deterministic command ready", "AUDIT")], "Pending values are never drawn as zero."),
    ]
    index = ["# Figure Index", "", "| Figure | Source CSV | Scope | Evidence | Limitation |", "|---|---|---|---|---|"]
    for name, title, boxes, limitation in specs:
        source = FIGURES / f"{name}_source.csv"
        write_csv(source, [{"label": a, "value": b, "status": c} for a, b, c in boxes], ["label", "value", "status"])
        figure(name, title, [f"Source: {repo_rel(source)}", f"Limitation: {limitation}"], boxes)
        index.append(f"| {name} | `{repo_rel(source)}` | {title} | mixed, explicitly labeled | {limitation} |")
    write_text(FIGURES / "FIGURE_INDEX.md", "\n".join(index))


def generate_board_docs() -> None:
    schema = ["case_id", "sample_count", "core_cycles", "core_latency_ms", "system_cycles", "system_latency_ms", "samples_per_second", "realtime_margin", "final_pred", "final_mem_NSR", "final_mem_CHF", "final_mem_ARR", "final_mem_AFF", "pred_match", "mem_match", "timing_source", "timer_frequency_hz"]
    write_csv(BOARD / "result_schema.csv", [], schema)
    write_text(BOARD / "transcript_example.txt", """CASE_ID=AFF_afdb_06995_chunk01
BOARD_BENCH sample_count=1800000 core_cycles_lo=PENDING_BOARD core_cycles_hi=PENDING_BOARD system_cycles_lo=PENDING_BOARD system_cycles_hi=PENDING_BOARD final_pred=PENDING_BOARD final_mem_NSR=PENDING_BOARD final_mem_CHF=PENDING_BOARD final_mem_ARR=PENDING_BOARD final_mem_AFF=PENDING_BOARD timing_source=accelerator_profile_counter timer_frequency_hz=100000000
SNN_ECG_FULL_REPLAY_BOARD_PASS
""")
    build_log = BOARD / "build" / "build_instrumented_app.log"
    status_path = BOARD / "build" / "build_status.json"
    prior_status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    elf = BOARD / "build" / "snn_ecg_mb_full_replay_benchmark.elf"
    built = prior_status.get("status") == "built" and elf.exists()
    if built:
        prior_status.update({"physical_execution": "NOT_EXECUTED_NO_BOARD", "instrumented_elf": repo_rel(elf), "elf_sha256": sha256(elf)})
        write_json(status_path, prior_status)
        build_note = f"The instrumented ELF was built with Vitis 2020.2 (`{repo_rel(elf)}`, SHA256 `{sha256(elf)}`). Physical execution remains PENDING_BOARD."
    else:
        build_status = {
            "status": "BUILD_FAILED_PLATFORM_GENERATION",
            "physical_execution": "NOT_EXECUTED_NO_BOARD",
            "toolchain": "Vitis 2020.2 / MicroBlaze GCC found",
            "failure": "fresh big-endian platform generation failed before BSP destination creation",
            "source_libgloss_exists": True,
            "log": repo_rel(build_log),
            "instrumented_elf": "NOT_GENERATED",
        }
        write_json(status_path, build_status)
        build_note = "The local fresh-platform attempt failed during big-endian BSP generation. The source `libgloss.a` exists; the failure is a destination/platform-generation issue. See `build/build_status.json`."
    write_text(BOARD / "README.md", f"""# Future Board Timing Package

Status: **PENDING_BOARD**. No USB/JTAG probing or board execution was performed.

The instrumented application uses existing 64-bit accelerator profile registers. `core_cycles` is the hardware last-decision counter; `system_cycles` is the total transaction counter. UART printing occurs after counters stop. The existing platform has no independent AXI Timer, so scope limitations remain explicit.

Build:

```powershell
python benchmarks/accelerator_benefit/board/build_instrumented_app.py
```

{build_note}

Future execution after repairing the Vitis installation and connecting a Nexys A7-100T:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port COM5 --program
python benchmarks/accelerator_benefit/board/parse_board_benchmark.py
python benchmarks/accelerator_benefit/tools/generate_benchmark_artifacts.py
```

Dependencies: Python 3, NumPy, Pillow, and pyserial for the existing UART runner.
""")


def ready_doc() -> None:
    artifacts = {row["artifact"]: row["sha256"] for row in read_csv(RESULTS / "immutable_artifact_hashes.csv")}
    bit = "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit"
    xsa = "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa"
    elf = "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf"
    state = json.loads((RESULTS / "repository_start_state.json").read_text(encoding="utf-8"))
    instrumented = BOARD / "build" / "snn_ecg_mb_full_replay_benchmark.elf"
    instrumented_line = (f"- instrumented ELF `{repo_rel(instrumented)}`: `{sha256(instrumented)}`" if instrumented.exists() else "- instrumented ELF: **PENDING_BUILD**")
    build_instruction = ("The instrumented ELF is already built. Rebuild only when intentionally verifying the same source/XSA:\n\n```powershell\npython benchmarks/accelerator_benefit/board/build_instrumented_app.py\n```" if instrumented.exists() else "Run:\n\n```powershell\npython benchmarks/accelerator_benefit/board/build_instrumented_app.py\n```")
    write_text(BENCH / "READY_FOR_BOARD_BENCHMARK.md", f"""# READY FOR BOARD BENCHMARK

Status: **PENDING_BOARD**; deterministic package prepared in NO_BOARD mode.

## 1. Hardware

Nexys A7-100T, USB/JTAG cable, board power, and USB-UART serial connection.

## 2. Software

Vivado/Vitis 2020.2, Digilent cable/UART drivers, Python 3 with NumPy, Pillow, and pyserial.

## 3. Immutable artifacts

- BIT `{bit}`: `{artifacts[bit]}`
- XSA `{xsa}`: `{artifacts[xsa]}`
- existing ELF `{elf}`: `{artifacts[elf]}` (functional replay only)
{instrumented_line}
- dataset manifest: `{state['dataset_manifest_sha256']}`
- locked config: `{state['locked_config_sha256']}`
- locked params file: `{state['locked_params_file_sha256']}`

## 4. Programming

{build_instruction}

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
""")


def reports(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None) -> None:
    latency = rtl["total_latency_ms"]["median"]
    throughput = rtl["throughput_msamples_per_s"]
    margin = rtl["realtime_margin_vs_1ksps"]
    energy = 0.099 * latency / 1000
    cpp_kr = (f"Verilator 기반 exact C++ RTL 변환은 36/36 출력 동등성 검증 후 3회 warm-up과 case당 10회 측정했다. Per-case median의 중앙값은 {cpp['per_case_median_latency_ms']['median']:.6f} ms이다. 이는 Python 대체물이 아니며 별도 scope로 보고한다." if cpp else "Optional C/C++ baseline은 완료되지 않았다.")
    cpp_en = (f"The Verilator-generated exact C++ RTL translation passed 36/36 output equivalence and was measured after three warmups with 10 repetitions per case. The median of per-case median latencies is {cpp['per_case_median_latency_ms']['median']:.6f} ms. It is reported as an independent host scope, not as a Python substitute." if cpp else "The optional C/C++ baseline was not completed.")
    python_kr = (f"Benchmark-scoped Python 정수 clock model은 delayed valid/data staging을 locked RTL과 동일하게 복원하여 pred/mem 36/36 동등성을 통과했다. 1 process/1 thread, 3 warm-up, case당 10회 측정의 kernel per-case median 중앙값은 {python['kernel']['per_case_median_latency_ms']['median']:.6f} ms이며, 동일한 stored-data scope에서 RTL speedup은 {python['kernel']['per_case_median_latency_ms']['median'] / latency:.2f}×이다." if python else "Python equivalence gate와 timing은 아직 완료되지 않았으므로 CPU latency와 speedup을 주장하지 않는다.")
    python_en = (f"The benchmark-scoped exact Python integer clock model passed 36/36 prediction and membrane equivalence. With one process/thread, three warmups, and 10 repetitions per case, its median per-case-median kernel latency is {python['kernel']['per_case_median_latency_ms']['median']:.6f} ms; the like-for-like stored-data RTL speedup is {python['kernel']['per_case_median_latency_ms']['median'] / latency:.2f}×." if python else "The Python equivalence gate and timings are incomplete, so Python latency and speedup are not claimed.")
    kr = f"""# SNN ECG Accelerator Benefit (KR)

## 1. 벤치마크 목적
Locked SNN ECG 4-class IP의 실행 이점을 모델 변경 없이 정량화한다.

## 2. NO_BOARD 실행 조건
물리 Nexys A7 보드는 연결되지 않았다. 보드 latency/power는 PENDING_BOARD이다.

## 3. Locked-model 보호
시작 commit과 config/RTL/dataset/BIT/XSA/ELF/transcript SHA256를 고정했다. 분류 지표 29/36 및 16/19는 변경하지 않았다.

## 4. 공통 데이터와 functional equivalence
동일한 36개 1,800,000-sample stream을 사용했다. Canonical RTL 및 기존 board replay는 final_pred/final_mem 36/36 일치한다. 이는 accuracy 100%가 아니라 기능 동등성이다.

## 5. CPU 방법
{python_kr}

{cpp_kr}

## 6. RTL cycle 방법
sample_gap_cycles=2, 100 MHz, committed profile counters를 사용했다. XSim host wall-clock은 사용하지 않았다.

## 7. 기존 board 기능 증거
36 transcripts, 1,800,000 samples, 30 snapshots, 1 decision, pred/mem 36/36를 audit했다.

## 8. 향후 board timing
기존 64-bit hardware profile counter를 읽고 timing 종료 후 UART를 출력하는 instrumented source와 parser를 준비했다.

## 9. Latency 결과
저장된 30분 ECG stream의 pure RTL cycle-derived 처리 latency는 {latency:.6f} ms이다.

## 10. Throughput
{throughput:.6f} MSamples/s, 1 kSPS 대비 {margin:.2f}× margin이다.

## 11. Real-time 해석
저장 데이터 처리 시간과 live 관찰 시간을 구분한다. Live ECG 최종 판단은 30분 observation window에 의해 제한된다.

## 12. Streaming memory
2.7 MB decimal full raw buffer를 저장하지 않는다. Pure RTL은 BRAM 0, DSP 0이다.

## 13. Resource
Pure RTL 9719 LUT/5038 FF와 MicroBlaze system 12494 LUT/8494 FF/16 BRAM/3 DSP는 scope가 다르다.

## 14. Estimated power/energy
0.099 W는 Vivado estimate이다. **Vivado-estimated power × cycle-derived stored-data processing latency**는 {energy:.12f} J/decision이며 board 측정값이 아니다.

## 15. Board pending
core/system/host latency 및 physical power는 모두 PENDING_BOARD이다.

## 16. 대회 보고서용 문구
“저장된 30분 ECG stream의 accelerator processing latency는 canonical RTL cycle count와 실제 구현 clock으로부터 산출했다. Live operation의 최종 decision latency는 30분 observation window에 의해 제한된다.”

## 17. Board 확보 후 절차
`READY_FOR_BOARD_BENCHMARK.md`의 build, program, 36-case run, parser, integrity 명령을 그대로 실행한다.
"""
    write_text(REPORTS / "ACCELERATOR_BENEFIT_KR.md", kr)
    en = f"""# SNN ECG Accelerator Benefit (EN)

This NO_BOARD study protects the locked classifier and uses the same 36 streams. Canonical RTL is cycle-derived at a verified 100 MHz and sample_gap_cycles=2: {latency:.6f} ms per stored 30-minute stream, {throughput:.6f} MSamples/s, and {margin:.2f}× the 1 kSPS input rate. In live operation, the final result still requires the 30-minute observation window.

Existing FPGA evidence is functional only: 36/36 pred and membrane matches, while classification accuracy remains 29/36. {python_en} {cpp_en}

Pure RTL resources are 9719 LUT, 5038 FF, 0 BRAM, and 0 DSP. The design avoids a 2.7 MB raw full-window buffer. The 0.099 W figure is Vivado-estimated power; estimated energy ({energy:.12f} J) is estimated power times cycle-derived stored-data latency, not measured board energy.

All timer-based board latency and physical board power remain PENDING_BOARD. The instrumented source, build attempt, schema, parser, launcher, and deterministic checklist are ready.
"""
    write_text(REPORTS / "ACCELERATOR_BENEFIT_EN.md", en)
    python_limitation = ("- Python timing is a cycle-explicit reference-model measurement and includes the canonical two idle cycles per accepted sample; it is not an optimized vectorized CPU implementation.\n- Python-to-RTL speedup compares aligned stored-data processing scopes; live observation still takes 30 minutes." if python else "- The exact Python equivalence/timing run is incomplete, so no Python speedup is claimed.")
    write_text(REPORTS / "BENCHMARK_LIMITATIONS.md", f"""# Benchmark Limitations

- No physical board was available; board timing and physical power are pending.
{python_limitation}
- The measured C++ path is a Verilator-generated cycle-accurate RTL translation, not a hand-optimized CPU algorithm and not a Python substitute.
- The raw Vivado power report is not committed; 0.099 W is traceable only through the locked final metrics/report summary.
- Total FF is only an all-state upper bound, not exact persistent inference memory.
- Pure RTL and complete MicroBlaze resource scopes are not directly equivalent.
- Existing UART transcripts are functional evidence, not a timer-based latency study.
- Incompatible board/host timing scopes are never combined.
""")
    claims = [
        {"claim_id": "C1", "claim": "Canonical RTL matches locked board-facing expected outputs 36/36.", "status": "SUPPORTED", "evidence_type": "cycle/profile artifact", "evidence_path": "benchmarks/accelerator_benefit/results/rtl_cycle_benchmark.csv", "limitation": "functional equivalence, not 100% accuracy"},
        {"claim_id": "C2", "claim": f"Stored-data RTL latency is {latency:.6f} ms at 100 MHz.", "status": "SUPPORTED", "evidence_type": "CYCLE_DERIVED", "evidence_path": "benchmarks/accelerator_benefit/results/rtl_cycle_summary.json", "limitation": "not live observation latency"},
        {"claim_id": "C3", "claim": "Live final decision requires a 30-minute observation window.", "status": "SUPPORTED", "evidence_type": "input contract", "evidence_path": "configs/final_submission_locked_model.json", "limitation": "none"},
        {"claim_id": "C4", "claim": "0.099 W is measured board power.", "status": "FORBIDDEN", "evidence_type": "none", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md", "limitation": "Vivado estimate only"},
        ({"claim_id": "C5", "claim": f"Python-kernel to canonical RTL stored-data speedup is {python['kernel']['per_case_median_latency_ms']['median'] / latency:.6f}x.", "status": "SUPPORTED", "evidence_type": "MEASURED_NOW / CYCLE_DERIVED", "evidence_path": "benchmarks/accelerator_benefit/results/accelerator_benefit_summary.csv", "limitation": "stored-data processing only; not live decision latency"} if python else {"claim_id": "C5", "claim": "CPU speedup versus RTL.", "status": "NOT_CLAIMED", "evidence_type": "incomplete equivalence/timing", "evidence_path": "benchmarks/accelerator_benefit/reports/PYTHON_BASELINE_NOT_COMPLETED.md", "limitation": "no completed exact CPU latency"}),
        {"claim_id": "C6", "claim": "Board timer latency.", "status": "PENDING_BOARD", "evidence_type": "pending", "evidence_path": "benchmarks/accelerator_benefit/READY_FOR_BOARD_BENCHMARK.md", "limitation": "no board in this run"},
    ]
    if cpp:
        claims.append({"claim_id": "C7", "claim": f"Exact C++ RTL translation per-case-median aggregate latency is {cpp['per_case_median_latency_ms']['median']:.6f} ms.", "status": "SUPPORTED", "evidence_type": "MEASURED_NOW", "evidence_path": "benchmarks/accelerator_benefit/results/cpu_cpp_kernel_summary.json", "limitation": "generated cycle-accurate host model; not hand-optimized C++ and not Python"})
    write_csv(REPORTS / "CLAIM_REGISTRY.csv", claims, list(claims[0]))


def main() -> int:
    for path in (RESULTS, REPORTS, FIGURES, BOARD, REFERENCE):
        path.mkdir(parents=True, exist_ok=True)
    protocol_hash = generate_protocol()
    generate_hashes(protocol_hash)
    python = generate_cpu_status()
    cpp = generate_cpp_status()
    rtl = generate_rtl()
    generate_board_audit()
    generate_memory_power(rtl)
    generate_comparison(rtl, python, cpp)
    generate_figures(rtl, python, cpp)
    generate_board_docs()
    ready_doc()
    reports(rtl, python, cpp)
    print(json.dumps({"status": "generated", "rtl_latency_ms": rtl["total_latency_ms"]["median"], "throughput_msps": rtl["throughput_msamples_per_s"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
