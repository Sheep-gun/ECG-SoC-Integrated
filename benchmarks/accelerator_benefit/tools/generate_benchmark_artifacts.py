#!/usr/bin/env python3
"""Generate measured-board timing and post-implementation power deliverables."""

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
EXACT_CPP = BENCH / "exact_cpp"
CASES_CSV = REPO / "reports" / "final" / "board_replay_36_cases.csv"
BOARD_CSV = REPO / "reports" / "final" / "board_replay_36_expected_vs_board.csv"
BOARD_TIMING_CSV = BOARD / "board_timing_results.csv"
BOARD_RUN_SUMMARY = BOARD / "future_run" / "batch_summary.json"
POWER_SUMMARY_JSON = BENCH / "power" / "results" / "power_summary.json"
XSIM_CSV = REPO / "reports" / "final" / "fulltop_xsim_final_test_36" / "locked_class_cases_fulltop_xsim_predictions.csv"
LOCKED_CONFIG = REPO / "configs" / "final_submission_locked_model.json"
LOCKED_PARAMS = REPO / "configs" / "recordwise_resplit_seed20260808" / "best_final_membrane_structural_grid_locked.json"
FINAL_METRICS = REPO / "reports" / "final" / "final_metrics.json"
HISTORICAL_PYTHON = REPO / "reports" / "final" / "strict_recordwise" / "structural_final_test_predictions.csv"
CLOCK_HZ = 100_000_000
START_COMMIT = "795d3dbffc8dd3fbb45ad1f4ce39df92e3d33bdc"
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


def load_power_summary() -> dict[str, Any]:
    if not POWER_SUMMARY_JSON.exists():
        raise SystemExit(f"verified power summary missing: {POWER_SUMMARY_JSON}")
    power = json.loads(POWER_SUMMARY_JSON.read_text(encoding="utf-8"))
    scopes = power.get("scopes", {})
    if set(scopes) != {"pure_rtl", "microblaze_system"}:
        raise SystemExit("power summary must contain pure_rtl and microblaze_system scopes")
    for name, scope in scopes.items():
        if scope.get("evidence_class") != "ESTIMATED":
            raise SystemExit(f"{name} power is not labeled ESTIMATED")
        report = REPO / scope["raw_power_report"]
        if not report.exists() or sha256(report) != scope["raw_power_report_sha256"]:
            raise SystemExit(f"{name} raw power report hash mismatch")
    return power


def stats(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "std": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
    }


def load_board_timing() -> dict[str, Any]:
    if not BOARD_TIMING_CSV.exists() or not BOARD_RUN_SUMMARY.exists():
        raise SystemExit("completed board timing CSV and batch summary are required")
    rows = read_csv(BOARD_TIMING_CSV)
    batch = json.loads(BOARD_RUN_SUMMARY.read_text(encoding="utf-8"))
    if len(rows) != 36:
        raise SystemExit(f"expected 36 board timing rows, got {len(rows)}")
    if any(
        int(row["sample_count"]) != 1_800_000
        or int(row["core_cycles"]) <= 0
        or int(row["system_cycles"]) <= 0
        or int(row["core_active_cycles"]) <= 0
        or row["pred_match"] != "1"
        or row["mem_match"] != "1"
        for row in rows
    ):
        raise SystemExit("board timing acceptance failed")
    uart_core = [float(row["core_latency_ms"]) for row in rows]
    uart_transaction = [float(row["system_latency_ms"]) for row in rows]
    uart_throughput = [float(row["samples_per_second"]) for row in rows]
    active_cycles = [int(row["core_active_cycles"]) for row in rows]
    active_ms = [float(row["core_active_latency_ms"]) for row in rows]
    active_run_cycles = [int(row["core_run_active_cycles"]) for row in rows]
    active_run_ms = [float(row["core_run_active_latency_ms"]) for row in rows]
    non_run_cycles = [int(row["non_run_overhead_cycles"]) for row in rows]
    active_throughput = [float(row["core_active_samples_per_second"]) for row in rows]
    input_wait_ms = [int(row["profile_input_wait_cycles"]) * 1000.0 / int(row["timer_frequency_hz"]) for row in rows]

    cases = {row["case_id"]: row for row in read_csv(CASES_CSV)}
    xsim = {row["case_id"]: row for row in read_csv(XSIM_CSV)}
    xsim_active_by_case: dict[str, int] = {}
    for row in rows:
        case = cases[row["case_id"]]
        xsim_row = xsim[case["source_prediction_case_id"]]
        expected_active = int(xsim_row["prof_total_cycles"]) - int(xsim_row["prof_input_wait_cycles"])
        xsim_active_by_case[row["case_id"]] = expected_active
        if int(row["core_active_cycles"]) != expected_active:
            raise SystemExit(f"board/XSim active-cycle mismatch: {row['case_id']}")
    return {
        "evidence_class": "MEASURED_COUNTERS_AND_DERIVED_ACTIVE_CYCLES",
        "rows": rows,
        "uart_paced_core_counter_interval_ms": stats(uart_core),
        "uart_paced_transaction_counter_interval_ms": stats(uart_transaction),
        "uart_paced_throughput_samples_per_s": stats(uart_throughput),
        "uart_paced_realtime_margin_vs_1ksps": stats([value / 1000 for value in uart_throughput]),
        "input_wait_latency_ms": stats(input_wait_ms),
        "core_active_cycles": stats(active_cycles),
        "core_active_latency_ms": stats(active_ms),
        "core_run_active_cycles": stats(active_run_cycles),
        "core_run_active_latency_ms": stats(active_run_ms),
        "non_run_overhead_cycles": stats(non_run_cycles),
        "core_active_throughput_samples_per_s": stats(active_throughput),
        "core_active_realtime_margin_vs_1ksps": stats([value / 1000 for value in active_throughput]),
        "active_cycle_unique_values": sorted(set(active_cycles)),
        "xsim_active_cycle_unique_values": sorted(set(xsim_active_by_case.values())),
        "xsim_active_cycle_crosscheck": "36/36",
        "system_compute_latency_status": "NOT_MEASURED_REQUIRES_PRELOAD_AND_INDEPENDENT_TIMER",
        "core_system_equal_cases": sum(row["core_cycles"] == row["system_cycles"] for row in rows),
        "classification_correct": batch["classification_correct"],
        "classification_total": batch["classification_total"],
        "pred_match_correct": batch["pred_match_correct"],
        "pred_match_total": batch["pred_match_total"],
        "final_mem_match_values": batch["final_mem_match_correct"] * 4,
        "final_mem_total_values": batch["final_mem_match_total"] * 4,
        "port": batch["uart_port"],
        "baud": batch["baud"],
    }


def generate_protocol() -> str:
    text = """# Frozen Accelerator-Benefit Benchmark Protocol

- Mode: **BOARD_MEASURED_TIMING_AND_VIVADO_ESTIMATED_POWER**
- Starting commit: `795d3dbffc8dd3fbb45ad1f4ce39df92e3d33bdc`
- Branch: `codex/accelerator-benefit-benchmark`
- Locked model: `structural_guarded_silent_aff_1008710`
- Cases: the 36 rows in `reports/final/board_replay_36_cases.csv`
- Input: signed 12-bit, 1,800,000 samples per case
- Canonical RTL cadence: `sample_gap_cycles=2`
- Clock: 100 MHz, verified by the 10.000 ns constraints and implemented-system timing report
- CPU validity gate: timing is reportable only after current locked Python output matches canonical RTL `final_pred` and all four `final_mem` values 36/36.
- RTL scope: active cycles are `prof_total_cycles - prof_input_wait_cycles`; XSim host wall time is forbidden.
- Board core timing: `profile_total - profile_input_wait`, derived from two measured 100 MHz hardware counters in each of 36 UART transcripts.
- Board raw transaction interval: retained only as a UART-paced transport diagnostic.
- Integrated-system compute latency: not measured; it requires preloaded DDR/BRAM input and an independent system timer.
- Power: post-implementation vectorless Vivado estimate; physical board power is not measured.
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
    if EXACT_CPP.exists():
        paths += sorted(
            path for path in EXACT_CPP.rglob("*")
            if path.is_file() and path.name not in {"integrity_check.json", "performance_integrity.json"}
        )
    rows = [{"artifact": repo_rel(path), "sha256": sha256(path), "bytes": path.stat().st_size} for path in paths]
    rows.append({"artifact": repo_rel(RESULTS / "benchmark_dataset_manifest.csv"), "sha256": sha256(RESULTS / "benchmark_dataset_manifest.csv"), "bytes": (RESULTS / "benchmark_dataset_manifest.csv").stat().st_size})
    rows.append({"artifact": repo_rel(REPORTS / "BENCHMARK_PROTOCOL.md"), "sha256": protocol_hash, "bytes": (REPORTS / "BENCHMARK_PROTOCOL.md").stat().st_size})
    write_csv(RESULTS / "immutable_artifact_hashes.csv", rows, ["artifact", "sha256", "bytes"])
    write_json(RESULTS / "repository_start_state.json", {
        "starting_commit_sha": START_COMMIT,
        "branch": "codex/accelerator-benefit-benchmark",
        "mode": "BOARD_MEASURED_TIMING_AND_VIVADO_ESTIMATED_POWER",
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
        "implementation": "Verilator-generated cycle-accurate RTL simulation model",
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
    write_text(REPORTS / "CPP_BASELINE_MEASURED.md", f"""# Verilator RTL Simulation Host Timing

