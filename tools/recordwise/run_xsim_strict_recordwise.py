from __future__ import annotations

import argparse
import sys

from recordwise_common import REPORTS, write_csv, write_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare/report strict record-wise XSim rerun status.")
    parser.add_argument("--run", action="store_true", help="Reserved for future full XSim execution.")
    args = parser.parse_args()

    xsim_dir = REPORTS / "xsim"
    summary = xsim_dir / "strict_recordwise_xsim_summary.md"
    mismatch = xsim_dir / "strict_recordwise_xsim_mismatch.csv"
    write_csv(mismatch, [{"status": "not_run", "reason": "strict params export exists, but RTL include/integration is not yet wired"}])
    lines = [
        "# Strict Record-wise XSim Status",
        "",
        "- Status: `TODO / not run`",
        "- Python strict record-wise final test is separate from RTL/XSim proof.",
        "- Reason: strict search exports parameters to `generated/recordwise_params_pkg.sv` and `generated/recordwise_params.vh`, but the existing RTL is not automatically rewired to consume those generated parameters.",
        "- Existing XSim evidence for the frozen V2 RTL remains under `results/final_membrane_v2_snn/`; it should not be re-labeled as strict record-wise parameter verification.",
        "",
        "## Next Steps",
        "",
        "1. Wire exported strict parameters into the Python-to-RTL expected generation path or RTL localparams.",
        "2. Regenerate strict record-wise test manifests for XSim.",
        "3. Run RTL-vs-Python comparison and populate `strict_recordwise_xsim_mismatch.csv` with real mismatch rows.",
    ]
    if args.run:
        lines.insert(2, "- Requested `--run`, but execution is intentionally blocked until RTL parameter integration is implemented.")
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    write_log("run_xsim_strict_recordwise", sys.argv, [summary, mismatch], {"status": "not_run", "rtl_params_integrated": False})
    print(summary)


if __name__ == "__main__":
    main()
