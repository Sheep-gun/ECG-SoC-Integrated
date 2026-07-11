#!/usr/bin/env python3
"""Validate the final paper-style repository surface."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
FINAL_MODEL = "structural_guarded_silent_aff_1008710"

EXPECTED = {
    ("train", "correct"): 61,
    ("train", "total"): 68,
    ("train", "accuracy_percent"): 89.71,
    ("validation", "correct"): 32,
    ("validation", "total"): 32,
    ("validation", "accuracy_percent"): 100.0,
    ("final_test_chunk", "correct"): 29,
    ("final_test_chunk", "total"): 36,
    ("final_test_chunk", "accuracy_percent"): 80.56,
    ("final_test_chunk", "macro_f1_percent"): 80.44,
    ("final_test_chunk", "balanced_accuracy_percent"): 80.56,
    ("final_test_record_majority", "correct"): 16,
    ("final_test_record_majority", "total"): 19,
    ("final_test_record_majority", "accuracy_percent"): 84.21,
    ("final_test_record_majority", "macro_f1_percent"): 80.8,
    ("final_test_record_majority", "balanced_accuracy_percent"): 88.19,
}

EXPECTED_RECALL = {
    "final_test_chunk": {"NSR": 100.0, "CHF": 66.67, "ARR": 77.78, "AFF": 77.78},
    "final_test_record_majority": {"NSR": 100.0, "CHF": 75.0, "ARR": 77.78, "AFF": 100.0},
}

REQUIRED_FILES = [
    "README.md",
    "FINAL_REPORT_KR.md",
    "configs/final_submission_locked_model.json",
    "configs/recordwise_resplit_seed20260808/final_test_records_locked.json",
    "configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json",
    "configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json",
    "docs/PAPER_SUMMARY_KR.md",
    "docs/SYSTEM_ARCHITECTURE_KR.md",
    "docs/STRICT_RECORDWISE_PROTOCOL_KR.md",
    "docs/HARDWARE_VALIDATION_KR.md",
    "docs/LIMITATIONS_KR.md",
    "reports/final/final_metrics.json",
    "reports/final/strict_recordwise_final_result.md",
    "reports/final/strict_recordwise/strict_recordwise_metric_summary.json",
    "reports/final/strict_recordwise/final_test_chunk_class_metrics.csv",
    "reports/final/strict_recordwise/final_test_record_majority_class_metrics.csv",
    "reports/final/hardware_validation_result.md",
    "reports/final/xsim_locked_model_summary.md",
    "reports/final/vivado_locked_model_metrics.md",
    "reports/final/board_replay_result.md",
    "reports/final/board_replay_36_preflight_audit.md",
    "reports/final/board_replay_36_cases.csv",
    "reports/final/board_replay_36_cases.json",
    "reports/final/board_replay_36_expected_vs_board.csv",
    "reports/final/board_replay_36_batch_summary.md",
    "reports/final/board_replay_36_batch_summary.json",
    "reports/final/board_replay_36_final_mem_alignment_audit.md",
    "reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv",
    "reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_metadata.json",
    "reports/final/fulltop_xsim_final_test_36/locked_class_cases_xsim_vs_board.csv",
    "reports/final/fulltop_xsim_final_test_36/locked_class_cases_xsim_vs_board_summary.json",
    "reports/final/fulltop_xsim_final_test_36/locked_class_cases_xsim_vs_board_summary.md",
    "reports/final/formatting_and_figure_audit.md",
    "reports/final/figures/FIGURE_INDEX.md",
    "reports/final/fulltop_xsim_locked_class_cases_predictions.csv",
    "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit",
    "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa",
    "results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf",
    "tools/evaluate_final_strict_recordwise.py",
    "tools/collect_final_vivado_metrics.py",
    "tools/board_replay/run_locked_fulltop_xsim_cases.py",
    "tools/board_replay/run_full_record_batch_36.py",
    "tools/board_replay/send_full_record_uart.py",
    "tools/check_final_paper_repo.py",
    "tools/make_final_report_figures.py",
]

FINAL_DOC_GLOBS = [
    "README.md",
    "FINAL_REPORT_KR.md",
    "docs/*.md",
    "reports/final/*.md",
    "reports/final/*.json",
    "configs/*.json",
    "configs/recordwise_resplit_seed20260808/*.json",
]

MARKDOWN_LINK_GLOBS = [
    "README.md",
    "FINAL_REPORT_KR.md",
    "docs/*.md",
    "reports/final/*.md",
]

REQUIRED_FIGURES = [
    "reports/final/figures/final_system_architecture.png",
    "reports/final/figures/snapshot_to_final_membrane_pipeline.png",
    "reports/final/figures/strict_recordwise_protocol.png",
    "reports/final/figures/final_result_summary.png",
    "reports/final/figures/hardware_validation_flow.png",
    "reports/final/figures/resource_timing_summary.png",
    "reports/final/figures/board_replay_pass_matrix.png",
    "reports/final/figures/final_test_confusion_matrix.png",
]

REQUIRED_IMAGE_LINKS = {
    "README.md": [
        "reports/final/figures/final_system_architecture.png",
        "reports/final/figures/final_result_summary.png",
    ],
    "FINAL_REPORT_KR.md": [
        "reports/final/figures/final_system_architecture.png",
        "reports/final/figures/snapshot_to_final_membrane_pipeline.png",
        "reports/final/figures/strict_recordwise_protocol.png",
        "reports/final/figures/final_result_summary.png",
        "reports/final/figures/hardware_validation_flow.png",
        "reports/final/figures/resource_timing_summary.png",
        "reports/final/figures/board_replay_pass_matrix.png",
        "reports/final/figures/final_test_confusion_matrix.png",
    ],
}

FORBIDDEN_PATTERNS = [
    r"margin_" + r"evidence_0038974",
    r"test_" + r"case_0_nsr",
    r"test_" + r"case_0",
    r"chunk" + r"-level",
    r"chunk" + r" level",
    r"\b88" + r"\.89\b",
    r"\b32" + r"/36\b",
    r"final_" + r"membrane_v2",
    r"snapshot_" + r"v2",
    r"SNN_" + r"ECG_" + r"V" + r"2",
    r"SNN ECG " + r"V" + r"2",
    r"holdout\s+" + r"reconfig",
    r"holdout " + r"\uc7ac\uad6c\uc131",
    r"test\ub97c " + r"\ubcf4\uace0",
    r"post" + r"-test",
    r"re" + r"-tune",
    r"re" + r"tune",
    r"raw analog ECG " + r"recovered",
    r"actual AFE PCB " + r"verified",
    r"Virtuoso post-layout " + r"verified",
    r"clinical " + r"validation " + r"completed",
]

BOARD_CASES = [
    "locked_nsr_case117",
    "locked_chf_case91",
    "locked_arr_case45",
    "locked_aff_case16",
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(rel_path: str) -> dict:
    return json.loads((REPO / rel_path).read_text(encoding="utf-8-sig"))


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def check_required_files(failures: list[str]) -> None:
    for item in REQUIRED_FILES:
        if not (REPO / item).exists():
            fail(f"missing required file: {item}", failures)


def check_required_figures(failures: list[str]) -> None:
    for item in REQUIRED_FIGURES:
        path = REPO / item
        if not path.exists():
            fail(f"missing required figure: {item}", failures)
        elif path.stat().st_size <= 0:
            fail(f"empty required figure: {item}", failures)
        else:
            with Image.open(path) as image:
                width, height = image.size
            if width < 1400 or height < 780:
                fail(f"final figure is too small for report use: {item} ({width}x{height})", failures)


def check_doc_count(failures: list[str]) -> None:
    docs = sorted(path.name for path in (REPO / "docs").glob("*.md"))
    expected = sorted(
        [
            "PAPER_SUMMARY_KR.md",
            "SYSTEM_ARCHITECTURE_KR.md",
            "STRICT_RECORDWISE_PROTOCOL_KR.md",
            "HARDWARE_VALIDATION_KR.md",
            "LIMITATIONS_KR.md",
        ]
    )
    if docs != expected:
        fail(f"unexpected docs set: {docs}", failures)


def check_forbidden_patterns(failures: list[str]) -> None:
    files: list[Path] = []
    for pattern in FINAL_DOC_GLOBS:
        files.extend(REPO.glob(pattern))
    regexes = [(pattern, re.compile(pattern, re.IGNORECASE)) for pattern in FORBIDDEN_PATTERNS]
    for path in sorted(set(files)):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for label, regex in regexes:
            if regex.search(text):
                fail(f"forbidden pattern {label!r} found in {rel(path)}", failures)


def local_link_target(raw: str) -> str | None:
    target = raw.strip()
    if not target or target.startswith("#"):
        return None
    lowered = target.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "data:")):
        return None
    if target.startswith("<"):
        end = target.find(">")
        target = target[1:end] if end != -1 else target[1:]
    else:
        target = target.split()[0]
    target = unquote(target)
    if "#" in target:
        target = target.split("#", 1)[0]
    return target or None


def check_markdown_links(failures: list[str]) -> None:
    link_re = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    files: list[Path] = []
    for pattern in MARKDOWN_LINK_GLOBS:
        files.extend(REPO.glob(pattern))
    for path in sorted(set(files)):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for match in link_re.finditer(text):
            target = local_link_target(match.group(1))
            if target is None:
                continue
            target_path = Path(target)
            if not target_path.is_absolute():
                target_path = path.parent / target_path
            if not target_path.exists():
                fail(f"broken markdown link in {rel(path)}: {match.group(1)}", failures)


def check_markdown_image_links(failures: list[str]) -> None:
    image_re = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    files: list[Path] = []
    for pattern in MARKDOWN_LINK_GLOBS:
        files.extend(REPO.glob(pattern))
    for path in sorted(set(files)):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        image_targets = [local_link_target(match.group(1)) for match in image_re.finditer(text)]
        image_targets = [target for target in image_targets if target is not None]
        for target in image_targets:
            target_path = Path(target)
            if not target_path.is_absolute():
                target_path = path.parent / target_path
            if not target_path.exists():
                fail(f"broken markdown image link in {rel(path)}: {target}", failures)
        required = REQUIRED_IMAGE_LINKS.get(rel(path), [])
        normalized = {str((path.parent / target).resolve()).replace("\\", "/") for target in image_targets}
        for target in required:
            expected = str((REPO / target).resolve()).replace("\\", "/")
            if expected not in normalized:
                fail(f"missing required image link in {rel(path)}: {target}", failures)


def check_mermaid_fences(failures: list[str]) -> None:
    required = ["README.md", "FINAL_REPORT_KR.md", "docs/SYSTEM_ARCHITECTURE_KR.md"]
    for item in required:
        text = (REPO / item).read_text(encoding="utf-8-sig", errors="replace")
        if "```mermaid" not in text:
            fail(f"missing mermaid code fence: {item}", failures)
        if text.count("```mermaid") > text.count("```") // 2:
            fail(f"possibly unclosed mermaid code fence: {item}", failures)


def check_markdown_heading_spacing(failures: list[str]) -> None:
    files: list[Path] = []
    for pattern in MARKDOWN_LINK_GLOBS:
        files.extend(REPO.glob(pattern))
    heading_re = re.compile(r"#{1,6}\s+\S")
    for path in sorted(set(files)):
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        in_fence = False
        for idx, line in enumerate(lines):
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not heading_re.match(line):
                continue
            if idx > 0 and lines[idx - 1].strip():
                fail(f"heading missing blank line before in {rel(path)}:{idx + 1}", failures)
            if idx + 1 < len(lines) and lines[idx + 1].strip():
                fail(f"heading missing blank line after in {rel(path)}:{idx + 1}", failures)


def check_markdown_tables(failures: list[str]) -> None:
    files: list[Path] = []
    for pattern in MARKDOWN_LINK_GLOBS:
        files.extend(REPO.glob(pattern))
    for path in sorted(set(files)):
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        in_fence = False
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line.startswith("```"):
                in_fence = not in_fence
                idx += 1
                continue
            if in_fence or not line.startswith("|") or idx + 1 >= len(lines):
                idx += 1
                continue
            sep = lines[idx + 1]
            if sep.startswith("|") and re.fullmatch(r"\|(?:\s*:?-{3,}:?\s*\|)+", sep):
                cols = line.count("|")
                sep_cols = sep.count("|")
                if cols != sep_cols:
                    fail(f"markdown table header/separator column mismatch in {rel(path)}:{idx + 1}", failures)
                row_idx = idx + 2
                while row_idx < len(lines) and lines[row_idx].startswith("|"):
                    if lines[row_idx].count("|") != cols:
                        fail(f"markdown table row column mismatch in {rel(path)}:{row_idx + 1}", failures)
                    row_idx += 1
                idx = row_idx
                continue
            idx += 1


def check_metrics(failures: list[str]) -> None:
    metrics = read_json("reports/final/final_metrics.json")
    submission = read_json("configs/final_submission_locked_model.json")
    locked = read_json("configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json")

    for name, payload in [("final_metrics", metrics), ("final_submission", submission)]:
        if payload.get("final_model_id") != FINAL_MODEL:
            fail(f"{name} final_model_id mismatch: {payload.get('final_model_id')}", failures)
        for (section, key), expected in EXPECTED.items():
            got = payload.get(section, {}).get(key)
            if got != expected:
                fail(f"{name} {section}.{key} expected {expected}, got {got}", failures)
        for section, expected_recall in EXPECTED_RECALL.items():
            got_recall = payload.get(section, {}).get("class_recall_percent", {})
            if got_recall != expected_recall:
                fail(f"{name} {section}.class_recall_percent expected {expected_recall}, got {got_recall}", failures)
    summary = read_json("reports/final/strict_recordwise/strict_recordwise_metric_summary.json")
    for (section, key), expected in EXPECTED.items():
        if section not in {"final_test_chunk", "final_test_record_majority"}:
            continue
        got = summary.get(section, {}).get(key)
        if got != expected:
            fail(f"strict_recordwise_metric_summary {section}.{key} expected {expected}, got {got}", failures)
    for section, expected_recall in EXPECTED_RECALL.items():
        got_recall = summary.get(section, {}).get("class_recall_percent", {})
        if got_recall != expected_recall:
            fail(f"strict_recordwise_metric_summary {section}.class_recall_percent expected {expected_recall}, got {got_recall}", failures)
    if locked.get("selected_candidate_id") != FINAL_MODEL:
        fail(f"locked JSON candidate mismatch: {locked.get('selected_candidate_id')}", failures)
    if locked.get("test_used_for_selection") is not False:
        fail("locked JSON test_used_for_selection must be false", failures)
    if locked.get("test_used_for_parameter_search") is not False:
        fail("locked JSON test_used_for_parameter_search must be false", failures)
    if locked.get("test_used_for_chatgpt_context") is not False:
        fail("locked JSON test_used_for_chatgpt_context must be false", failures)


def check_board_replay(failures: list[str]) -> None:
    for case in BOARD_CASES:
        comparison = REPO / "reports" / "final" / "board_replay" / f"{case}_expected_vs_board.csv"
        transcript = REPO / "reports" / "final" / "board_replay" / f"{case}_uart_full_replay.txt"
        summary = REPO / "reports" / "final" / "board_replay" / f"{case}_summary.md"
        for path in [comparison, transcript, summary]:
            if not path.exists():
                fail(f"missing board replay artifact: {rel(path)}", failures)
        if not comparison.exists():
            continue
        with comparison.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        mismatches = [row for row in rows if row.get("match") not in ("1", "")]
        if mismatches:
            fail(f"board replay mismatch in {rel(comparison)}: {mismatches[:3]}", failures)
        required_metrics = {
            "samples_received": "1800000",
            "snapshot_count": "30",
            "decision_count": "1",
            "final_valid": "1",
            "done": "1",
        }
        by_metric = {row.get("metric"): row for row in rows}
        for metric, expected in required_metrics.items():
            row = by_metric.get(metric)
            if row is None or row.get("board") != expected or row.get("match") != "1":
                fail(f"{case} {metric} expected board={expected}, match=1", failures)
        if transcript.exists() and "SNN_ECG_FULL_REPLAY_BOARD_PASS" not in transcript.read_text(
            encoding="utf-8-sig", errors="replace"
        ):
            fail(f"missing PASS marker in {rel(transcript)}", failures)


def check_board_replay_36(failures: list[str]) -> None:
    metrics = read_json("reports/final/final_metrics.json")
    board = metrics.get("board_replay_36", {})
    expected_scalars = {
        "status": "completed",
        "cases_requested": 36,
        "cases_completed": 36,
        "cases_final_mem_mismatch": 0,
        "pred_match_correct": 36,
        "pred_match_total": 36,
        "final_mem_match_correct": 36,
        "final_mem_match_total": 36,
        "classification_correct": 29,
        "classification_total": 36,
        "classification_accuracy_percent": 80.56,
    }
    for key, expected in expected_scalars.items():
        got = board.get(key)
        if got != expected:
            fail(f"board_replay_36.{key} expected {expected}, got {got}", failures)
    if board.get("validation_result") != "pass":
        fail("board_replay_36.validation_result must be pass because final_mem exact is 36/36", failures)

    summary = REPO / "reports" / "final" / "board_replay_36_batch_summary.md"
    comparison = REPO / "reports" / "final" / "board_replay_36_expected_vs_board.csv"
    manifest = REPO / "reports" / "final" / "board_replay_36_cases.csv"
    metadata = REPO / "reports" / "final" / "fulltop_xsim_final_test_36" / "locked_class_cases_fulltop_xsim_metadata.json"
    for path in [summary, comparison, manifest, metadata]:
        if not path.exists():
            fail(f"missing 36-case board replay artifact: {rel(path)}", failures)
    if metadata.exists():
        payload = json.loads(metadata.read_text(encoding="utf-8-sig"))
        if payload.get("sample_gap_cycles") != 2:
            fail(f"36-case board-equivalent XSim sample_gap_cycles expected 2, got {payload.get('sample_gap_cycles')}", failures)
    xsim_summary = REPO / "reports" / "final" / "fulltop_xsim_final_test_36" / "locked_class_cases_xsim_vs_board_summary.json"
    if xsim_summary.exists():
        payload = json.loads(xsim_summary.read_text(encoding="utf-8-sig"))
        for key in ["all_transport_ok", "all_final_pred_match", "all_final_mem_match"]:
            if payload.get(key) is not True:
                fail(f"36-case XSim-vs-board {key} must be true, got {payload.get(key)}", failures)
    if not comparison.exists():
        return

    with comparison.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 36:
        fail(f"36-case comparison row count expected 36, got {len(rows)}", failures)
    pred_matches = sum(1 for row in rows if row.get("pred_match") == "1")
    mem_matches = sum(1 for row in rows if row.get("final_mem_exact_match") == "1")
    label_matches = sum(1 for row in rows if row.get("board_correct_vs_label") == "1")
    if pred_matches != 36:
        fail(f"36-case final_pred matches expected 36, got {pred_matches}", failures)
    if mem_matches != 36:
        fail(f"36-case final_mem exact matches expected 36, got {mem_matches}", failures)
    if label_matches != 29:
        fail(f"36-case label matches expected 29, got {label_matches}", failures)
    for row in rows:
        transcript = row.get("transcript_path")
        parsed = row.get("parsed_json_path")
        if not transcript or not (REPO / transcript).exists():
            fail(f"missing 36-case transcript for {row.get('case_id')}", failures)
        if not parsed or not (REPO / parsed).exists():
            fail(f"missing 36-case parsed JSON for {row.get('case_id')}", failures)


def write_summary(failures: list[str]) -> None:
    out = REPO / "reports" / "final" / "final_repo_consistency_check.md"
    lines = [
        "# Final Repository Consistency Check",
        "",
        f"- Status: `{'PASS' if not failures else 'FAIL'}`",
        f"- Final model: `{FINAL_MODEL}`",
        "",
    ]
    if failures:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {item}" for item in failures)
    else:
        lines.extend(
            [
                "## 확인 항목",
                "",
                "- 최종 제출용 필수 파일이 존재한다.",
                "- 최종 보고서용 figure가 존재하며 보고서 삽입에 충분한 해상도를 가진다.",
                "- `docs/` 폴더에는 최종 5개 문서만 남아 있다.",
                "- 폐기 benchmark/candidate 문자열은 final-facing artifact에 남아 있지 않다.",
                "- Final-facing Markdown 문서의 local link와 image link가 해석된다.",
                "- Mermaid fence, heading blank line, Markdown table 구조가 기본 검사를 통과한다.",
                "- Locked strict record-wise metric은 source-of-truth 값과 일치한다.",
                "- 4개 class-wise board replay comparison CSV와 UART PASS marker가 존재한다.",
                "- 36-case board replay transcript/comparison evidence가 final_metrics와 일치한다.",
                "",
            ]
        )
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    check_required_figures(failures)
    check_doc_count(failures)
    check_forbidden_patterns(failures)
    check_markdown_links(failures)
    check_markdown_image_links(failures)
    check_mermaid_fences(failures)
    check_markdown_heading_spacing(failures)
    check_markdown_tables(failures)
    check_metrics(failures)
    check_board_replay(failures)
    check_board_replay_36(failures)
    write_summary(failures)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("final paper repo check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
