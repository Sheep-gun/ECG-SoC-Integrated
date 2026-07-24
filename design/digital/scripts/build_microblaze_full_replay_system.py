from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import build_microblaze_template_system as base


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "board_replay" / "microblaze_full_replay"
WORK = REPO.parent / "_snn_ecg_microblaze_full_replay_work"
PART = base.PART

SNN_BASE = base.SNN_BASE
FEEDER_BASE = base.FEEDER_BASE
UART_BASE = base.UART_BASE
INTC_BASE = base.INTC_BASE

SNAPSHOT_SAMPLES = 60000
SNAPSHOTS_PER_CHUNK = 30
TOTAL_SAMPLES = SNAPSHOT_SAMPLES * SNAPSHOTS_PER_CHUNK
POST_DONE_TICKS = 37
PROFILE_EN = 1
TLAST_CHECK_EN = 1
UART_BAUD = 230400


def write_tcl(no_bitstream: bool) -> Path:
    base.RESULTS = RESULTS
    base.WORK = WORK
    tcl = base.write_tcl(no_bitstream)
    text = tcl.read_text(encoding="utf-8")
    replacements = {
        "SNN_ECG_MB_TEMPLATE": "SNN_ECG_MB_FULL_REPLAY",
        "snn_ecg_mb_template": "snn_ecg_mb_full_replay",
        "MicroBlaze template": "MicroBlaze full-record replay",
        "MicroBlaze packaged-IP template": "MicroBlaze packaged-IP full-record replay",
        "CONFIG.SNAPSHOT_SAMPLES {8}": f"CONFIG.SNAPSHOT_SAMPLES {{{SNAPSHOT_SAMPLES}}}",
        "CONFIG.SNAPSHOTS_PER_CHUNK {2}": f"CONFIG.SNAPSHOTS_PER_CHUNK {{{SNAPSHOTS_PER_CHUNK}}}",
        "CONFIG.POST_DONE_TICKS {37}": f"CONFIG.POST_DONE_TICKS {{{POST_DONE_TICKS}}}",
        "CONFIG.PROFILE_EN {1}": f"CONFIG.PROFILE_EN {{{PROFILE_EN}}}",
        "CONFIG.TLAST_CHECK_EN {1}": f"CONFIG.TLAST_CHECK_EN {{{TLAST_CHECK_EN}}}",
        "CONFIG.C_BAUDRATE {115200}": f"CONFIG.C_BAUDRATE {{{UART_BAUD}}}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    full_tcl = RESULTS / "build_microblaze_full_replay_system.tcl"
    full_tcl.write_text(text, encoding="utf-8", newline="\n")
    if tcl != full_tcl and tcl.exists():
        tcl.unlink()
    return full_tcl


def ensure_packaged_ips(skip_package: bool) -> None:
    base.RESULTS = RESULTS
    base.ensure_packaged_ips(skip_package)


def parse_timing(path: Path) -> dict[str, float | int | None]:
    return base.parse_timing(path)


def parse_util(path: Path) -> dict[str, str]:
    return base.parse_util(path)


def write_summary(no_bitstream: bool) -> None:
    reports = RESULTS / "reports"
    timing_path = reports / "system_timing_summary.rpt"
    util_path = reports / "system_utilization.rpt"
    cdc_path = reports / "system_cdc.rpt"
    timing_text = timing_path.read_text(encoding="utf-8", errors="replace") if timing_path.exists() else ""
    check_timing_clean = False
    cdc_clean = False
    if timing_path.exists():
        check_timing_clean = all(
            marker in timing_text
            for marker in [
                "checking no_clock (0)",
                "checking unconstrained_internal_endpoints (0)",
                "There are 0 input ports with no input delay specified.",
                "There are 0 ports with no output delay specified.",
                "checking partial_input_delay (0)",
                "checking partial_output_delay (0)",
            ]
        )
    if cdc_path.exists():
        cdc_text = cdc_path.read_text(encoding="utf-8", errors="replace")
        cdc_clean = not re.search(r"\b(Critical|Warning)\b", cdc_text)

    summary = {
        "top": "snn_ecg_mb_full_replay_wrapper",
        "part": PART,
        "full_record_parameters": {
            "snapshot_samples": SNAPSHOT_SAMPLES,
            "snapshots_per_chunk": SNAPSHOTS_PER_CHUNK,
            "total_samples": TOTAL_SAMPLES,
            "post_done_ticks": POST_DONE_TICKS,
            "tlast_check_en": TLAST_CHECK_EN,
            "profile_en": PROFILE_EN,
            "uart_baud": UART_BAUD,
        },
        "addresses": {
            "snn_ecg_axi_accelerator": f"0x{SNN_BASE:08x}",
            "sample_feeder": f"0x{FEEDER_BASE:08x}",
            "axi_uartlite": f"0x{UART_BASE:08x}",
            "axi_intc": f"0x{INTC_BASE:08x}",
        },
        "bitstream": str(RESULTS / "snn_ecg_mb_full_replay.bit"),
        "bitstream_exists": (RESULTS / "snn_ecg_mb_full_replay.bit").exists() if not no_bitstream else False,
        "xsa": str(RESULTS / "snn_ecg_mb_full_replay.xsa"),
        "xsa_exists": (RESULTS / "snn_ecg_mb_full_replay.xsa").exists(),
        "timing_constraints_met": timing_path.exists() and (
            "Timing constraints are met." in timing_text
            or "All user specified timing constraints are met." in timing_text
        ),
        "timing": parse_timing(timing_path) if timing_path.exists() else {},
        "check_timing_clean_markers": check_timing_clean,
        "cdc_clean_markers": cdc_clean,
        "utilization": parse_util(util_path) if util_path.exists() else {},
        "reports": {
            "timing": str(timing_path),
            "cdc": str(cdc_path),
            "clock_interaction": str(reports / "system_clock_interaction.rpt"),
            "drc": str(reports / "system_drc.rpt"),
            "io": str(reports / "system_io.rpt"),
            "route_status": str(reports / "system_route_status.rpt"),
            "utilization": str(util_path),
            "utilization_hier": str(reports / "system_utilization_hier.rpt"),
            "bd_address": str(reports / "system_bd_address.rpt"),
            "ip_status": str(reports / "system_ip_status.rpt"),
        },
    }
    (RESULTS / "microblaze_full_replay_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the MicroBlaze full-record board replay system.")
    parser.add_argument("--skip-package", action="store_true", help="Do not regenerate local packaged IPs first.")
    parser.add_argument("--no-bitstream", action="store_true", help="Stop at routed implementation reports without writing a bitstream.")
    parser.add_argument("--keep-work", action="store_true", help="Keep the previous external Vivado work directory.")
    args = parser.parse_args()

    if not base.VIVADO.exists():
        raise FileNotFoundError(f"Vivado not found: {base.VIVADO}")
    if WORK.exists() and not args.keep_work:
        shutil.rmtree(WORK)
    RESULTS.mkdir(parents=True, exist_ok=True)
    ensure_packaged_ips(args.skip_package)
    tcl = write_tcl(args.no_bitstream)
    base.run(
        [str(base.VIVADO), "-mode", "batch", "-nojournal", "-nolog", "-source", base.slash(tcl)],
        REPO,
        RESULTS / "vivado_microblaze_full_replay_build.log",
    )
    write_summary(args.no_bitstream)
    print(RESULTS / "microblaze_full_replay_summary.json")


if __name__ == "__main__":
    main()
