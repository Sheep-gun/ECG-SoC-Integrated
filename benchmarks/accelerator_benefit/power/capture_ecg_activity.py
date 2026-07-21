#!/usr/bin/env python3
"""Capture real-ECG SAIF traces for the direct-100-MHz Pure RTL design."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
POWER = REPO / "benchmarks" / "accelerator_benefit" / "power"
CASES_CSV = REPO / "reports" / "final" / "board_replay_36_cases.csv"
RESULT_ROOT = POWER / "results" / "activity"
WORK = POWER / "work" / "activity_xsim"
XVLOG = Path(r"C:\Xilinx\Vivado\2020.2\bin\xvlog.bat")
XELAB = Path(r"C:\Xilinx\Vivado\2020.2\bin\xelab.bat")
XSIM = Path(r"C:\Xilinx\Vivado\2020.2\bin\xsim.bat")

CORE_SOURCES = [
    "ecg_event_encoder.v",
    "ecg_event_encoder_adaptive.v",
    "snn_ecg_input_normalizer.v",
    "qrs_lif_detector.v",
    "pnn_rhythm_predictor.v",
    "dscr_spike_counter.v",
    "ram_peak_accumulator.v",
    "rdm_variability_neuron.v",
    "ectopic_pair_neuron.v",
    "qrs_maf_neuron.v",
    "rbbb_qrs_delay_bank.v",
    "abandoned_feature_stubs.v",
    "class_score_neurons.v",
    "snn_ecg_3feat_top.v",
]


def slash(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path, log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        process = subprocess.run(command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"command failed ({process.returncode}); see {log}")


def run_xsim(command: list[str], cwd: Path, log: Path) -> None:
    """Run XSim and tolerate its Windows wrapper lingering after Tcl exit."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        process = subprocess.Popen(command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT, text=True)
        deadline = time.monotonic() + 7200
        while time.monotonic() < deadline:
            returncode = process.poll()
            handle.flush()
            text = log.read_text(encoding="utf-8", errors="replace")
            if returncode is not None:
                if returncode != 0:
                    raise RuntimeError(f"XSim failed ({returncode}); see {log}")
                return
            if "INFO: [Common 17-206] Exiting xsim" in text:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                return
            time.sleep(2)
        process.kill()
        process.wait()
        raise TimeoutError(f"XSim did not finish within two hours; see {log}")


def load_cases() -> dict[str, dict[str, str]]:
    with CASES_CSV.open(newline="", encoding="utf-8-sig") as handle:
        return {row["case_id"]: row for row in csv.DictReader(handle)}


def select_default_cases(cases: dict[str, dict[str, str]]) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for case_id, row in cases.items():
        label = row["class_label"]
        if label not in seen:
            seen.add(label)
            selected.append(case_id)
    return selected


def build_snapshot() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    prj = WORK / "activity_sources.prj"
    sources = [REPO / "rtl" / "core" / name for name in CORE_SOURCES]
    sources += [
        REPO / "rtl" / "final_membrane_layer.v",
        REPO / "rtl" / "snn_ecg_30min_final_top.v",
        POWER / "sources" / "snn_ecg_v2_nexys_a7_100mhz_top.v",
        REPO / "sim" / "tb_snn_ecg_power_activity.v",
    ]
    prj.write_text("".join(f'verilog work "{slash(path)}"\n' for path in sources), encoding="utf-8")
    run([str(XVLOG), "--nolog", "-i", slash(REPO / "rtl"), "-prj", slash(prj)], WORK, WORK / "xvlog.log")
    run(
        [str(XELAB), "--nolog", "-debug", "typical", "tb_snn_ecg_power_activity", "-s", "tb_snn_ecg_power_activity"],
        WORK,
        WORK / "xelab.log",
    )


