from __future__ import annotations

import json
from pathlib import Path

from award_readiness_common import REPORTS, REPO, RESULTS, md_table, write_json


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def status(path: Path) -> str:
    return "present" if path.exists() else "missing"


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    board = load_json(RESULTS / "vivado_snn_ecg_v2" / "snn_ecg_v2_vivado_summary.json")
    axi = load_json(RESULTS / "axi_impl_timing_10ns" / "axi_impl_timing_10ns_summary.json")
    mb = load_json(RESULTS / "microblaze_smoke" / "microblaze_smoke_summary.json")
    xsim = load_json(RESULTS / "xsim_snn_ecg_v2_summary.json")

    evidence = {
        "board_top": board,
        "axi_ooc": axi,
        "microblaze_smoke": mb,
        "xsim_summary": {
            "candidate_id": xsim.get("candidate_id"),
            "python_vs_xsim": xsim.get("python_vs_xsim"),
            "test_accuracy": xsim.get("splits", {}).get("test", {}).get("python", {}).get("accuracy"),
        },
        "ip_packaging": {
            "snn_component_xml": status(REPO / "ip_repo" / "snn_ecg_axi_accelerator" / "component.xml"),
            "snn_xgui": status(REPO / "ip_repo" / "snn_ecg_axi_accelerator" / "xgui" / "snn_ecg_axi_accelerator_v1_0.tcl"),
            "feeder_component_xml": status(REPO / "ip_repo" / "axi_lite_axis_sample_feeder" / "component.xml"),
            "feeder_xgui": status(REPO / "ip_repo" / "axi_lite_axis_sample_feeder" / "xgui" / "axi_lite_axis_sample_feeder_v1_0.tcl"),
        },
    }
    write_json(REPORTS / "vivado_metrics.json", evidence)

    rows = []
    if board:
        util = board.get("utilization", {})
        timing = board.get("timing", {})
        rows.extend(
            [
                ["board LUT", util.get("slice_lut"), "vivado_snn_ecg_v2 summary"],
                ["board FF", util.get("ff"), "vivado_snn_ecg_v2 summary"],
                ["board BRAM", util.get("bram_tile"), "vivado_snn_ecg_v2 summary"],
                ["board DSP", util.get("dsp"), "vivado_snn_ecg_v2 summary"],
                ["board WNS ns", timing.get("wns_ns"), "vivado_snn_ecg_v2 timing"],
                ["board total power W", board.get("power", {}).get("total_on_chip_power_w"), "Vivado estimated power"],
            ]
        )
    axi_run = axi.get("runs", {}).get("1", {}) if axi else {}
    if axi_run:
        rows.extend(
            [
                ["AXI OOC LUT", axi_run.get("utilization", {}).get("slice_lut"), "axi_impl_timing_10ns"],
                ["AXI OOC FF", axi_run.get("utilization", {}).get("ff"), "axi_impl_timing_10ns"],
                ["AXI OOC BRAM", axi_run.get("utilization", {}).get("bram_tile"), "axi_impl_timing_10ns"],
                ["AXI OOC DSP", axi_run.get("utilization", {}).get("dsp"), "axi_impl_timing_10ns"],
                ["AXI OOC WNS ns", axi_run.get("timing", {}).get("setup_worst_slack_ns"), "10 ns post-route"],
            ]
        )
    if mb:
        rows.extend(
            [
                ["MicroBlaze smoke LUT", mb.get("utilization", {}).get("slice_lut"), "microblaze_smoke_summary"],
                ["MicroBlaze smoke FF", mb.get("utilization", {}).get("ff"), "microblaze_smoke_summary"],
                ["MicroBlaze smoke BRAM", mb.get("utilization", {}).get("bram_tile"), "system infrastructure included"],
                ["MicroBlaze smoke DSP", mb.get("utilization", {}).get("dsp"), "system infrastructure included"],
                ["MicroBlaze smoke WNS ns", mb.get("timing", {}).get("setup_worst_slack_ns"), "system_timing_summary"],
            ]
        )

    md = [
        "# Vivado / IP Metrics",
        "",
        md_table(["metric", "value", "source"], rows),
        "",
        "## IP Packaging Evidence",
        "",
        md_table(["evidence", "status"], [[k, v] for k, v in evidence["ip_packaging"].items()]),
        "",
        "Limitations: Vivado power is an estimate. MicroBlaze system resources include CPU/LMB/BRAM/UART infrastructure and should not be compared directly with the bare accelerator core.",
    ]
    (REPORTS / "vivado_metrics.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "vivado_metrics.md")


if __name__ == "__main__":
    main()
