#!/usr/bin/env python3
"""Validate canonical files, metrics, figures, and claim boundaries."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

REQUIRED = [
    "README.md", "START_HERE_KR.md", "REPRODUCIBILITY_KR.md", "WORKSPACE_INVENTORY_KR.md",
    "docs/SYSTEM_OVERVIEW_KR.md", "docs/DATASET_AND_EVALUATION_KR.md",
    "docs/FEATURE_SELECTION_AND_ANNOTATION_KR.md", "docs/DIGITAL_ARCHITECTURE_KR.md",
    "docs/HARDWARE_IMPLEMENTATION_KR.md", "docs/INTEGRATION_VERIFICATION_KR.md",
    "docs/LIMITATIONS_AND_CLAIM_BOUNDARY_KR.md", "docs/RELATED_WORK_HOLTER_ECG_KR.md",
    "reports/INTEGRATED_TECHNICAL_REPORT_KR.md",
    "reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv",
    "INTEGRATION_AUDIT.md", "LICENSE_OR_PROVENANCE.md",
    "project_registry/claim_registry.csv", "project_registry/upstream_commits.yaml",
    "project_registry/artifact_manifest.csv",
    "project_registry/external_reference_registry.csv", "project_registry/unresolved_artifacts.csv",
    "verification/timing_optimization/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md",
    "verification/xmodel_rtl_acceptance_36case/output_equivalence_36case.csv",
    "verification/xmodel_rtl_e2e/overall_summary.csv",
    "design/digital/rtl/snn_ecg_30min_final_top.v",
    "design/digital/reports/final/final_metrics.json",
    "design/digital/reports/final/board_replay_36_batch_summary.json",
    "models/digital_equivalence/results/accelerator_benefit_summary.csv",
    "models/digital_equivalence/results/power_energy_summary.csv",
    "figures/FIGURE_INDEX.md",
    "vivado/microblaze/SNN_ECG_MB_FULL_REPLAY.xpr",
    "vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr",
]
PUBLIC_TEXT = [
    "README.md", "START_HERE_KR.md", "REPRODUCIBILITY_KR.md",
    "reports/INTEGRATED_TECHNICAL_REPORT_KR.md",
]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def run_checker(path: str) -> tuple[bool, str]:
    result = subprocess.run([PYTHON, str(ROOT / path)], cwd=ROOT, text=True, capture_output=True)
    return result.returncode == 0, result.stdout + result.stderr


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"missing required artifact: {rel}")

    manifest_path = ROOT / "project_registry/artifact_manifest.csv"
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
            manifest_rows = list(csv.DictReader(handle))
        manifest_by_path = {row.get("path", ""): row for row in manifest_rows}
        current_files: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path == manifest_path:
                continue
            rel = path.relative_to(ROOT)
            if any(part in {".git", "tmp", "__pycache__", ".pytest_cache", ".mypy_cache"} for part in rel.parts):
                continue
            current_files.append(rel.as_posix())
        if set(manifest_by_path) != set(current_files):
            missing = sorted(set(current_files) - set(manifest_by_path))
            stale = sorted(set(manifest_by_path) - set(current_files))
            errors.append(f"artifact manifest path mismatch: missing={missing[:5]}, stale={stale[:5]}")
        else:
            for rel in current_files:
                row = manifest_by_path[rel]
                path = ROOT / rel
                if row.get("sha256") != file_sha256(path) or row.get("size_bytes") != str(path.stat().st_size):
                    errors.append(f"artifact manifest hash/size mismatch: {rel}")
                    break

    metrics_path = ROOT / "design/digital/reports/final/final_metrics.json"
    if metrics_path.exists():
        raw = metrics_path.read_text(encoding="utf-8")
        for token in ["80.56", "80.44", "9719", "5038", "8.184", "12494", "8494", "0.097"]:
            if token not in raw:
                errors.append(f"final_metrics.json lacks expected token: {token}")

    compact = ROOT / "verification/xmodel_rtl_acceptance_36case/output_equivalence_36case.csv"
    if compact.exists():
        with compact.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 36 or not all(row.get("pred_match", "").lower() == "true" and row.get("mem_match", "").lower() == "true" for row in rows):
            errors.append("compact XMODEL/RTL acceptance is not 36/36")

    raw_audit = ROOT / "verification/xmodel_rtl_e2e/overall_summary.csv"
    if raw_audit.exists():
        with raw_audit.open(encoding="utf-8-sig", newline="") as handle:
            audit = {row["metric"]: row for row in csv.DictReader(handle)}
        present = audit.get("actual_xmodel_adc_files_present_valid", {})
        if present.get("pass_count") != "4" or present.get("required_count") != "36":
            errors.append("raw-dump audit scope must remain explicitly 4/36")

    figures_index = (ROOT / "figures/FIGURE_INDEX.md").read_text(encoding="utf-8") if (ROOT / "figures/FIGURE_INDEX.md").exists() else ""
    figure_files = list((ROOT / "figures/final_submission").rglob("*.svg"))
    if len(figure_files) < 10:
        errors.append(f"too few final SVG figures: {len(figure_files)}")
    for p in figure_files:
        if p.name not in figures_index and p.stem not in figures_index:
            errors.append(f"final figure absent from index: {p.relative_to(ROOT)}")

    for rel in PUBLIC_TEXT:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "SNN-inspired" in text:
            errors.append(f"legacy SNN-inspired wording in public text: {rel}")

    ok, output = run_checker("tools/check_clean_workspace.py")
    if not ok:
        errors.append("clean workspace checker failed:\n" + output.strip())
    ok, output = run_checker("tools/check_integrated_technical_report.py")
    if not ok:
        errors.append("technical report checker failed:\n" + output.strip())

    if errors:
        print("INTEGRATED_REPOSITORY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("INTEGRATED_REPOSITORY: PASS")
    print(f"- {len(REQUIRED)} canonical artifacts present")
    print(f"- {len(figure_files)} indexed final SVG figures")
    print("- fixed metrics and evidence-scope boundaries verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
