#!/usr/bin/env python3
"""Apply captured ECG SAIF activity to baseline and power-optimized DCPs."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
POWER = REPO / "benchmarks" / "accelerator_benefit" / "power"
MANIFEST = POWER / "results" / "activity" / "activity_manifest.json"
VIVADO = Path(r"C:\Xilinx\Vivado\2020.2\bin\vivado.bat")
SCRIPT = POWER / "report_activity_power.tcl"
DCP = {
    "baseline": POWER / "work" / "pure_rtl_100mhz" / "pure_rtl_100mhz_routed.dcp",
    "power_opt": POWER / "work" / "pure_rtl_100mhz" / "pure_rtl_100mhz_power_opt_routed.dcp",
    "ip_baseline": POWER / "work" / "accelerator_ip_100mhz" / "accelerator_ip_100mhz_routed.dcp",
    "ip_power_opt": POWER / "work" / "accelerator_ip_100mhz" / "accelerator_ip_100mhz_power_opt_routed.dcp",
}


def slash(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation", choices=[*DCP, "all"], default="all")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--mode", choices=["burst_full_record", "streaming_1ksps_prefix"])
    args = parser.parse_args()
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    implementations = list(DCP) if args.implementation == "all" else [args.implementation]
    selected = []
    for record in payload["records"]:
        if args.case_id and record["case_id"] not in args.case_id:
            continue
        if args.mode and record["mode"] != args.mode:
            continue
        selected.append(record)
    if not selected:
        raise SystemExit("no matching activity records")
    for implementation in implementations:
        dcp = DCP[implementation]
        if not dcp.exists():
            raise FileNotFoundError(dcp)
        for record in selected:
            case_id = record["case_id"]
            mode = record["mode"]
            saif = REPO / record["saif"]
            out = POWER / "results" / "activity_power" / implementation / case_id / mode
            prefix = f"{case_id}_{mode}_{implementation}"
            activity_description = (
                "Full-record real-ECG preloaded burst RTL SAIF"
                if mode == "burst_full_record"
                else "Literal 100 MHz / 1 kS/s representative-prefix real-ECG RTL SAIF"
            )
            command = [
                str(VIVADO), "-mode", "batch", "-nolog", "-nojournal", "-source", slash(SCRIPT), "-tclargs",
                slash(dcp), slash(saif), payload["saif_strip_path"], slash(out), prefix, activity_description,
            ]
            out.mkdir(parents=True, exist_ok=True)
            log = out / f"{prefix}_vivado.log"
            expected_outputs = [
                out / f"{prefix}_power_post_route.rpt",
                out / f"{prefix}_utilization_post_route.rpt",
                out / f"{prefix}_timing_post_route.rpt",
                out / f"{prefix}_saif_unmatched.rpt",
                out / f"{prefix}_environment.txt",
            ]
            if all(path.exists() and path.stat().st_size > 0 for path in expected_outputs):
                print(f"reuse {out}")
                continue
            with log.open("w", encoding="utf-8", errors="replace") as handle:
                process = subprocess.run(command, cwd=REPO, stdout=handle, stderr=subprocess.STDOUT, text=True)
            if process.returncode != 0:
                raise RuntimeError(f"Vivado activity power failed; see {log}")
            print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