def duration_seconds(saif: Path) -> float:
    text = saif.read_text(encoding="utf-8", errors="replace")
    timescale = re.search(r"\(TIMESCALE\s+([0-9]+)\s+(fs|ps|ns|us|ms|s)\)", text)
    duration = re.search(r"\(DURATION\s+([0-9]+)\)", text)
    if not timescale or not duration:
        raise ValueError(f"cannot parse SAIF duration: {saif}")
    units = {"fs": 1e-15, "ps": 1e-12, "ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0}
    return int(timescale.group(1)) * units[timescale.group(2)] * int(duration.group(1))


def capture(case: dict[str, str], mode: str, samples: int, gap_cycles: int) -> dict[str, object]:
    case_id = case["case_id"]
    out_dir = RESULT_ROOT / case_id / mode
    out_dir.mkdir(parents=True, exist_ok=True)
    mem = REPO / case["mem_path"]
    actual_sha = sha256(mem)
    if actual_sha != case["mem_sha256"]:
        raise ValueError(f"SHA-256 mismatch for {mem}: {actual_sha}")
    saif = out_dir / f"{case_id}_{mode}.saif"
    unmatched = out_dir / f"{case_id}_{mode}_simulation.log"
    tcl = out_dir / f"capture_{mode}.tcl"
    tcl.write_text(
        f'open_saif {{{slash(saif)}}}\n'
        'log_saif [get_objects -r /tb_snn_ecg_power_activity/uut/*]\n'
        "run all\n"
        "close_saif\n"
        "quit\n",
        encoding="utf-8",
    )
    require_final = int(mode == "burst_full_record")
    command = [
        str(XSIM),
        "tb_snn_ecg_power_activity",
        "--nolog",
        "--onfinish",
        "stop",
        "--tclbatch",
        "{" + slash(tcl) + "}",
        "--testplusarg",
        f"MEM{Path(os.path.relpath(mem, WORK)).as_posix()}",
        "--testplusarg",
        f"SAMPLES{samples}",
        "--testplusarg",
        f"GAP_CYCLES{gap_cycles}",
        "--testplusarg",
        f"REQUIRE_FINAL{require_final}",
        "--testplusarg",
        f"EXPECTED_PRED{case['expected_final_pred']}",
        "--testplusarg",
        f"EXPECTED_MEM_NSR{case['expected_final_mem_NSR']}",
        "--testplusarg",
        f"EXPECTED_MEM_CHF{case['expected_final_mem_CHF']}",
        "--testplusarg",
        f"EXPECTED_MEM_ARR{case['expected_final_mem_ARR']}",
        "--testplusarg",
        f"EXPECTED_MEM_AFF{case['expected_final_mem_AFF']}",
    ]
    existing_log = unmatched.read_text(encoding="utf-8", errors="replace") if unmatched.exists() else ""
    minimum_duration_s = samples * max(2, gap_cycles + 1) * 10e-9 * 0.99
    existing_duration_s = duration_seconds(saif) if saif.exists() and saif.stat().st_size > 0 else 0.0
    if not (
        existing_duration_s >= minimum_duration_s
        and "ACTIVITY_PASS" in existing_log
        and "INFO: [Common 17-206] Exiting xsim" in existing_log
        and "expected integer" not in existing_log
    ):
        run_xsim(command, WORK, unmatched)
    log_text = unmatched.read_text(encoding="utf-8", errors="replace")
    if "ACTIVITY_PASS" not in log_text or "ACTIVITY_FAIL" in log_text:
        raise RuntimeError(f"functional activity capture failed; see {unmatched}")
    captured_duration_s = duration_seconds(saif)
    if captured_duration_s < minimum_duration_s:
        raise RuntimeError(
            f"truncated SAIF duration {captured_duration_s:.9f}s; expected at least {minimum_duration_s:.9f}s"
        )
    return {
        "case_id": case_id,
        "class_label_internal": case["class_label"],
        "class_label_report": "AF" if case["class_label"] == "AFF" else case["class_label"],
        "mode": mode,
        "sample_count": samples,
        "sample_gap_cycles": gap_cycles,
        "clock_frequency_mhz": 100.0,
        "literal_sample_rate_hz": 100_000_000.0 / (gap_cycles + 1),
        "full_record": samples == int(case["sample_count_expected"]),
        "functional_final_checked": bool(require_final),
        "input_mem": case["mem_path"],
        "input_mem_sha256": actual_sha,
        "saif": saif.relative_to(REPO).as_posix(),
        "saif_sha256": sha256(saif),
        "saif_duration_s": captured_duration_s,
        "simulation_log": unmatched.relative_to(REPO).as_posix(),
        "simulation_log_sha256": sha256(unmatched),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", action="append", help="repeat to capture selected cases; default is one per class")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--burst-only", action="store_true")
    parser.add_argument("--streaming-samples", type=int, default=100)
    args = parser.parse_args()
    cases = load_cases()
    case_ids = args.case_id or select_default_cases(cases)
    unknown = [case_id for case_id in case_ids if case_id not in cases]
    if unknown:
        raise SystemExit(f"unknown case IDs: {unknown}")
    if not args.skip_build:
        build_snapshot()
    records: list[dict[str, object]] = []
    for case_id in case_ids:
        case = cases[case_id]
        records.append(capture(case, "burst_full_record", int(case["sample_count_expected"]), 0))
        if not args.burst_only:
            records.append(capture(case, "streaming_1ksps_prefix", args.streaming_samples, 99_999))
    merged: dict[tuple[str, str], dict[str, object]] = {}
    manifest_path = RESULT_ROOT / "activity_manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        for record in previous.get("records", []):
            merged[(record["case_id"], record["mode"])] = record
    for record in records:
        merged[(str(record["case_id"]), str(record["mode"]))] = record
    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "vivado_xsim_version": "Vivado XSim 2020.2",
        "design_top": "snn_ecg_v2_nexys_a7_100mhz_top",
        "saif_strip_path": "tb_snn_ecg_power_activity/uut",
        "methodology": {
            "burst_full_record": "All 1,800,000 real ECG samples at the fastest ready/valid cadence; final outputs checked against the locked board/XSim reference.",
            "streaming_1ksps_prefix": "Literal 100 MHz simulation with one accepted real ECG sample per 100,000 clock cycles; representative prefix only, not a full 30-minute simulation.",
        },
        "records": sorted(merged.values(), key=lambda item: (str(item["case_id"]), str(item["mode"]))),
    }
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
