from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "final_membrane_v2_snn"
OUT = RESULTS / "profile_synth_overhead"
VIVADO = Path(r"C:\Xilinx\Vivado\2020.2\bin\vivado.bat")

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
    return str(path).replace("\\", "/")


def write_tcl(profile_en: int) -> Path:
    run_dir = OUT / f"profile_en_{profile_en}"
    run_dir.mkdir(parents=True, exist_ok=True)
    tcl = run_dir / "synth_profile_overhead.tcl"
    rtl_files = [f"rtl/core/{src}" for src in CORE_SOURCES]
    rtl_files.extend(
        [
            "rtl/final_membrane_layer.v",
            "rtl/snn_ecg_30min_final_top.v",
        ]
    )
    file_list = " \\\n    ".join(f'"{slash(REPO / path)}"' for path in rtl_files)
    tcl.write_text(
        f"""set repo_dir "{slash(REPO)}"
set run_dir "{slash(run_dir)}"
set env(SYNTH_COMMON) "C:/Xilinx/Vivado/2020.2/scripts/rt/data"
cd $run_dir
file copy -force "$repo_dir/rtl/strict_recordwise_locked_params.vh" "$run_dir/strict_recordwise_locked_params.vh"

read_verilog [list \\
    {file_list} \\
]

synth_design -top snn_ecg_30min_final_top -part xc7a100tcsg324-1 \\
    -mode out_of_context -flatten_hierarchy none -generic {{PROFILE_EN={profile_en}}}
create_clock -period 10.000 -name clk [get_ports clk]

report_utilization -file "$run_dir/utilization.rpt"
report_utilization -hierarchical -file "$run_dir/utilization_hier.rpt"
report_timing_summary -file "$run_dir/timing_summary.rpt"
set rdm_to_pred_from [get_cells -quiet -hier -filter {{NAME =~ *rdm_level_spike_reg*}}]
set rdm_to_pred_to [get_cells -quiet -hier -filter {{NAME =~ *pred_class_reg*}}]
set rdm_to_pred_paths [get_timing_paths -quiet -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 1]
if {{[llength $rdm_to_pred_paths] == 0}} {{
    set rdm_to_pred_fp [open "$run_dir/rdm_to_pred_class_timing.rpt" w]
    puts $rdm_to_pred_fp "No timing paths found."
    close $rdm_to_pred_fp
}} else {{
    report_timing -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 10 -file "$run_dir/rdm_to_pred_class_timing.rpt"
}}
write_checkpoint -force "$run_dir/synth.dcp"
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def clean_vivado_cache(run_dir: Path | None = None) -> None:
    caches = [REPO / ".Xil", OUT / ".Xil"]
    if run_dir is not None:
        caches.append(run_dir / ".Xil")
    for cache in caches:
        for _ in range(10):
            if not cache.exists():
                break
            try:
                shutil.rmtree(cache)
                break
            except PermissionError:
                time.sleep(1.0)


def is_retryable_vivado_failure(log: Path) -> bool:
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    retry_markers = [
        ".Xil",
        "realtime",
        "lib_core.tcl",
        "common.tcl",
        "rtSynthParallelPrep.tcl",
        "fpga_tcl",
        "unimacro",
        "No error",
        "called Tcl_Close on channel with refCount > 0",
        "invalid command name \"rt-undefined\"",
    ]
    return any(marker in text for marker in retry_markers)


def run_vivado(profile_en: int) -> None:
    run_dir = OUT / f"profile_en_{profile_en}"
    tcl = write_tcl(profile_en)
    log = run_dir / "vivado.log"
    stale_outputs = [
        run_dir / "utilization.rpt",
        run_dir / "utilization_hier.rpt",
        run_dir / "timing_summary.rpt",
        run_dir / "rdm_to_pred_class_timing.rpt",
        run_dir / "synth.dcp",
    ]
    for path in stale_outputs:
        if path.exists():
            path.unlink()
    for attempt in range(6):
        clean_vivado_cache(run_dir)
        if attempt:
            time.sleep(1.0)
        with log.open("w", encoding="utf-8", errors="replace") as f:
            proc = subprocess.run(
                [str(VIVADO), "-mode", "batch", "-nojournal", "-nolog", "-source", slash(tcl)],
                cwd=run_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )
        if proc.returncode == 0:
            return
        if (attempt < 5) and is_retryable_vivado_failure(log):
            continue
        raise RuntimeError(f"Vivado failed for PROFILE_EN={profile_en}; see {log}")


def parse_util(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = {
        "slice_lut": r"\|\s*Slice LUTs\*?\s*\|\s*([0-9]+)",
        "slice_reg": r"\|\s*Slice Registers\s*\|\s*([0-9]+)",
        "ff": r"\|\s*Register as Flip Flop\s*\|\s*([0-9]+)",
        "bram_tile": r"\|\s*Block RAM Tile\s*\|\s*([0-9]+)",
        "dsp": r"\|\s*DSPs\s*\|\s*([0-9]+)",
    }
    out: dict[str, int] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            out[key] = int(match.group(1))
    return out


def parse_hierarchy(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    line_re = re.compile(
        r"^\|\s*(?P<inst>[^|]+?)\s*\|\s*(?P<module>[^|]+?)\s*\|\s*"
        r"(?P<lut>[0-9]+)\s*\|\s*(?P<logic>[0-9]+)\s*\|\s*"
        r"(?P<lutram>[0-9]+)\s*\|\s*(?P<srl>[0-9]+)\s*\|\s*"
        r"(?P<ff>[0-9]+)\s*\|\s*(?P<ramb36>[0-9]+)\s*\|\s*"
        r"(?P<ramb18>[0-9]+)\s*\|\s*(?P<dsp>[0-9]+)\s*\|"
    )
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = line_re.match(line)
        if not match:
            continue
        inst = match.group("inst").strip()
        if inst == "Instance":
            continue
        rows.append(
            {
                "instance": inst,
                "module": match.group("module").strip(),
                "lut": int(match.group("lut")),
                "logic_lut": int(match.group("logic")),
                "lutram": int(match.group("lutram")),
                "srl": int(match.group("srl")),
                "ff": int(match.group("ff")),
                "ramb36": int(match.group("ramb36")),
                "ramb18": int(match.group("ramb18")),
                "dsp": int(match.group("dsp")),
            }
        )
    return rows


def parse_timing(path: Path) -> dict[str, float | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    setup = re.search(r"Setup\s*:\s*[0-9]+\s+Failing Endpoints,\s+Worst Slack\s+(-?[0-9.]+)ns", text)
    hold = re.search(r"Hold\s*:\s*[0-9]+\s+Failing Endpoints,\s+Worst Slack\s+(-?[0-9.]+)ns", text)
    return {
        "setup_wns_ns": float(setup.group(1)) if setup else None,
        "hold_whs_ns": float(hold.group(1)) if hold else None,
    }


def build_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {"runs": {}, "delta_profile_en_1_minus_0": {}}
    for profile_en in [0, 1]:
        run_dir = OUT / f"profile_en_{profile_en}"
        util = parse_util(run_dir / "utilization.rpt")
        hier = parse_hierarchy(run_dir / "utilization_hier.rpt")
        timing = parse_timing(run_dir / "timing_summary.rpt")
        summary["runs"][str(profile_en)] = {
            "utilization": util,
            "timing": timing,
            "top_hierarchy_by_lut": sorted(hier, key=lambda row: row["lut"], reverse=True)[:12],
        }

    util0 = summary["runs"]["0"]["utilization"]
    util1 = summary["runs"]["1"]["utilization"]
    for key in sorted(set(util0) | set(util1)):
        summary["delta_profile_en_1_minus_0"][key] = util1.get(key, 0) - util0.get(key, 0)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "profile_synth_overhead_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# PROFILE_EN Synth Overhead",
        "",
        "Top: `snn_ecg_30min_final_top` out-of-context, part `xc7a100tcsg324-1`, 10 ns clock.",
        "",
        "| PROFILE_EN | LUT | FF | BRAM tile | DSP | Setup WNS ns | Hold WHS ns |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile_en in ["0", "1"]:
        run = summary["runs"][profile_en]
        util = run["utilization"]
        timing = run["timing"]
        lines.append(
            f"| {profile_en} | {util.get('slice_lut', 0)} | {util.get('ff', 0)} | "
            f"{util.get('bram_tile', 0)} | {util.get('dsp', 0)} | "
            f"{timing.get('setup_wns_ns')} | {timing.get('hold_whs_ns')} |"
        )

    delta = summary["delta_profile_en_1_minus_0"]
    lines.extend(
        [
            "",
            "Delta `PROFILE_EN=1 - PROFILE_EN=0`:",
            "",
            "| Resource | Delta |",
            "|---|---:|",
        ]
    )
    for key in ["slice_lut", "ff", "bram_tile", "dsp"]:
        lines.append(f"| {key} | {delta.get(key, 0)} |")

    lines.extend(["", "## Top LUT Hotspots", ""])
    for profile_en in ["0", "1"]:
        lines.extend(
            [
                f"### PROFILE_EN={profile_en}",
                "",
                "| Instance | Module | LUT | FF |",
                "|---|---|---:|---:|",
            ]
        )
        for row in summary["runs"][profile_en]["top_hierarchy_by_lut"]:
            lines.append(f"| `{row['instance']}` | `{row['module']}` | {row['lut']} | {row['ff']} |")
        lines.append("")
    (OUT / "profile_synth_overhead_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for profile_en in [0, 1]:
        run_vivado(profile_en)
    summary = build_summary()
    write_report(summary)
    print(OUT / "profile_synth_overhead_summary.json")


if __name__ == "__main__":
    main()
