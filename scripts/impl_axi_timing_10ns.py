from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "final_membrane_v2_snn"
OUT = RESULTS / "axi_impl_timing_10ns"
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


def run_dir(profile_en: int) -> Path:
    return OUT / f"profile_en_{profile_en}"


def write_tcl(profile_en: int) -> Path:
    rd = run_dir(profile_en)
    rd.mkdir(parents=True, exist_ok=True)

    rtl_files = [REPO / "rtl" / "common" / "reset_sync.v"]
    rtl_files.extend(REPO / "rtl" / "core" / src for src in CORE_SOURCES)
    rtl_files.extend(
        [
            REPO / "rtl" / "final_membrane_layer.v",
            REPO / "rtl" / "snn_ecg_30min_final_top.v",
            REPO / "rtl" / "axi" / "snn_ecg_axi_lite_stream_top.v",
        ]
    )
    file_list = " \\\n    ".join(f'"{slash(path)}"' for path in rtl_files)
    xdc = REPO / "constraints" / "snn_ecg_axi_ooc.xdc"

    tcl = rd / "impl_axi_timing_10ns.tcl"
    tcl.write_text(
        f"""set repo_dir "{slash(REPO)}"
set run_dir "{slash(rd)}"
set env(SYNTH_COMMON) "C:/Xilinx/Vivado/2020.2/scripts/rt/data"
cd $run_dir

read_verilog [list \\
    {file_list} \\
]
read_xdc [list "{slash(xdc)}"]

synth_design -top snn_ecg_axi_lite_stream_top -part xc7a100tcsg324-1 \\
    -mode out_of_context -flatten_hierarchy none -generic {{PROFILE_EN={profile_en}}}
report_timing_summary -file "$run_dir/post_synth_timing_summary.rpt"
check_timing -verbose -file "$run_dir/post_synth_check_timing.rpt"

opt_design
place_design
phys_opt_design
route_design

report_route_status -file "$run_dir/route_status.rpt"
check_timing -verbose -file "$run_dir/post_route_check_timing.rpt"
report_timing_summary -file "$run_dir/post_route_timing_summary.rpt"
report_timing -delay_type max -max_paths 30 -nworst 5 \\
    -path_type full_clock_expanded -input_pins \\
    -file "$run_dir/worst_setup_paths.rpt"
report_timing -delay_type min -max_paths 30 -nworst 5 \\
    -path_type full_clock_expanded -input_pins \\
    -file "$run_dir/worst_hold_paths.rpt"
report_utilization -file "$run_dir/post_route_utilization.rpt"
report_utilization -hierarchical -file "$run_dir/post_route_utilization_hier.rpt"
report_clock_utilization -file "$run_dir/clock_utilization.rpt"
catch {{report_cdc -details -file "$run_dir/cdc.rpt"}} cdc_err
catch {{report_clock_interaction -file "$run_dir/clock_interaction.rpt"}} clock_interaction_err
catch {{report_io -file "$run_dir/io.rpt"}} io_err
catch {{report_control_sets -file "$run_dir/control_sets.rpt"}} control_sets_err
catch {{report_methodology -file "$run_dir/methodology.rpt"}} methodology_err
catch {{report_drc -file "$run_dir/drc.rpt"}} drc_err
catch {{report_qor_suggestions -file "$run_dir/qor_suggestions.rpt"}} qor_err

set rdm_to_pred_from [get_cells -quiet -hier -filter {{NAME =~ *rdm_level_spike_reg*}}]
set rdm_to_pred_to [get_cells -quiet -hier -filter {{NAME =~ *pred_class_reg*}}]
set rdm_to_pred_paths [get_timing_paths -quiet -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 1]
if {{[llength $rdm_to_pred_paths] == 0}} {{
    set rdm_to_pred_fp [open "$run_dir/rdm_to_pred_class_timing.rpt" w]
    puts $rdm_to_pred_fp "No timing paths found."
    close $rdm_to_pred_fp
}} else {{
    report_timing -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 10 \\
        -path_type full_clock_expanded -input_pins \\
        -file "$run_dir/rdm_to_pred_class_timing.rpt"
}}

write_checkpoint -force "$run_dir/routed.dcp"
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def clean_vivado_cache(rd: Path) -> None:
    for cache in [REPO / ".Xil", OUT / ".Xil", rd / ".Xil"]:
        for _ in range(10):
            if not cache.exists():
                break
            try:
                shutil.rmtree(cache)
                break
            except PermissionError:
                time.sleep(1.0)


def run_vivado(profile_en: int) -> None:
    if not VIVADO.exists():
        raise FileNotFoundError(f"Vivado not found: {VIVADO}")

    rd = run_dir(profile_en)
    tcl = write_tcl(profile_en)
    log = rd / "vivado.log"
    stale_outputs = [
        "post_synth_timing_summary.rpt",
        "post_synth_check_timing.rpt",
        "route_status.rpt",
        "post_route_check_timing.rpt",
        "post_route_timing_summary.rpt",
        "worst_setup_paths.rpt",
        "worst_hold_paths.rpt",
        "post_route_utilization.rpt",
        "post_route_utilization_hier.rpt",
        "clock_utilization.rpt",
        "cdc.rpt",
        "clock_interaction.rpt",
        "io.rpt",
        "control_sets.rpt",
        "methodology.rpt",
        "drc.rpt",
        "qor_suggestions.rpt",
        "rdm_to_pred_class_timing.rpt",
        "routed.dcp",
    ]
    for name in stale_outputs:
        path = rd / name
        if path.exists():
            path.unlink()

    for attempt in range(6):
        clean_vivado_cache(rd)
        if attempt:
            time.sleep(1.0)
        with log.open("w", encoding="utf-8", errors="replace") as f:
            proc = subprocess.run(
                [str(VIVADO), "-mode", "batch", "-nojournal", "-nolog", "-source", slash(tcl)],
                cwd=rd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )
        if proc.returncode == 0:
            return
        if attempt < 5:
            continue
        raise RuntimeError(f"Vivado failed for PROFILE_EN={profile_en}; see {log}")


def parse_timing(path: Path) -> dict[str, float | int | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, float | int | None] = {}
    for key, label in [("setup", "Setup"), ("hold", "Hold"), ("pulse_width", "PW")]:
        pattern = (
            rf"{label}\s*:\s*(?P<fail>[0-9]+)\s+Failing Endpoint[s]?\s*,?\s+"
            rf"Worst Slack\s+(?P<slack>-?[0-9.]+)ns,\s+"
            rf"Total Violation\s+(?P<violation>-?[0-9.]+)ns"
        )
        match = re.search(pattern, text)
        if match:
            out[f"{key}_failing_endpoints"] = int(match.group("fail"))
            out[f"{key}_worst_slack_ns"] = float(match.group("slack"))
            out[f"{key}_total_violation_ns"] = float(match.group("violation"))
        else:
            out[f"{key}_failing_endpoints"] = None
            out[f"{key}_worst_slack_ns"] = None
            out[f"{key}_total_violation_ns"] = None
    return out


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


def parse_worst_path(path: Path) -> dict[str, str | int | float | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    slack = re.search(r"Slack\s+\(MET\)\s*:\s*(-?[0-9.]+)ns|Slack\s+\(VIOLATED\)\s*:\s*(-?[0-9.]+)ns", text)
    source = re.search(r"^\s*Source:\s+(.+)$", text, re.MULTILINE)
    destination = re.search(r"^\s*Destination:\s+(.+)$", text, re.MULTILINE)
    logic = re.search(r"^\s*Logic Levels:\s+([0-9]+)\s+\(([^)]+)\)", text, re.MULTILINE)
    return {
        "slack_ns": float(next(group for group in slack.groups() if group is not None)) if slack else None,
        "source": source.group(1).strip() if source else None,
        "destination": destination.group(1).strip() if destination else None,
        "logic_levels": int(logic.group(1)) if logic else None,
        "logic_detail": logic.group(2).strip() if logic else None,
    }


def parse_route_status(path: Path) -> dict[str, bool | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    routable = re.search(r"# of routable nets\.+\s*:\s*([0-9]+)\s*:", text)
    routed = re.search(r"# of fully routed nets\.+\s*:\s*([0-9]+)\s*:", text)
    errors = re.search(r"# of nets with routing errors\.+\s*:\s*([0-9]+)\s*:", text)
    fully_routed = "Design is fully routed" in text
    if routable and routed and errors:
        fully_routed = int(routable.group(1)) == int(routed.group(1)) and int(errors.group(1)) == 0
    return {
        "fully_routed": fully_routed,
        "has_unrouted": not fully_routed,
    }


def parse_cdc(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"report_exists": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "report_exists": True,
        "has_critical": bool(re.search(r"\bCritical\b", text, re.IGNORECASE)),
        "has_warning": bool(re.search(r"\bWarning\b", text, re.IGNORECASE)),
    }


def build_summary(profiles: list[int]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "top": "snn_ecg_axi_lite_stream_top",
        "part": "xc7a100tcsg324-1",
        "clock_period_ns": 10.0,
        "runs": {},
    }
    for profile_en in profiles:
        rd = run_dir(profile_en)
        timing = parse_timing(rd / "post_route_timing_summary.rpt")
        run = {
            "profile_en": profile_en,
            "timing": timing,
            "route_status": parse_route_status(rd / "route_status.rpt"),
            "cdc": parse_cdc(rd / "cdc.rpt"),
            "utilization": parse_util(rd / "post_route_utilization.rpt"),
            "worst_setup_path": parse_worst_path(rd / "worst_setup_paths.rpt"),
            "worst_hold_path": parse_worst_path(rd / "worst_hold_paths.rpt"),
            "reports": {
                "post_route_timing_summary": str(rd / "post_route_timing_summary.rpt"),
                "worst_setup_paths": str(rd / "worst_setup_paths.rpt"),
                "worst_hold_paths": str(rd / "worst_hold_paths.rpt"),
                "route_status": str(rd / "route_status.rpt"),
                "check_timing": str(rd / "post_route_check_timing.rpt"),
                "cdc": str(rd / "cdc.rpt"),
                "clock_interaction": str(rd / "clock_interaction.rpt"),
                "io": str(rd / "io.rpt"),
                "utilization": str(rd / "post_route_utilization.rpt"),
                "utilization_hier": str(rd / "post_route_utilization_hier.rpt"),
                "checkpoint": str(rd / "routed.dcp"),
            },
        }
        run["constraints_met"] = (
            timing.get("setup_failing_endpoints") == 0
            and timing.get("hold_failing_endpoints") == 0
            and timing.get("pulse_width_failing_endpoints") == 0
            and bool(run["route_status"].get("fully_routed"))
        )
        summary["runs"][str(profile_en)] = run
    return summary


def write_report(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "axi_impl_timing_10ns_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# AXI Wrapper 10 ns OOC Implementation Timing",
        "",
        f"Top: `{summary['top']}`",
        f"Part: `{summary['part']}`",
        f"Clock period: `{summary['clock_period_ns']}` ns",
        "",
        "| PROFILE_EN | Routed | Constraints met | Setup WNS ns | Setup TNS ns | Hold WHS ns | Hold THS ns | PW WNS ns | CDC report |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for profile_key in sorted(summary["runs"], key=int):
        run = summary["runs"][profile_key]
        timing = run["timing"]
        lines.append(
            f"| {profile_key} | {run['route_status'].get('fully_routed')} | {run['constraints_met']} | "
            f"{timing.get('setup_worst_slack_ns')} | {timing.get('setup_total_violation_ns')} | "
            f"{timing.get('hold_worst_slack_ns')} | {timing.get('hold_total_violation_ns')} | "
            f"{timing.get('pulse_width_worst_slack_ns')} | {run['cdc'].get('report_exists')} |"
        )

    lines.extend(["", "## Worst Setup Paths", ""])
    for profile_key in sorted(summary["runs"], key=int):
        path = summary["runs"][profile_key]["worst_setup_path"]
        lines.extend(
            [
                f"### PROFILE_EN={profile_key}",
                "",
                f"- Slack ns: `{path.get('slack_ns')}`",
                f"- Source: `{path.get('source')}`",
                f"- Destination: `{path.get('destination')}`",
                f"- Logic levels: `{path.get('logic_levels')}` (`{path.get('logic_detail')}`)",
                "",
            ]
        )

    (OUT / "axi_impl_timing_10ns_report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OOC place/route timing for the AXI SNN ECG wrapper at 10 ns.")
    parser.add_argument(
        "--profile-en",
        choices=["0", "1", "all"],
        default="1",
        help="PROFILE_EN generic to implement. Default: 1.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profiles = [0, 1] if args.profile_en == "all" else [int(args.profile_en)]
    OUT.mkdir(parents=True, exist_ok=True)
    for profile_en in profiles:
        run_vivado(profile_en)
    summary = build_summary(profiles)
    write_report(summary)
    print(OUT / "axi_impl_timing_10ns_summary.json")


if __name__ == "__main__":
    main()
