from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Sequence

import ecg_to_xmodel_stimulus as stimulus


CLASS_SEGMENT_MAP = {
    "NSR": "NSR",
    "NSRDB": "NSR",
    "NORMAL": "NSR",
    "CHF": "CHF",
    "CHFDB": "CHF",
    "ARR": "ARR",
    "MITDB": "ARR",
    "MIT-BIH": "ARR",
    "AFF": "AFF",
    "AFDB": "AFF",
    "AF": "AFF",
}

GENERATED_NAMES = {
    "stimulus_xmodel.csv",
    "stimulus_pwl.txt",
    "metadata.json",
    "summary_manifest.csv",
    "summary_metadata.json",
}

MANIFEST_FIELDS = [
    "class",
    "record_id",
    "input_path",
    "out_dir",
    "status",
    "error",
    "stimulus_xmodel_csv",
    "stimulus_pwl_txt",
    "metadata_json",
    "qa_plot_png",
    "readme_stimulus_md",
    "warnings",
]


def detect_class(path: Path, input_root: Path) -> str | None:
    try:
        rel_parts = path.relative_to(input_root).parts
    except ValueError:
        rel_parts = path.parts
    for part in rel_parts:
        key = part.upper()
        if key in CLASS_SEGMENT_MAP:
            return CLASS_SEGMENT_MAP[key]
    return None


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def discover_inputs(input_root: Path, output_root: Path | None = None) -> list[Path]:
    records: list[Path] = []
    seen_wfdb: set[Path] = set()
    for path in sorted(input_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in GENERATED_NAMES:
            continue
        if output_root is not None and is_relative_to(path, output_root):
            continue
        suffix = path.suffix.lower()
        if suffix == ".csv":
            records.append(path)
        elif suffix == ".hea":
            stem = path.with_suffix("")
            if stem not in seen_wfdb:
                seen_wfdb.add(stem)
                records.append(path)
    return records


def safe_record_id(path: Path, input_root: Path) -> str:
    rel = path.relative_to(input_root).with_suffix("")
    return "__".join(part.replace(" ", "_") for part in rel.parts)


def build_single_args(batch_args: argparse.Namespace, input_path: Path, out_dir: Path) -> list[str]:
    argv = [
        "--input",
        str(input_path),
        "--out-dir",
        str(out_dir),
        "--channel",
        str(batch_args.channel),
        "--start-sec",
        str(batch_args.start_sec),
        "--stim-fs",
        str(batch_args.stim_fs),
        "--dac-mode",
        batch_args.dac_mode,
        "--nan-policy",
        batch_args.nan_policy,
        "--max-output-points",
        str(batch_args.max_output_points),
        "--low-source-fs-warn-hz",
        str(batch_args.low_source_fs_warn_hz),
        "--amplitude-warn-v",
        str(batch_args.amplitude_warn_v),
    ]
    if batch_args.duration_sec is not None:
        argv.extend(["--duration-sec", str(batch_args.duration_sec)])
    if batch_args.fs is not None:
        argv.extend(["--fs", str(batch_args.fs)])
    if batch_args.input_units is not None:
        argv.extend(["--input-units", batch_args.input_units])
    if batch_args.time_col is not None:
        argv.extend(["--time-col", batch_args.time_col])
    if batch_args.value_col is not None:
        argv.extend(["--value-col", batch_args.value_col])
    if batch_args.truncate_to_max:
        argv.append("--truncate-to-max")
    return argv


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_batch(args: argparse.Namespace) -> dict[str, object]:
    input_root = Path(args.input_root).expanduser()
    output_root = Path(args.output_root).expanduser()
    if not input_root.exists():
        raise FileNotFoundError(input_root)
    output_root.mkdir(parents=True, exist_ok=True)

    records = discover_inputs(input_root, output_root)
    rows: list[dict[str, object]] = []
    counts = {"ok": 0, "failed": 0, "skipped": 0}
    allowed_classes = {cls.strip().upper() for cls in args.classes.split(",") if cls.strip()}

    for input_path in records:
        cls = detect_class(input_path, input_root)
        if cls is None or cls.upper() not in allowed_classes:
            counts["skipped"] += 1
            continue
        record_id = safe_record_id(input_path, input_root)
        out_dir = output_root / cls / record_id
        row: dict[str, object] = {field: "" for field in MANIFEST_FIELDS}
        row.update(
            {
            "class": cls,
            "record_id": record_id,
            "input_path": str(input_path),
            "out_dir": str(out_dir),
            "status": "pending",
            "error": "",
            }
        )
        try:
            single_argv = build_single_args(args, input_path, out_dir)
            result = stimulus.main(single_argv)
            row.update(
                {
                    "status": "ok",
                    "stimulus_xmodel_csv": str(result.stimulus_csv),
                    "stimulus_pwl_txt": str(result.stimulus_pwl),
                    "metadata_json": str(result.metadata_json),
                    "qa_plot_png": str(result.qa_plot),
                    "readme_stimulus_md": str(result.readme),
                    "warnings": len(result.metadata.get("warnings", [])),
                }
            )
            counts["ok"] += 1
        except Exception as exc:  # Keep batch generation moving across records.
            row["status"] = "failed"
            row["error"] = str(exc)
            counts["failed"] += 1
            print(f"[failed] {input_path}: {exc}", file=sys.stderr)
        rows.append(row)
        if args.max_records is not None and counts["ok"] >= args.max_records:
            break

    manifest_csv = output_root / "summary_manifest.csv"
    summary_json = output_root / "summary_metadata.json"
    write_manifest(manifest_csv, rows)
    summary = {
        "input_root": str(input_root),
        "output_root": str(output_root),
        "counts": counts,
        "records_seen": len(records),
        "manifest_csv": str(manifest_csv),
        "rows": rows,
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch-build XMODEL ECG stimulus artifacts by class.")
    parser.add_argument("--input-root", required=True, help="Root containing NSR/CHF/ARR/AFF or nsrdb/chfdb/mitdb/afdb data.")
    parser.add_argument("--output-root", default=str(Path("build") / "xmodel_stimulus"), help="Output root.")
    parser.add_argument("--classes", default="NSR,CHF,ARR,AFF", help="Comma-separated class filter.")
    parser.add_argument("--channel", default="0")
    parser.add_argument("--value-col", default=None)
    parser.add_argument("--time-col", default=None)
    parser.add_argument("--fs", type=float, default=None)
    parser.add_argument("--input-units", default=None)
    parser.add_argument("--start-sec", type=float, default=0.0)
    parser.add_argument("--duration-sec", type=float, default=None)
    parser.add_argument("--stim-fs", type=float, default=10000.0)
    parser.add_argument("--dac-mode", choices=stimulus.DAC_MODES, default="linear")
    parser.add_argument("--nan-policy", choices=("error", "interpolate", "drop", "zero"), default="interpolate")
    parser.add_argument("--max-output-points", type=int, default=2_000_000)
    parser.add_argument("--truncate-to-max", action="store_true")
    parser.add_argument("--low-source-fs-warn-hz", type=float, default=300.0)
    parser.add_argument("--amplitude-warn-v", type=float, default=0.020)
    parser.add_argument("--max-records", type=int, default=None, help="Optional smoke-test limit on successful records.")
    return parser


def main(argv: Sequence[str] | None = None) -> dict[str, object]:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_batch(args)


if __name__ == "__main__":
    main()