Status: **MEASURED_NOW**.

This is host timing of a Verilator-generated, cycle-accurate simulation model of the unchanged locked RTL. It is **not** the hand-written Exact C++ native CPU inference baseline and is not treated as an optimized CPU implementation.

- Functional gate: 36/36 `final_pred` and 36/36 all four `final_mem` values.
- Timing: 3 untimed warmups followed by 10 measured runs per case (360 measured runs).
- Scope: samples already loaded in memory through final result, one model instance, one host thread.
- Per-case-median aggregate latency: median {summary['per_case_median_latency_ms']['median']:.6f} ms, mean {summary['per_case_median_latency_ms']['mean']:.6f} ms, population standard deviation {summary['per_case_median_latency_ms']['std']:.6f} ms, IQR {summary['per_case_median_latency_ms']['iqr']:.6f} ms.
- Median measured throughput: {summary['throughput_samples_per_s_median'] / 1e6:.6f} MSamples/s.

This simulation-runtime timing is reported independently and has no CPU-baseline speedup claim. The native CPU baseline is documented under `exact_cpp/`.
""")
    stale = REPORTS / "CPP_BASELINE_NOT_COMPLETED.md"
    if stale.exists():
        stale.unlink()
    return summary


def generate_native_cpp_status() -> dict[str, Any] | None:
    summary_path = EXACT_CPP / "results/exact_cpp_cpu_summary.csv"
    raw_path = EXACT_CPP / "results/exact_cpp_cpu_raw.csv"
    performance_path = EXACT_CPP / "results/performance_integrity.json"
    post_path = EXACT_CPP / "results/post_benchmark_equivalence.json"
    comparison_path = EXACT_CPP / "results/cpu_fpga_comparison.csv"
    if not EXACT_CPP.exists():
        return None
    required = (summary_path, raw_path, performance_path, post_path, comparison_path)
    if not all(path.exists() for path in required):
        raise SystemExit("incomplete transaction-level Exact C++ benchmark package")
    performance = json.loads(performance_path.read_text(encoding="utf-8"))
    post = json.loads(post_path.read_text(encoding="utf-8"))
    if performance.get("status") != "pass" or post.get("status") != "pass":
        raise SystemExit("transaction-level Exact C++ equivalence/performance gate failed")
    raw = read_csv(raw_path)
    if len(raw) != 720 or len({row["case_id"] for row in raw}) != 36:
        raise SystemExit("transaction-level Exact C++ raw result cardinality failed")
    if any(
        row.get("output_exact") != "1"
        or row.get("accepted_samples") != "1800000"
        or row.get("snapshots") != "30"
        or row.get("decisions") != "1"
        for row in raw
    ):
        raise SystemExit("transaction-level Exact C++ raw equivalence failed")
    summary_rows = read_csv(summary_path)

    def mode_summary(mode: str) -> dict[str, Any]:
        cases = [row for row in summary_rows if row["scope"] == "case" and row["mode"] == mode]
        aggregate = [row for row in summary_rows if row["scope"] == "all_cases" and row["mode"] == mode]
        if len(cases) != 36 or len(aggregate) != 1:
            raise SystemExit(f"transaction-level Exact C++ {mode} summary cardinality failed")
        if any(row["runs"] != "10" or row["output_exact_count"] != "10" for row in cases):
            raise SystemExit(f"transaction-level Exact C++ {mode} summary equivalence failed")
        medians = [float(row["latency_median_ms"]) for row in cases]
        all_row = aggregate[0]
        return {
            "scope": mode,
            "all_run_latency_ms": {
                "median": float(all_row["latency_median_ms"]),
                "mean": float(all_row["latency_mean_ms"]),
                "std": float(all_row["latency_stddev_ms"]),
                "min": float(all_row["latency_min_ms"]),
                "max": float(all_row["latency_max_ms"]),
            },
            "per_case_median_latency_ms": {
                "median": statistics.median(medians),
                "mean": statistics.mean(medians),
                "std": statistics.pstdev(medians),
                "min": min(medians),
                "max": max(medians),
                "q1": quantile(medians, 0.25),
                "q3": quantile(medians, 0.75),
                "iqr": quantile(medians, 0.75) - quantile(medians, 0.25),
            },
            "throughput_samples_per_s_median": float(all_row["samples_per_s_median"]),
        }

    comparison = read_csv(comparison_path)
    if len(comparison) != 1:
        raise SystemExit("transaction-level Exact C++ FPGA comparison cardinality failed")
    return {
        "status": "MEASURED_NOW",
        "implementation": "hand-written single-thread transaction-level exact C++",
        "kernel": mode_summary("kernel"),
        "end_to_end": mode_summary("end_to_end"),
        "fpga_core_speedup_estimate": float(comparison[0]["ratio_cpu_over_fpga"]),
        "output_equivalence": "36/36 final_pred; 144/144 final_mem; 1080/1080 snapshots",
        "run_evidence": repo_rel(raw_path),
        "report_evidence": repo_rel(EXACT_CPP / "reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md"),
    }


def generate_rtl() -> dict[str, Any]:
    cases = read_csv(CASES_CSV)
    xsim = {row["case_id"]: row for row in read_csv(XSIM_CSV)}
    fields = [
        "case_id", "sample_gap_cycles", "clock_frequency_hz", "prof_total_cycles",
        "prof_run_cycles", "prof_input_wait_cycles", "accepted_samples", "windows",
        "decisions", "total_latency_ms", "run_latency_ms", "input_wait_latency_ms",
        "active_total_cycles", "active_total_latency_ms", "active_run_cycles",
        "active_run_latency_ms", "non_run_overhead_cycles", "active_throughput_samples_per_s",
        "active_realtime_margin", "gap_inclusive_throughput_samples_per_s",
        "gap_inclusive_realtime_margin", "final_pred_match", "final_mem_match",
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
        active_total = total - wait
        active_run = run - wait
        non_run = total - run
        row = {
            "case_id": case["case_id"], "sample_gap_cycles": 2, "clock_frequency_hz": CLOCK_HZ,
            "prof_total_cycles": total, "prof_run_cycles": run, "prof_input_wait_cycles": wait,
            "accepted_samples": accepted, "windows": int(src["prof_windows"]),
            "decisions": int(src["prof_decisions"]),
            "total_latency_ms": f"{total * 1000 / CLOCK_HZ:.9f}",
            "run_latency_ms": f"{run * 1000 / CLOCK_HZ:.9f}",
            "input_wait_latency_ms": f"{wait * 1000 / CLOCK_HZ:.9f}",
            "active_total_cycles": active_total,
            "active_total_latency_ms": f"{active_total * 1000 / CLOCK_HZ:.9f}",
            "active_run_cycles": active_run,
            "active_run_latency_ms": f"{active_run * 1000 / CLOCK_HZ:.9f}",
            "non_run_overhead_cycles": non_run,
            "active_throughput_samples_per_s": f"{accepted * CLOCK_HZ / active_total:.6f}",
            "active_realtime_margin": f"{accepted * CLOCK_HZ / active_total / 1000:.6f}",
            "gap_inclusive_throughput_samples_per_s": f"{accepted * CLOCK_HZ / total:.6f}",
            "gap_inclusive_realtime_margin": f"{accepted * CLOCK_HZ / total / 1000:.6f}",
            "final_pred_match": str(pred_match).lower(), "final_mem_match": str(memories).lower(),
        }
        if accepted != 1_800_000 or row["windows"] != 30 or row["decisions"] != 1 or not pred_match or not memories:
            raise SystemExit(f"RTL acceptance failed: {case['case_id']}")
        rows.append(row)
    write_csv(RESULTS / "rtl_cycle_benchmark.csv", rows, fields)
    gap_inclusive_latencies = [float(row["total_latency_ms"]) for row in rows]
    active_latencies = [float(row["active_total_latency_ms"]) for row in rows]
    active_throughput = [float(row["active_throughput_samples_per_s"]) for row in rows]
    summary = {
        "status": "COUNTER_DERIVED", "case_count": 36, "sample_gap_cycles": 2,
        "clock_frequency_hz": CLOCK_HZ,
        "clock_evidence": [
            "constraints/snn_ecg_axi_ooc.xdc: create_clock period 10.000 ns",
            "constraints/nexys_a7_microblaze_full_replay.xdc: create_clock period 10.000 ns",
            "results/board_replay/microblaze_full_replay/reports/system_timing_summary.rpt: 100.000 MHz",
        ],
        "gap_inclusive_total_latency_ms": stats(gap_inclusive_latencies),
        "active_total_cycles": stats([int(row["active_total_cycles"]) for row in rows]),
        "active_total_latency_ms": stats(active_latencies),
        "active_run_cycles": stats([int(row["active_run_cycles"]) for row in rows]),
        "non_run_overhead_cycles": stats([int(row["non_run_overhead_cycles"]) for row in rows]),
        "active_throughput_samples_per_s": statistics.mean(active_throughput),
        "active_throughput_msamples_per_s": statistics.mean(active_throughput) / 1e6,
        "active_realtime_margin_vs_1ksps": statistics.mean(active_throughput) / 1000,
        "board_active_cycle_crosscheck": "3,601,290 cycles in all 36 board cases",
        "equivalence": "final_pred 36/36; final_mem 36/36",
    }
    write_json(RESULTS / "rtl_cycle_summary.json", summary)
    write_text(REPORTS / "RTL_CYCLE_METHODOLOGY.md", f"""# RTL Cycle Methodology

The committed full-top XSim profile is used at canonical `sample_gap_cycles=2`. Host simulator wall time is not used. The implemented clock is 100 MHz from the 10.000 ns XDC constraint and the committed Vivado timing report.

For each case, active accelerator cycles are `prof_total_cycles - prof_input_wait_cycles`. The input-wait counter increments only while the core is in RUN, ready to accept a sample, and `sample_valid` is absent. Internal back-pressure cycles, snapshot/decision work, and non-RUN control overhead therefore remain in the active interval. Latency = active cycles / 100,000,000; throughput = 1,800,000 / latency; real-time margin = throughput / 1,000.

The XSim active result is {summary['active_total_cycles']['median']:.0f} cycles ({summary['active_total_latency_ms']['median']:.6f} ms), exactly matching all 36 board-counter differences. The canonical gap-inclusive XSim interval remains {summary['gap_inclusive_total_latency_ms']['median']:.6f} ms and is not used as no-stall core latency. All 36 rows validate 1,800,000 accepted samples, 30 windows, one decision, final_pred exact, and final_mem exact. Live ECG still requires 30 minutes to observe the decision window.
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
    power = load_power_summary()
    board = load_board_timing()
    pure = power["scopes"]["pure_rtl"]
    system = power["scopes"]["microblaze_system"]
    pure_util = pure["utilization"]
    memory = [
        {"item": "hypothetical_full_30min_raw_input", "category": "avoided_input_buffer", "bits": 21_600_000, "bytes": 2_700_000, "status": "derived", "evidence": "1800000 samples * 12 bits", "notes": "not instantiated"},
        {"item": "pure_rtl_total_flip_flops", "category": "all_sequential_state_upper_bound", "bits": pure_util["flip_flop"], "bytes": pure_util["flip_flop"] / 8, "status": "post_implementation_reported", "evidence": pure["utilization_report"], "notes": "includes persistent, pipeline, control, and interface state; not exact inference memory"},
        {"item": "persistent_inference_state", "category": "persistent_state", "bits": f"<={pure_util['flip_flop']}", "bytes": f"<={pure_util['flip_flop'] / 8}", "status": "upper_bound", "evidence": pure["utilization_report"], "notes": "exact post-synthesis category split unavailable"},
        {"item": "pipeline_control_interface_state", "category": "nonpersistent_or_control", "bits": f"included_in_{pure_util['flip_flop']}", "bytes": f"included_in_{pure_util['flip_flop'] / 8}", "status": "not_separately_quantified", "evidence": "RTL declarations and post-route utilization", "notes": "not misreported as inference memory"},
        {"item": "BRAM", "category": "resource", "bits": 0, "bytes": 0, "status": "post_implementation_reported", "evidence": pure["utilization_report"], "notes": "pure RTL"},
        {"item": "DSP", "category": "resource", "bits": "N/A", "bytes": "N/A", "status": "post_implementation_reported", "evidence": pure["utilization_report"], "notes": f"{pure_util['dsp']} DSP"},
    ]
    write_csv(RESULTS / "state_memory_inventory.csv", memory, ["item", "category", "bits", "bytes", "status", "evidence", "notes"])
    write_text(REPORTS / "STREAMING_MEMORY_ANALYSIS.md", f"""# Streaming Memory Analysis

The accelerator updates state sample by sample and does not instantiate a 1,800,000-sample input buffer. Raw full-window storage would be 21,600,000 bits = 2,700,000 bytes (2.7 MB decimal).

Pure RTL uses {pure_util['bram_tile']} BRAM and {pure_util['dsp']} DSP. The {pure_util['flip_flop']:,} post-route FFs provide a conservative {pure_util['flip_flop']:,}-bit ({pure_util['flip_flop'] / 8:.3f}-byte) upper bound on all sequential storage, but this is deliberately not called exact inference-state memory: it includes persistent inference state, pipeline registers, counters, control, and interface state. A per-category split is unavailable.
""")
    pure_energy = pure["total_on_chip_power_w"] * board["core_active_latency_ms"]["median"] / 1000
    rows = [
        {"implementation": "Pure RTL accelerator", "power_w": f"{pure['total_on_chip_power_w']:.6f}", "power_class": "ESTIMATED", "energy_per_decision_j": f"{pure_energy:.12f}", "energy_class": "DERIVED", "evidence_type": "Vivado-estimated power * hardware-counter-derived active core latency", "scope": "accelerator implementation estimate", "evidence_path": f"{pure['raw_power_report']}; {repo_rel(BOARD_TIMING_CSV)}"},
        {"implementation": "MicroBlaze integrated FPGA system", "power_w": f"{system['total_on_chip_power_w']:.6f}", "power_class": "ESTIMATED", "energy_per_decision_j": "NOT_MEASURED", "energy_class": "NOT_MEASURED", "evidence_type": "integrated compute latency unavailable; UART-paced counter is not used", "scope": "MicroBlaze, BRAM, AXI, UART, feeder, and accelerator", "evidence_path": system["raw_power_report"]},
        {"implementation": "Physical FPGA board", "power_w": "NOT_MEASURED", "power_class": "NOT_MEASURED", "energy_per_decision_j": "NOT_MEASURED", "energy_class": "NOT_MEASURED", "evidence_type": "none; no external power meter", "scope": "board input power", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md"},
        {"implementation": "CPU", "power_w": "N/A", "power_class": "N/A", "energy_per_decision_j": "N/A", "energy_class": "N/A", "evidence_type": "none", "scope": "CPU", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md"},
    ]
    write_csv(RESULTS / "power_energy_summary.csv", rows, list(rows[0]))
    write_text(REPORTS / "POWER_ENERGY_METHODOLOGY.md", f"""# Power and Energy Methodology

- Pure RTL: {pure['total_on_chip_power_w']:.6f} W is a post-implementation vectorless Vivado estimate, not board-measured power. Derived energy is **estimated power x hardware-counter-derived active core latency**: {pure['total_on_chip_power_w']:.6f} W x {board['core_active_latency_ms']['median'] / 1000:.9f} s = {pure_energy:.12f} J/decision.
- The active core latency comes from `profile_total - profile_input_wait` in each board transcript. Both operands are MEASURED 100 MHz hardware counters; the subtraction is DERIVED. It retains internal stalls and snapshot/final-decision overhead.
- Integrated system: {system['total_on_chip_power_w']:.6f} W is a separate post-implementation vectorless estimate for MicroBlaze, BRAM, AXI, UART, feeder, and accelerator. Integrated compute energy is **NOT_MEASURED/NOT DERIVED** because the current BIT has neither preloaded input nor an independent system timer. Multiplying this power by the UART-paced replay interval would measure transport waiting, not integrated compute energy.
- Activity: no SAIF/VCD was supplied. Both results use Vivado default vectorless propagation and are explicitly labeled **Post-implementation vectorless Vivado power estimate**.
- Physical board power was not measured because no external power meter was available. These values must not be described as board power or measured accelerator energy.
- CPU: N/A because no RAPL/powercap or equivalent defensible counter is available.

Runtime alone is never converted into energy-efficiency speedup.
""")


def generate_comparison(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None, native_cpp: dict[str, Any] | None) -> None:
    power = load_power_summary()
    board = load_board_timing()
    pure = power["scopes"]["pure_rtl"]
    system_power = power["scopes"]["microblaze_system"]
    exact_ms = native_cpp["kernel"]["all_run_latency_ms"]["median"] if native_cpp else None
    core_ms = board["core_active_latency_ms"]["median"]
    uart_interval_ms = board["uart_paced_transaction_counter_interval_ms"]["median"]
    fields = ["implementation", "measurement_scope", "status", "evidence_type", "sample_count", "latency_ms_median", "latency_ms_mean", "latency_ms_std", "throughput_samples_per_s", "realtime_margin_vs_1ksps", "speedup_vs_python_kernel", "speedup_vs_exact_cpp_kernel", "power_w", "power_evidence", "energy_per_decision_j", "energy_evidence", "LUT", "FF", "BRAM", "DSP", "full_input_buffer_required", "output_equivalence", "evidence_path", "notes"]
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
    py_all_run_ms = python["kernel"]["all_run_latency_ms"]["median"] if python else None
    native_rows = []
    if native_cpp:
        native_kernel = native_cpp["kernel"]
        native_e2e = native_cpp["end_to_end"]
        native_rows = [
            {"implementation": "Exact C++ native CPU kernel", "measurement_scope": "preloaded signed-12 samples to final result", "status": "MEASURED_NOW", "evidence_type": "QueryPerformanceCounter after full exact-equivalence gate", "sample_count": 1_800_000, "latency_ms_median": f"{native_kernel['all_run_latency_ms']['median']:.6f}", "latency_ms_mean": f"{native_kernel['all_run_latency_ms']['mean']:.6f}", "latency_ms_std": f"{native_kernel['all_run_latency_ms']['std']:.6f}", "throughput_samples_per_s": f"{native_kernel['throughput_samples_per_s_median']:.6f}", "realtime_margin_vs_1ksps": f"{native_kernel['throughput_samples_per_s_median'] / 1000:.6f}", "speedup_vs_python_kernel": (f"{py_all_run_ms / native_kernel['all_run_latency_ms']['median']:.6f}" if py_all_run_ms else "N/A"), "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "36/36 pred; 144/144 mem; 1080/1080 snapshots", "evidence_path": "benchmarks/accelerator_benefit/exact_cpp/reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md", "notes": f"hand-written transaction-level CPU code; single thread; fixed affinity; -O3 -march=native; all-360-run median; active-core comparison {native_kernel['all_run_latency_ms']['median'] / core_ms:.6f}x"},
            {"implementation": "Exact C++ native CPU end-to-end", "measurement_scope": "file open/parse through flushed result JSON", "status": "MEASURED_NOW", "evidence_type": "QueryPerformanceCounter after full exact-equivalence gate", "sample_count": 1_800_000, "latency_ms_median": f"{native_e2e['all_run_latency_ms']['median']:.6f}", "latency_ms_mean": f"{native_e2e['all_run_latency_ms']['mean']:.6f}", "latency_ms_std": f"{native_e2e['all_run_latency_ms']['std']:.6f}", "throughput_samples_per_s": f"{native_e2e['throughput_samples_per_s_median']:.6f}", "realtime_margin_vs_1ksps": f"{native_e2e['throughput_samples_per_s_median'] / 1000:.6f}", "speedup_vs_python_kernel": "N/A", "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "36/36 pred; 144/144 mem; 1080/1080 snapshots", "evidence_path": "benchmarks/accelerator_benefit/exact_cpp/reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md", "notes": "hand-written transaction-level CPU code; includes file open, signed-12 parsing, inference, and result JSON write/flush"},
        ]
    rows = [
        *measured_python_rows,
        *native_rows,
        ({"implementation": "Verilator-generated RTL simulation", "measurement_scope": "host runtime of generated cycle-accurate RTL model", "status": "MEASURED_NOW", "evidence_type": "host steady-clock simulation timing after exact 36/36 equivalence", "sample_count": 1_800_000, "latency_ms_median": f"{cpp['per_case_median_latency_ms']['median']:.6f}", "latency_ms_mean": f"{cpp['per_case_median_latency_ms']['mean']:.6f}", "latency_ms_std": f"{cpp['per_case_median_latency_ms']['std']:.6f}", "throughput_samples_per_s": f"{cpp['throughput_samples_per_s_median']:.6f}", "realtime_margin_vs_1ksps": f"{cpp['throughput_samples_per_s_median'] / 1000:.6f}", "speedup_vs_python_kernel": "N/A", "power_w": "N/A", "power_evidence": "N/A", "energy_per_decision_j": "N/A", "energy_evidence": "N/A", "LUT": "N/A", "FF": "N/A", "BRAM": "N/A", "DSP": "N/A", "full_input_buffer_required": "yes", "output_equivalence": "36/36 pred; 36/36 mem", "evidence_path": "benchmarks/accelerator_benefit/results/cpu_cpp_kernel_summary.json", "notes": "Verilator-generated RTL simulation/verification runtime; explicitly not the Exact C++ native CPU baseline"} if cpp else
         {"implementation": "C/C++ integer kernel", "measurement_scope": "loaded samples to final result", "status": "NOT_COMPLETED", "evidence_type": "blocker", **na_cpu, "evidence_path": "benchmarks/accelerator_benefit/reports/CPP_BASELINE_NOT_COMPLETED.md", "notes": "Approximate translation forbidden"}),
        {"implementation": "Pure RTL XSim active-cycle cross-check", "measurement_scope": "prof_total minus prof_input_wait", "status": "DERIVED", "evidence_type": "validated RTL counter subtraction", "sample_count": 1_800_000, "latency_ms_median": f"{rtl['active_total_latency_ms']['median']:.9f}", "latency_ms_mean": f"{rtl['active_total_latency_ms']['mean']:.9f}", "latency_ms_std": f"{rtl['active_total_latency_ms']['std']:.9f}", "throughput_samples_per_s": f"{rtl['active_throughput_samples_per_s']:.6f}", "realtime_margin_vs_1ksps": f"{rtl['active_realtime_margin_vs_1ksps']:.6f}", "speedup_vs_python_kernel": (f"{py_kernel_ms / rtl['active_total_latency_ms']['median']:.6f}" if py_kernel_ms else "N/A"), "speedup_vs_exact_cpp_kernel": (f"{exact_ms / rtl['active_total_latency_ms']['median']:.6f}" if exact_ms else "N/A"), "power_w": f"{pure['total_on_chip_power_w']:.6f}", "power_evidence": "ESTIMATED post-implementation vectorless Vivado", "energy_per_decision_j": f"{pure['total_on_chip_power_w'] * rtl['active_total_latency_ms']['median'] / 1000:.12f}", "energy_evidence": "DERIVED estimated power * XSim active-cycle latency", "LUT": pure["utilization"]["lut"], "FF": pure["utilization"]["flip_flop"], "BRAM": pure["utilization"]["bram_tile"], "DSP": pure["utilization"]["dsp"], "full_input_buffer_required": "no", "output_equivalence": "36/36 pred; 144/144 mem", "evidence_path": f"benchmarks/accelerator_benefit/results/rtl_cycle_benchmark.csv; {pure['raw_power_report']}", "notes": "Exactly matches the board active-cycle difference in 36/36 cases"},
        {"implementation": "FPGA board accelerator active-cycle latency", "measurement_scope": "profile_total minus profile_input_wait", "status": "DERIVED", "evidence_type": "difference of two MEASURED 100 MHz FPGA hardware counters", "sample_count": 1_800_000, "latency_ms_median": f"{core_ms:.9f}", "latency_ms_mean": f"{board['core_active_latency_ms']['mean']:.9f}", "latency_ms_std": f"{board['core_active_latency_ms']['std']:.9f}", "throughput_samples_per_s": f"{board['core_active_throughput_samples_per_s']['median']:.6f}", "realtime_margin_vs_1ksps": f"{board['core_active_realtime_margin_vs_1ksps']['median']:.6f}", "speedup_vs_python_kernel": (f"{py_kernel_ms / core_ms:.6f}" if py_kernel_ms else "N/A"), "speedup_vs_exact_cpp_kernel": (f"{exact_ms / core_ms:.6f}" if exact_ms else "N/A"), "power_w": f"{pure['total_on_chip_power_w']:.6f}", "power_evidence": "ESTIMATED post-implementation vectorless Vivado", "energy_per_decision_j": f"{pure['total_on_chip_power_w'] * core_ms / 1000:.12f}", "energy_evidence": "DERIVED estimated Pure RTL power * hardware-counter-derived active latency", "LUT": pure["utilization"]["lut"], "FF": pure["utilization"]["flip_flop"], "BRAM": pure["utilization"]["bram_tile"], "DSP": pure["utilization"]["dsp"], "full_input_buffer_required": "host streamed; input-wait subtracted", "output_equivalence": "36/36 pred; 144/144 mem", "evidence_path": f"{repo_rel(BOARD_TIMING_CSV)}; {pure['raw_power_report']}", "notes": "Retains internal stalls, snapshot/final-decision work, and 1320 non-RUN control cycles; XSim match 36/36"},
        {"implementation": "FPGA board UART-paced transaction diagnostic", "measurement_scope": "raw start-to-final-decision counter including input starvation", "status": "MEASURED", "evidence_type": "100 MHz FPGA hardware counter parsed from UART", "sample_count": 1_800_000, "latency_ms_median": f"{uart_interval_ms:.9f}", "latency_ms_mean": f"{board['uart_paced_transaction_counter_interval_ms']['mean']:.9f}", "latency_ms_std": f"{board['uart_paced_transaction_counter_interval_ms']['std']:.9f}", "throughput_samples_per_s": f"{board['uart_paced_throughput_samples_per_s']['median']:.6f}", "realtime_margin_vs_1ksps": f"{board['uart_paced_realtime_margin_vs_1ksps']['median']:.6f}", "speedup_vs_python_kernel": "N/A", "speedup_vs_exact_cpp_kernel": "N/A", "power_w": f"{system_power['total_on_chip_power_w']:.6f}", "power_evidence": "ESTIMATED post-implementation vectorless Vivado", "energy_per_decision_j": "N/A", "energy_evidence": "N/A; transport-wait interval is not integrated compute latency", "LUT": system_power["utilization"]["lut"], "FF": system_power["utilization"]["flip_flop"], "BRAM": system_power["utilization"]["bram_tile"], "DSP": system_power["utilization"]["dsp"], "full_input_buffer_required": "host streamed", "output_equivalence": "36/36 pred; 144/144 mem", "evidence_path": f"{repo_rel(BOARD_TIMING_CSV)}; {system_power['raw_power_report']}", "notes": "Not used for accelerator or integrated-system speedup/energy; DDR preload plus independent timer is required"},
    ]
    for row in rows:
        if row["status"] == "MEASURED_NOW":
            row["status"] = "MEASURED"
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
    canvas_height = max(1050, 260 + 145 * len(boxes) + 42 * len(lines))
    img = Image.new("RGB", (1800, canvas_height), "#f7f9fc")
    draw = ImageDraw.Draw(img)
    draw.text((80, 55), title, fill="#10233f", font=font(48, True))
    draw.line((80, 125, 1720, 125), fill="#4c78a8", width=5)
    y = 175
    for label, value, status in boxes:
        color = {"CYCLE_DERIVED": "#4c78a8", "DERIVED": "#4c78a8", "MEASURED": "#59a14f", "ESTIMATED": "#f28e2b", "PENDING_BOARD": "#b0b7c3", "AUDIT": "#59a14f", "N/A": "#d9dce2"}.get(status, "#76b7b2")
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


def generate_figures(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None, native_cpp: dict[str, Any] | None) -> None:
    power = load_power_summary()
    board = load_board_timing()
    pure = power["scopes"]["pure_rtl"]
    system = power["scopes"]["microblaze_system"]
    core_ms = board["core_active_latency_ms"]["median"]
    uart_interval_ms = board["uart_paced_transaction_counter_interval_ms"]["median"]
    cpu_boxes = ([
        ("Python integer kernel", f"{python['kernel']['per_case_median_latency_ms']['median']:.3f} ms", "MEASURED"),
    ] if python else [("Python integer kernel", "NOT COMPLETED (equivalence gate)", "AUDIT")])
    if native_cpp:
        cpu_boxes.append(("Exact C++ native CPU kernel", f"{native_cpp['kernel']['all_run_latency_ms']['median']:.3f} ms", "MEASURED"))
    if cpp:
        cpu_boxes.append(("Verilator-generated RTL simulation", f"{cpp['per_case_median_latency_ms']['median']:.3f} ms", "MEASURED"))
    cpu_boxes.append(("Pure RTL XSim active-cycle cross-check", f"{rtl['active_total_latency_ms']['median']:.6f} ms", "DERIVED"))
    cpu_boxes.append(("FPGA board active-cycle latency", f"{core_ms:.6f} ms", "DERIVED"))
    cpu_boxes.append(("UART-paced transaction diagnostic", f"{uart_interval_ms:.3f} ms", "MEASURED"))
    specs = [
        ("01_cpu_vs_rtl_latency", "CPU, RTL, and measured-board latency", cpu_boxes, ("Exact C++ is the native CPU baseline; Verilator is separately labeled RTL simulation runtime." if python else "Python latency and Python speedup remain absent.")),
        ("02_throughput_realtime_margin", "FPGA active-core throughput and real-time margin", [("Active-core throughput", f"{board['core_active_throughput_samples_per_s']['median']:.3f} samples/s", "DERIVED"), ("Margin versus 1 kSPS", f"{board['core_active_realtime_margin_vs_1ksps']['median']:.3f}x", "DERIVED")], "Derived from measured total/input-wait counters; live final decision still needs 30 minutes."),
        ("03_resource_scope", "Post-route resource scope comparison", [("Pure RTL accelerator", f"{pure['utilization']['lut']} LUT / {pure['utilization']['flip_flop']} FF / {pure['utilization']['bram_tile']} BRAM / {pure['utilization']['dsp']} DSP", "DERIVED"), ("MicroBlaze replay system", f"{system['utilization']['lut']} LUT / {system['utilization']['flip_flop']} FF / {system['utilization']['bram_tile']} BRAM / {system['utilization']['dsp']} DSP", "DERIVED")], "Parsed from separate post-route utilization reports."),
        ("04_streaming_memory", "Streaming-memory benefit", [("Full raw window avoided", "2,700,000 bytes", "DERIVED"), ("All pure-RTL FF state upper bound", f"<={pure['utilization']['flip_flop'] / 8:.3f} bytes", "DERIVED")], "The FF upper bound includes pipeline, control, and interface state."),
        ("05_power_energy_status", "Estimated power and derived energy", [("Pure RTL power", f"{pure['total_on_chip_power_w']:.3f} W ESTIMATED", "ESTIMATED"), ("Pure RTL active energy", f"{pure['total_on_chip_power_w'] * core_ms / 1000:.6f} J DERIVED", "DERIVED"), ("Integrated system power", f"{system['total_on_chip_power_w']:.3f} W ESTIMATED", "ESTIMATED"), ("Integrated system energy", "NOT MEASURED", "N/A"), ("Physical board", "NOT MEASURED", "N/A")], "System compute energy requires preloaded input and an independent timer; no external power meter."),
        ("06_benchmark_scope_diagram", "Benchmark scopes remain separate", [("Exact C++ kernel", "MEASURED CPU", "MEASURED"), ("FPGA active cycles", "DERIVED from MEASURED counters", "DERIVED"), ("UART-paced interval", "TRANSPORT DIAGNOSTIC", "MEASURED"), ("Integrated compute latency", "NOT MEASURED", "N/A"), ("Vivado power", "ESTIMATED vectorless", "ESTIMATED")], "Pure RTL energy uses active-core latency; integrated energy remains unavailable."),
        ("07_future_board_completion", "Board measurement completion", [("1. Program immutable BIT/ELF", "complete", "MEASURED"), ("2. Execute 36 streams", "36/36", "MEASURED"), ("3. Parse hardware counters", "complete", "MEASURED"), ("4. Regenerate reports", "complete", "DERIVED")], "Physical board power remains unmeasured."),
    ]
    index = ["# Figure Index", "", "| Figure | Source CSV | Scope | Evidence | Limitation |", "|---|---|---|---|---|"]
    for name, title, boxes, limitation in specs:
        source = FIGURES / f"{name}_source.csv"
        write_csv(source, [{"label": a, "value": b, "status": c} for a, b, c in boxes], ["label", "value", "status"])
        figure(name, title, [f"Source: {repo_rel(source)}", f"Limitation: {limitation}"], boxes)
        index.append(f"| {name} | `{repo_rel(source)}` | {title} | mixed, explicitly labeled | {limitation} |")
    write_text(FIGURES / "FIGURE_INDEX.md", "\n".join(index))


def _legacy_generate_board_docs_unused() -> None:
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


def _legacy_ready_doc_unused() -> None:
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


def _legacy_reports_unused(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None, native_cpp: dict[str, Any] | None) -> None:
    latency = rtl["total_latency_ms"]["median"]
    throughput = rtl["throughput_msamples_per_s"]
    margin = rtl["realtime_margin_vs_1ksps"]
    pure_w = load_power_summary()["scopes"]["pure_rtl"]["total_on_chip_power_w"]
    energy = pure_w * latency / 1000
    cpp_kr = (f"Verilator-generated RTL simulation은 36/36 출력 동등성 검증 후 host runtime을 별도 측정했다. Per-case median의 중앙값은 {cpp['per_case_median_latency_ms']['median']:.6f} ms이다. 이는 Exact C++ native CPU baseline이 아니라 RTL simulation/verification runtime이다." if cpp else "Verilator RTL simulation timing은 완료되지 않았다.")
    cpp_en = (f"The Verilator-generated RTL simulation passed 36/36 output equivalence and its host runtime was measured separately. The median of per-case median latencies is {cpp['per_case_median_latency_ms']['median']:.6f} ms. This is an RTL simulation/verification runtime, not the Exact C++ native CPU baseline." if cpp else "The Verilator RTL simulation timing was not completed.")
    native_kr = (f"Hand-written single-thread transaction-level Exact C++는 final prediction 36/36, final membrane 144/144, Snapshot boundary 1080/1080 동등성 검증 후 측정했다. Kernel 360-run median은 {native_cpp['kernel']['all_run_latency_ms']['median']:.6f} ms이고, measured CPU와 cycle-derived FPGA core를 결합한 명시적 scope의 speedup estimate는 {native_cpp['fpga_core_speedup_estimate']:.6f}x이다." if native_cpp else "")
    native_en = (f"The hand-written single-thread transaction-level Exact C++ baseline passed 36/36 final predictions, 144/144 final membranes, and 1080/1080 Snapshot boundaries. Its kernel median over 360 runs is {native_cpp['kernel']['all_run_latency_ms']['median']:.6f} ms. The explicitly scoped measured-CPU versus cycle-derived FPGA-core speedup estimate is {native_cpp['fpga_core_speedup_estimate']:.6f}x." if native_cpp else "")
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

{native_kr}

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
{pure_w:.6f} W는 power summary에서 읽은 Vivado estimate이다. **Vivado-estimated power × cycle-derived stored-data processing latency**는 {energy:.12f} J/decision이며 board 측정값이 아니다.

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

Existing FPGA evidence is functional only: 36/36 pred and membrane matches, while classification accuracy remains 29/36. {python_en} {native_en} {cpp_en}

Pure RTL resources are reported separately from the integrated system. The design avoids a 2.7 MB raw full-window buffer. The {pure_w:.6f} W figure is read from the verified power summary; estimated energy ({energy:.12f} J) is estimated power times cycle-derived stored-data latency, not measured board energy.

All timer-based board latency and physical board power remain PENDING_BOARD. The instrumented source, build attempt, schema, parser, launcher, and deterministic checklist are ready.
"""
    write_text(REPORTS / "ACCELERATOR_BENEFIT_EN.md", en)
    python_limitation = ("- Python timing is a cycle-explicit reference-model measurement and includes the canonical two idle cycles per accepted sample; it is not an optimized vectorized CPU implementation.\n- Python-to-RTL speedup compares aligned stored-data processing scopes; live observation still takes 30 minutes." if python else "- The exact Python equivalence/timing run is incomplete, so no Python speedup is claimed.")
    write_text(REPORTS / "BENCHMARK_LIMITATIONS.md", f"""# Benchmark Limitations

- No physical board was available; board timing and physical power are pending.
{python_limitation}
- The native Exact C++ baseline is a hand-written transaction-level implementation with formally audited cadence compression; it is not a literal event-driven RTL simulation.
- Its 32.912687x FPGA-core estimate combines measured CPU latency with cycle-derived accelerator-core latency and is not measured board speedup.
- The separately reported Verilator host runtime is RTL simulation/verification evidence, not an Exact C++ or optimized CPU inference baseline; no CPU-baseline speedup is assigned to it.
- The power value is loaded from the verified raw-report summary rather than a numeric source-code constant.
- Total FF is only an all-state upper bound, not exact persistent inference memory.
- Pure RTL and complete MicroBlaze resource scopes are not directly equivalent.
- Existing UART transcripts are functional evidence, not a timer-based latency study.
- Incompatible board/host timing scopes are never combined.
""")
    claims = [
        {"claim_id": "C1", "claim": "Canonical RTL matches locked board-facing expected outputs 36/36.", "status": "SUPPORTED", "evidence_type": "cycle/profile artifact", "evidence_path": "benchmarks/accelerator_benefit/results/rtl_cycle_benchmark.csv", "limitation": "functional equivalence, not 100% accuracy"},
        {"claim_id": "C2", "claim": f"Stored-data RTL latency is {latency:.6f} ms at 100 MHz.", "status": "SUPPORTED", "evidence_type": "CYCLE_DERIVED", "evidence_path": "benchmarks/accelerator_benefit/results/rtl_cycle_summary.json", "limitation": "not live observation latency"},
        {"claim_id": "C3", "claim": "Live final decision requires a 30-minute observation window.", "status": "SUPPORTED", "evidence_type": "input contract", "evidence_path": "configs/final_submission_locked_model.json", "limitation": "none"},
        {"claim_id": "C4", "claim": f"{pure_w:.6f} W is measured board power.", "status": "FORBIDDEN", "evidence_type": "none", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md", "limitation": "Vivado estimate only"},
        ({"claim_id": "C5", "claim": f"Python-kernel to canonical RTL stored-data speedup is {python['kernel']['per_case_median_latency_ms']['median'] / latency:.6f}x.", "status": "SUPPORTED", "evidence_type": "MEASURED_NOW / CYCLE_DERIVED", "evidence_path": "benchmarks/accelerator_benefit/results/accelerator_benefit_summary.csv", "limitation": "stored-data processing only; not live decision latency"} if python else {"claim_id": "C5", "claim": "CPU speedup versus RTL.", "status": "NOT_CLAIMED", "evidence_type": "incomplete equivalence/timing", "evidence_path": "benchmarks/accelerator_benefit/reports/PYTHON_BASELINE_NOT_COMPLETED.md", "limitation": "no completed exact CPU latency"}),
        {"claim_id": "C6", "claim": "Board timer latency.", "status": "PENDING_BOARD", "evidence_type": "pending", "evidence_path": "benchmarks/accelerator_benefit/READY_FOR_BOARD_BENCHMARK.md", "limitation": "no board in this run"},
    ]
    if cpp:
        claims.append({"claim_id": "C7", "claim": f"Verilator-generated RTL simulation per-case-median host runtime is {cpp['per_case_median_latency_ms']['median']:.6f} ms.", "status": "SUPPORTED", "evidence_type": "MEASURED_NOW", "evidence_path": "benchmarks/accelerator_benefit/results/cpu_cpp_kernel_summary.json", "limitation": "RTL simulation/verification runtime; not the Exact C++ native CPU baseline; no CPU speedup claim"})
    if native_cpp:
        claims.append({"claim_id": "C8", "claim": f"Transaction-level Exact C++ kernel all-run median latency is {native_cpp['kernel']['all_run_latency_ms']['median']:.6f} ms.", "status": "SUPPORTED", "evidence_type": "MEASURED_NOW", "evidence_path": "benchmarks/accelerator_benefit/exact_cpp/reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md", "limitation": "single thread; fixed affinity; -O3 -march=native; transaction-level cadence compression"})
        claims.append({"claim_id": "C9", "claim": f"Transaction-level Exact C++ versus cycle-derived FPGA-core speedup estimate is {native_cpp['fpga_core_speedup_estimate']:.6f}x.", "status": "SUPPORTED", "evidence_type": "MEASURED_NOW / CYCLE_DERIVED", "evidence_path": "benchmarks/accelerator_benefit/exact_cpp/results/cpu_fpga_comparison.csv", "limitation": "not measured FPGA/board speedup; excludes host, MicroBlaze, UART, and board system scope"})
    write_csv(REPORTS / "CLAIM_REGISTRY.csv", claims, list(claims[0]))


def generate_board_docs() -> None:
    board = load_board_timing()
    schema = ["case_id", "sample_count", "core_cycles", "core_latency_ms", "system_cycles", "system_latency_ms", "samples_per_second", "realtime_margin", "profile_total_cycles", "profile_run_cycles", "profile_input_wait_cycles", "profile_accepted_samples", "core_active_cycles", "core_active_latency_ms", "core_run_active_cycles", "core_run_active_latency_ms", "non_run_overhead_cycles", "core_active_samples_per_second", "core_active_realtime_margin", "final_pred", "final_mem_NSR", "final_mem_CHF", "final_mem_ARR", "final_mem_AFF", "pred_match", "mem_match", "timing_source", "timer_frequency_hz"]
    write_csv(BOARD / "result_schema.csv", [], schema)
    first_transcript = sorted((BOARD / "future_run" / "transcripts").glob("*.txt"))[0]
    evidence_lines = [
        line for line in first_transcript.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith("SNN_ECG_FULL_REPLAY_READY") or line.startswith("BOARD_BENCH ") or line.startswith("SNN_ECG_FULL_REPLAY_BOARD_PASS")
    ]
    write_text(BOARD / "transcript_example.txt", "\n".join(evidence_lines))
    write_json(BOARD / "board_timing_summary.json", {
        "evidence_class": "MEASURED_COUNTERS_AND_DERIVED_ACTIVE_CYCLES",
        "board": "Nexys A7-100T",
        "uart_port": board["port"],
        "uart_baud": board["baud"],
        "cases_completed": 36,
        "samples_per_case": 1_800_000,
        "snapshots_per_case": 30,
        "decisions_per_case": 1,
        "board_golden_final_pred": "36/36",
        "board_golden_final_membrane_values": "144/144",
        "classification_accuracy": "29/36 (80.56%)",
        "core_active_formula": "profile_total_cycles - profile_input_wait_cycles",
        "core_active_cycles": board["core_active_cycles"],
        "core_active_latency_ms": board["core_active_latency_ms"],
        "core_run_active_cycles": board["core_run_active_cycles"],
        "core_run_active_latency_ms": board["core_run_active_latency_ms"],
        "non_run_overhead_cycles": board["non_run_overhead_cycles"],
        "core_active_throughput_samples_per_s": board["core_active_throughput_samples_per_s"],
        "core_active_realtime_margin_vs_1ksps": board["core_active_realtime_margin_vs_1ksps"],
        "uart_paced_core_counter_interval_ms": board["uart_paced_core_counter_interval_ms"],
        "uart_paced_transaction_counter_interval_ms": board["uart_paced_transaction_counter_interval_ms"],
        "uart_paced_throughput_samples_per_s": board["uart_paced_throughput_samples_per_s"],
        "uart_paced_realtime_margin_vs_1ksps": board["uart_paced_realtime_margin_vs_1ksps"],
        "core_system_equal_cases": board["core_system_equal_cases"],
        "input_wait_latency_ms": board["input_wait_latency_ms"],
        "active_cycle_unique_values": board["active_cycle_unique_values"],
        "xsim_active_cycle_unique_values": board["xsim_active_cycle_unique_values"],
        "xsim_active_cycle_crosscheck": board["xsim_active_cycle_crosscheck"],
        "system_compute_latency_status": board["system_compute_latency_status"],
        "counter_scope_note": "active core latency subtracts only RUN-state sample-valid starvation; raw core/system intervals remain UART-paced transport diagnostics",
    })
    bit = REPO / "results" / "board_replay" / "microblaze_full_replay" / "snn_ecg_mb_full_replay.bit"
    elf = BOARD / "build" / "snn_ecg_mb_full_replay_benchmark.elf"
    write_json(BOARD / "board_environment.json", {
        "board": "Nexys A7-100T",
        "fpga_target": "xc7a100t",
        "jtag_cable": "Digilent USB/JTAG",
        "microblaze_target_recognized": True,
        "uart_port": board["port"],
        "uart_baud": board["baud"],
        "vivado_vitis_version": "2020.2",
        "python_version": platform.python_version(),
        "bit_path": repo_rel(bit),
        "bit_sha256": sha256(bit),
        "elf_path": repo_rel(elf),
        "elf_sha256": sha256(elf),
        "physical_board_power_meter": "not available",
    })
    status_path = BOARD / "build" / "build_status.json"
    build_status = json.loads(status_path.read_text(encoding="utf-8"))
    build_status.update({
        "physical_execution": "COMPLETED_36_OF_36",
        "instrumented_elf": repo_rel(elf),
        "elf_sha256": sha256(elf),
        "board": "Nexys A7-100T",
        "uart_port": board["port"],
        "uart_baud": board["baud"],
    })
    write_json(status_path, build_status)
    write_text(BOARD / "README.md", f"""# Board Timing Package

Status: **COMPLETED** on Nexys A7-100T, `{board['port']}`, {board['baud']} baud.

The immutable BIT and instrumented ELF were programmed before each case. All 36 cases sent 1,800,000 samples, produced 30 snapshots and one decision, emitted exactly one `BOARD_BENCH` line and a board PASS marker, and matched Golden Reference final predictions 36/36 and all Final Membrane values 144/144.

The reportable accelerator performance metric is `core_active_cycles = profile_total_cycles - profile_input_wait_cycles`. Both operands are measured 100 MHz hardware counters. The RTL increments `profile_input_wait` only in RUN while the accelerator is ready and `sample_valid` is absent, so the subtraction removes upstream UART/MicroBlaze starvation but retains internal back-pressure, snapshot/final-decision work, and 1,320 non-RUN control cycles. All 36 cases produced exactly {board['core_active_cycles']['median']:.0f} active cycles ({board['core_active_latency_ms']['median']:.6f} ms), matching the canonical XSim subtraction 36/36.

Raw `core_cycles` and `system_cycles` are retained unchanged as UART-paced transaction diagnostics; they were equal in {board['core_system_equal_cases']}/36 cases. They are not used for accelerator speedup or energy. Integrated-system compute latency, speedup, and energy remain unmeasured because the immutable XSA has no preloaded input path or independent AXI Timer. UART result printing occurs after counters stop. The integrated AXI UARTLite is configured for 230400 baud; 115200 produces undecodable bytes.

Reproduce the manifest-only preflight:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --dry-run --output-dir benchmarks/accelerator_benefit/board/preflight_dry_run
```

Re-run or resume the board batch:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port {board['port']}
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port {board['port']} --resume
```

The 36-case runner programs each case by default. It does not accept or require `--program`. Raw transcripts are under `board/future_run/transcripts`; parsed JSON, batch summaries, and `board_timing_results.csv` are retained beside them.
""")


def ready_doc() -> None:
    artifacts = {row["artifact"]: row["sha256"] for row in read_csv(RESULTS / "immutable_artifact_hashes.csv")}
    board = load_board_timing()
    state = json.loads((RESULTS / "repository_start_state.json").read_text(encoding="utf-8"))
    bit = "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit"
    xsa = "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa"
    elf = BOARD / "build" / "snn_ecg_mb_full_replay_benchmark.elf"
    write_text(BENCH / "READY_FOR_BOARD_BENCHMARK.md", f"""# Board Benchmark Completion Record

Status: **COMPLETED**, Nexys A7-100T, `{board['port']}`, {board['baud']} baud.

## Immutable artifacts

- BIT `{bit}`: `{artifacts[bit]}`
- XSA `{xsa}`: `{artifacts[xsa]}`
- instrumented ELF `{repo_rel(elf)}`: `{sha256(elf)}`
- dataset manifest: `{state['dataset_manifest_sha256']}`
- locked config: `{state['locked_config_sha256']}`
- locked parameter file: `{state['locked_params_file_sha256']}`

## Acceptance

- completed: 36/36
- samples: 1,800,000 per case
- snapshots/decisions: 30/1 per case
- board vs Golden final prediction: 36/36
- board vs Golden Final Membrane: 144/144 values
- annotation accuracy: 29/36 (80.56%)
- every transcript: exactly one `BOARD_BENCH` and one board PASS marker
- every core/system counter: greater than zero
- active-core metric: `profile_total - profile_input_wait` = {board['core_active_cycles']['median']:.0f} cycles = {board['core_active_latency_ms']['median']:.6f} ms in 36/36 cases
- Exact C++ kernel / FPGA active-core speedup: {1777.6998 / board['core_active_latency_ms']['median']:.6f}x
- integrated-system compute latency/speedup/energy: not measured; requires preloaded input and an independent timer

Raw evidence is in `benchmarks/accelerator_benefit/board/future_run`. Use `--resume` only after a transport interruption; completed transcript/parsed pairs are retained. The immutable UARTLite configuration is 230400 baud.
""")


def reports(rtl: dict[str, Any], python: dict[str, Any] | None, cpp: dict[str, Any] | None, native_cpp: dict[str, Any] | None) -> None:
    board = load_board_timing()
    power = load_power_summary()
    pure = power["scopes"]["pure_rtl"]
    system = power["scopes"]["microblaze_system"]
    historical_pure = json.loads(FINAL_METRICS.read_text(encoding="utf-8-sig"))["pure_rtl_vivado"]
    exact_ms = native_cpp["kernel"]["all_run_latency_ms"]["median"] if native_cpp else float("nan")
    core = board["core_active_latency_ms"]
    uart_interval = board["uart_paced_transaction_counter_interval_ms"]
    core_speedup = exact_ms / core["median"]
    pure_energy = pure["total_on_chip_power_w"] * core["median"] / 1000
    pure_clocks = ", ".join(f"{item['name']} {item['frequency_mhz']:.3f} MHz" for item in pure["clocks"])
    system_clocks = ", ".join(f"{item['name']} {item['frequency_mhz']:.3f} MHz" for item in system["clocks"])

    kr = f"""# SNN ECG FPGA 실보드 성능 및 Vivado 전력 보고서

모든 표의 수치는 `MEASURED`, `ESTIMATED`, `DERIVED` 중 하나로 구분한다. raw firmware/schema의 legacy label `AFF`는 유지하며, 본 보고서의 의료 표기는 `AF`를 사용한다.

| 항목 | 결과 | 근거/분류 |
|---|---:|---|
| 분류 정확도 | 29/36, 80.56% | final-test annotation, MEASURED |
| 보드-Golden final_pred | 36/36 | UART board replay, MEASURED |
| 보드-Golden Final Membrane | 144/144 | UART board replay, MEASURED |
| FPGA core active latency median / mean / range | {core['median']:.6f} / {core['mean']:.6f} / {core['min']:.6f}-{core['max']:.6f} ms | 두 hardware counter의 차, DERIVED |
| FPGA core active cycles | {board['core_active_cycles']['median']:.0f} cycles, 36/36 동일 | `profile_total - profile_input_wait`, DERIVED from MEASURED counters |
| FPGA core throughput / 1 kSPS margin | {board['core_active_throughput_samples_per_s']['median']:.6f} samples/s / {board['core_active_realtime_margin_vs_1ksps']['median']:.6f}x | DERIVED |
| Exact C++ 대비 core speedup | {core_speedup:.9f}x | CPU MEASURED / FPGA counter-derived, DERIVED |
| UART-paced raw interval median | {uart_interval['median']:.6f} ms | transport diagnostic, MEASURED |
| Integrated-system compute latency/speedup | 미측정 | DDR 사전 적재와 독립 timer 필요 |
| Pure RTL power | {pure['total_on_chip_power_w']:.6f} W | Vivado post-implementation vectorless, ESTIMATED |
| Integrated FPGA system power | {system['total_on_chip_power_w']:.6f} W | Vivado post-implementation vectorless, ESTIMATED |
| Pure RTL energy/decision | {pure_energy:.9f} J | estimated power x measured core latency, DERIVED |
| Integrated system energy/decision | 미측정 | 유효한 integrated compute latency 없음 |
| Board physical power | 미측정 | 외부 전력계 없음 |

보드는 Nexys A7-100T, UART `{board['port']}`/{board['baud']} baud였다. 코어 성능은 `profile_total_cycles - profile_input_wait_cycles`로 산출했다. 두 피연산자는 모두 실보드 100 MHz hardware counter에서 MEASURED 되었고, latency·throughput·speedup은 그 차로부터 DERIVED 되었다. RTL에서 input-wait counter는 RUN 상태에서 코어가 입력을 받을 준비가 되었지만 `sample_valid`가 없을 때만 증가한다. 따라서 이 계산은 UART/MicroBlaze 입력 starvation만 제거하며 내부 back-pressure, snapshot/final-decision 처리와 {board['non_run_overhead_cycles']['median']:.0f} control cycles를 유지한다.

36개 보드 case의 UART-paced raw interval은 서로 달랐지만 active-cycle 차는 모두 정확히 {board['core_active_cycles']['median']:.0f} cycles였다. canonical XSim에서도 `5,401,260 - 1,799,970 = 3,601,290 cycles`로 동일해 36/36 교차 검증되었다. 과거 54.0126 ms와 32.912687x는 canonical sample gap을 포함한 값이므로 no-stall 코어 성능으로 사용하지 않는다. 현재 코어 결과는 {core['median']:.6f} ms 및 {core_speedup:.9f}x다.

원시 `core_cycles/system_cycles` 구간은 입력 대기를 포함하므로 UART-paced transport diagnostic으로만 보존한다. 이를 integrated-system 속도나 energy로 사용하지 않는다. 진짜 통합 시스템 계측에는 ECG를 DDR2 등에 먼저 적재하고 독립 AXI Timer로 feeder 시작부터 최종 decision까지 측정해야 한다.

Pure RTL 전력은 기존 {historical_pure['estimated_total_power_w']:.6f} W를 동일 RTL/part/clock으로 재현했다. 새 route 자원은 {pure['utilization']['lut']} LUT/{pure['utilization']['flip_flop']} FF로 과거 {historical_pure['lut']}/{historical_pure['ff']}와 소폭 다르며 route WNS도 새 보고서 값을 사용한다. Integrated system은 MicroBlaze, BRAM, AXI, UART, sample feeder와 accelerator를 모두 포함하므로 Pure RTL 값과 섞지 않는다.

두 전력값 모두 SAIF/VCD 없이 Vivado 기본 vectorless propagation을 사용한 **Post-implementation vectorless Vivado power estimate**다. confidence는 Pure RTL `{pure['power_estimation_confidence']}`, system `{system['power_estimation_confidence']}`이며 clock은 각각 {pure_clocks}; {system_clocks}다. 물리 보드 입력 전력과 가속기 실측 에너지는 측정하지 않았다.
"""
    write_text(REPORTS / "ACCELERATOR_BENEFIT_KR.md", kr)

    en = f"""# SNN ECG FPGA Board Performance and Vivado Power Report

Raw firmware/schema retain the legacy `AFF` label; report-facing medical text uses `AF`. Every result is classified as MEASURED, ESTIMATED, or DERIVED.

| Item | Result | Evidence |
|---|---:|---|
| Classification accuracy | 29/36 (80.56%) | final-test annotation, MEASURED |
| Board-Golden final prediction | 36/36 | UART replay, MEASURED |
| Board-Golden Final Membrane | 144/144 | UART replay, MEASURED |
| FPGA active-core latency median / mean / range | {core['median']:.6f} / {core['mean']:.6f} / {core['min']:.6f}-{core['max']:.6f} ms | difference of two hardware counters, DERIVED |
| FPGA active-core cycles | {board['core_active_cycles']['median']:.0f} cycles, identical in 36/36 | `profile_total - profile_input_wait`, DERIVED from MEASURED counters |
| FPGA active-core throughput / 1 kSPS margin | {board['core_active_throughput_samples_per_s']['median']:.6f} samples/s / {board['core_active_realtime_margin_vs_1ksps']['median']:.6f}x | DERIVED |
| Exact C++ / FPGA active-core speedup | {core_speedup:.9f}x | CPU MEASURED / FPGA counter-derived, DERIVED |
| UART-paced raw interval median | {uart_interval['median']:.6f} ms | transport diagnostic, MEASURED |
| Integrated-system compute latency/speedup | Not measured | requires preloaded input and independent timer |
| Pure RTL power | {pure['total_on_chip_power_w']:.6f} W | post-implementation vectorless Vivado, ESTIMATED |
| Integrated FPGA system power | {system['total_on_chip_power_w']:.6f} W | post-implementation vectorless Vivado, ESTIMATED |
| Pure RTL energy/decision | {pure_energy:.9f} J | estimated power x measured core latency, DERIVED |
| Integrated system energy/decision | Not measured | no valid integrated compute latency |
| Physical board power | Not measured | no external power meter |

The Nexys A7-100T ran on `{board['port']}` at {board['baud']} baud. Active-core performance is `profile_total_cycles - profile_input_wait_cycles`. Both operands are MEASURED 100 MHz on-board hardware counters; latency, throughput, and speedup are DERIVED from their difference. The RTL increments input-wait only in RUN when the core is ready but `sample_valid` is absent. The subtraction therefore removes UART/MicroBlaze input starvation while retaining internal back-pressure, snapshot/final-decision work, and {board['non_run_overhead_cycles']['median']:.0f} control cycles.

Although UART-paced raw intervals varied among cases, all 36 board differences were exactly {board['core_active_cycles']['median']:.0f} cycles. Canonical XSim independently gives `5,401,260 - 1,799,970 = 3,601,290 cycles`, a 36/36 cross-check. The former 54.0126 ms and 32.912687x values include the canonical sample gap and are not used as no-stall core performance. The corrected active-core result is {core['median']:.6f} ms and {core_speedup:.9f}x versus Exact C++.

Raw `core_cycles/system_cycles` intervals are retained only as UART-paced transport diagnostics. They are not used for integrated-system speedup or energy. A valid integrated measurement requires preloading the ECG in DDR2 (or equivalent) and bracketing feeder start through final decision with an independent AXI Timer.

Both power results are **Post-implementation vectorless Vivado power estimates** with no SAIF/VCD. Confidence is `{pure['power_estimation_confidence']}` for Pure RTL and `{system['power_estimation_confidence']}` for the integrated system. Physical board input power and measured accelerator energy were not obtained.
"""
    write_text(REPORTS / "ACCELERATOR_BENEFIT_EN.md", en)

    write_text(REPORTS / "BENCHMARK_LIMITATIONS.md", f"""# Benchmark Limitations

- Active-core latency is a DERIVED subtraction of two MEASURED hardware counters, not host wall time or an independent external timing measurement.
- The counter definition removes only RUN-state input starvation; its interpretation depends on the locked RTL semantics documented in `rtl/snn_ecg_30min_final_top.v`.
- Exact C++ is a single-thread hand-written transaction-level implementation with audited cadence compression; it is not a literal event-driven RTL simulation.
- Historical 54.0126 ms/32.912687x values include canonical sample-gap cycles and are superseded for active-core performance by 36.0129 ms/49.362862x.
- Integrated-system compute latency, speedup, and energy are not measured; DDR/preload plus an independent system timer is required.
- Pure RTL and integrated MicroBlaze power are separate post-implementation vectorless Vivado estimates with Medium confidence and no SAIF/VCD.
- Physical board input power was not measured; no value is presented as board power or measured energy.
- Pure RTL and integrated-system resource/power scopes are not directly equivalent.
- Live ECG still requires a 30-minute observation window even though stored-data replay completes faster.
""")

    claims = [
        {"claim_id": "C1", "claim": "Board matches Golden final predictions 36/36 and Final Membrane values 144/144.", "status": "SUPPORTED", "evidence_type": "MEASURED", "evidence_path": repo_rel(BOARD_TIMING_CSV), "limitation": "functional equivalence, not 100% annotation accuracy"},
        {"claim_id": "C2", "claim": f"FPGA active-core median latency is {core['median']:.6f} ms from {board['core_active_cycles']['median']:.0f} cycles.", "status": "SUPPORTED", "evidence_type": "DERIVED from two MEASURED hardware counters", "evidence_path": repo_rel(BOARD_TIMING_CSV), "limitation": "counter-semantics dependent; not host wall time"},
        {"claim_id": "C3", "claim": f"UART-paced raw transaction median is {uart_interval['median']:.6f} ms.", "status": "SUPPORTED_DIAGNOSTIC_ONLY", "evidence_type": "MEASURED", "evidence_path": repo_rel(BOARD_TIMING_CSV), "limitation": "not accelerator or integrated-system compute latency"},
        {"claim_id": "C4", "claim": f"Pure RTL post-implementation vectorless Vivado power is {pure['total_on_chip_power_w']:.6f} W.", "status": "SUPPORTED", "evidence_type": "ESTIMATED", "evidence_path": pure["raw_power_report"], "limitation": "not physical board power"},
        {"claim_id": "C5", "claim": f"Integrated-system post-implementation vectorless Vivado power is {system['total_on_chip_power_w']:.6f} W.", "status": "SUPPORTED", "evidence_type": "ESTIMATED", "evidence_path": system["raw_power_report"], "limitation": "not physical board power"},
        {"claim_id": "C6", "claim": "Physical board power was measured.", "status": "FORBIDDEN", "evidence_type": "none", "evidence_path": "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md", "limitation": "no external power meter"},
        {"claim_id": "C7", "claim": f"Exact C++ divided by FPGA active-core latency is {core_speedup:.9f}x.", "status": "SUPPORTED", "evidence_type": "DERIVED from CPU MEASURED and FPGA counter-derived latency", "evidence_path": repo_rel(BOARD_TIMING_CSV), "limitation": "core scope only; excludes integrated feeder/memory latency"},
        {"claim_id": "C8", "claim": f"Pure RTL estimated energy is {pure_energy:.9f} J per decision.", "status": "SUPPORTED", "evidence_type": "DERIVED estimated power times counter-derived active latency", "evidence_path": "benchmarks/accelerator_benefit/results/power_energy_summary.csv", "limitation": "not measured energy or physical-board power"},
        {"claim_id": "C9", "claim": "Integrated-system compute latency, speedup, and energy were measured.", "status": "FORBIDDEN", "evidence_type": "none", "evidence_path": "benchmarks/accelerator_benefit/reports/BENCHMARK_LIMITATIONS.md", "limitation": "requires preloaded input and independent timer"},
    ]
    write_csv(REPORTS / "CLAIM_REGISTRY.csv", claims, list(claims[0]))


def main() -> int:
    for path in (RESULTS, REPORTS, FIGURES, BOARD, REFERENCE):
        path.mkdir(parents=True, exist_ok=True)
    protocol_hash = generate_protocol()
    generate_hashes(protocol_hash)
    python = generate_cpu_status()
    cpp = generate_cpp_status()
    native_cpp = generate_native_cpp_status()
    rtl = generate_rtl()
    generate_board_audit()
    generate_memory_power(rtl)
    generate_comparison(rtl, python, cpp, native_cpp)
    generate_figures(rtl, python, cpp, native_cpp)
    generate_board_docs()
    ready_doc()
    reports(rtl, python, cpp, native_cpp)
    print(json.dumps({"status": "generated", "active_core_latency_ms": rtl["active_total_latency_ms"]["median"], "active_core_throughput_msps": rtl["active_throughput_msamples_per_s"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
