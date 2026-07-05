from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from itertools import islice
from pathlib import Path
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    DATASET,
    REPO,
    REPORTS,
    RESULTS,
    SOURCE_MANIFEST,
    load_final_module,
    load_recordwise_manifest,
    load_snapshot_module,
    load_strict_split,
    md_table,
    pct,
    read_json,
    record_lists_from_split,
    sha256_json,
    write_json,
    write_log,
)


def exists(path: Path) -> str:
    return "present" if path.exists() else "missing"


def csv_rows(path: Path) -> int | str:
    if not path.exists():
        return "missing"
    with path.open(newline="", encoding="utf-8-sig") as f:
        return sum(1 for _ in csv.DictReader(f))


def write_repo_audit() -> Path:
    path = REPORTS / "repo_audit.md"
    rows = [
        ["Dataset root", exists(DATASET), DATASET.relative_to(REPO), "30-minute AFE+ADC .mem chunks"],
        ["Source manifest", f"{csv_rows(SOURCE_MANIFEST)} rows", SOURCE_MANIFEST.relative_to(REPO), "source record metadata"],
        ["Window dump train", f"{csv_rows(RESULTS / 'window_dump_train.csv')} rows", (RESULTS / "window_dump_train.csv").relative_to(REPO), "snapshot feature cache"],
        ["Window dump val", f"{csv_rows(RESULTS / 'window_dump_val.csv')} rows", (RESULTS / "window_dump_val.csv").relative_to(REPO), "snapshot feature cache"],
        ["Window dump test", f"{csv_rows(RESULTS / 'window_dump_test.csv')} rows", (RESULTS / "window_dump_test.csv").relative_to(REPO), "snapshot feature cache"],
        ["Python snapshot search", exists(REPO / "scripts" / "snapshot_c24_v2_search.py"), "scripts/snapshot_c24_v2_search.py", "candidate_grid/apply_candidate"],
        ["Python final membrane search", exists(REPO / "scripts" / "search_final_membrane_v2_snn.py"), "scripts/search_final_membrane_v2_snn.py", "candidate_grid/build_chunks/apply_candidate"],
        ["XSim runner", exists(REPO / "scripts" / "run_final_membrane_v2_xsim.py"), "scripts/run_final_membrane_v2_xsim.py", "existing frozen RTL comparison runner"],
        ["AXI/IP wrapper", exists(REPO / "rtl" / "axi" / "snn_ecg_axi_lite_stream_top.v"), "rtl/axi/snn_ecg_axi_lite_stream_top.v", "packaged accelerator wrapper"],
        ["IP-XACT component", exists(REPO / "ip_repo" / "snn_ecg_axi_accelerator" / "component.xml"), "ip_repo/snn_ecg_axi_accelerator/component.xml", "Vivado IP packaging evidence"],
        ["Board full replay transcript", exists(REPO / "reports" / "board_replay" / "transcripts" / "test_case0_nsr_uart_full_replay.txt"), "reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt", "previous board evidence, not strict search"],
    ]
    lines = [
        "# Strict Record-wise Repo Audit",
        "",
        "This audit records the local evidence used before constructing the strict source-record split and search flow.",
        "",
        md_table(["item", "checked result", "file/path", "note"], rows),
        "",
        "## Scope Notes",
        "",
        "- Existing `32/36 = 88.89%` is the earlier chunk-level test protocol.",
        "- Strict record-wise scripts reuse split-independent cached snapshot feature rows from `window_dump_*.csv` and reassign them by `source_record_id`.",
        "- A class-free `physical_record_id = <source_db>_<record_id>` audit is also performed to catch cross-class source-record leakage.",
        "- The strict search does not claim raw analog ECG acquisition, physical AFE PCB validation, or clinical validation.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def unique_values(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    values: dict[str, set[Any]] = defaultdict(set)
    for row in rows:
        for key, value in row.items():
            values[key].add(value)
    out: dict[str, list[Any]] = {}
    for key, vals in values.items():
        try:
            out[key] = sorted(vals)
        except TypeError:
            out[key] = sorted(vals, key=lambda item: str(item))
    return out


def write_search_spaces(final_preview: int = 20000) -> tuple[Path, Path, Path]:
    snap = load_snapshot_module()
    final = load_final_module()
    snapshot_candidates = list(snap.candidate_grid())
    final_candidates = list(islice(final.candidate_grid(), final_preview))
    snapshot_space = {
        "source": "scripts/snapshot_c24_v2_search.py:candidate_grid",
        "candidate_count": len(snapshot_candidates),
        "parameter_values": unique_values(snapshot_candidates),
        "test_used_for_selection": False,
    }
    final_space = {
        "source": "scripts/search_final_membrane_v2_snn.py:candidate_grid",
        "evaluated_prefix_default": final_preview,
        "parameter_values_observed_in_default_prefix": unique_values(final_candidates),
        "note": "The generator is large; strict workflow documents and searches the deterministic prefix unless --max-trials is increased before final test.",
        "test_used_for_selection": False,
    }
    snap_path = CONFIGS / "search_space_snapshot.json"
    final_path = CONFIGS / "search_space_final_membrane.json"
    write_json(snap_path, snapshot_space)
    write_json(final_path, final_space)
    inventory_path = REPORTS / "parameter_inventory.md"
    rows = []
    for key, vals in snapshot_space["parameter_values"].items():
        rows.append([f"snapshot.{key}", "candidate-dependent", compact(vals), "scripts/snapshot_c24_v2_search.py", "Python/expected; RTL if mirrored", "searched"])
    for key, vals in final_space["parameter_values_observed_in_default_prefix"].items():
        rows.append([f"final.{key}", "candidate-dependent", compact(vals), "scripts/search_final_membrane_v2_snn.py", "Python/expected; RTL if mirrored", "searched in deterministic prefix"])
    rows.extend(
        [
            ["feature extractor RTL thresholds", "current RTL value", "fixed", "rtl/core/*.v", "yes", "not globally re-searched in this pass"],
            ["ARR-focus random post-search", "existing frozen value", "fixed/TODO", "scripts/search_final_membrane_v2_arr_focus.py", "Python final golden", "not fully re-searched here"],
            ["WTA tie-break", "NSR->CHF->ARR->AFF order by first max", "fixed", "Python/RTL decision code", "yes", "kept deterministic"],
        ]
    )
    lines = [
        "# Strict Record-wise Parameter Inventory",
        "",
        "Parameters are split into the subset actually searched by this strict flow and fixed/TODO items that remain part of the broader design.",
        "",
        md_table(["parameter", "current value", "search range", "location", "affects RTL?", "notes"], rows),
    ]
    inventory_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return snap_path, final_path, inventory_path


def compact(values: list[Any], limit: int = 12) -> str:
    if len(values) <= limit:
        return "`" + json.dumps(values, ensure_ascii=False) + "`"
    head = json.dumps(values[:limit], ensure_ascii=False)
    return f"`{head[:-1]}, ...]` ({len(values)} values)"


def load_optional(path: Path) -> Any | None:
    return read_json(path) if path.exists() else None


def write_docs() -> list[Path]:
    outputs: list[Path] = []
    split_rows = load_strict_split() if (REPORTS / "strict_recordwise_split.csv").exists() else []
    manifest_rows = load_recordwise_manifest() if (REPORTS / "recordwise_manifest.csv").exists() else []
    record_lists = record_lists_from_split(split_rows) if split_rows else {s: [] for s in ["train", "val", "test"]}
    manifest_summary = []
    for cls in CLASSES:
        cls_rows = [r for r in manifest_rows if r["class_label"] == cls]
        manifest_summary.append([cls, len(cls_rows), len({r["source_record_id"] for r in cls_rows})])
    split_summary = []
    for cls in CLASSES:
        cls_rows = [r for r in split_rows if r["class_label"] == cls]
        by_split_records = {s: {r["source_record_id"] for r in cls_rows if r["split"] == s} for s in ["train", "val", "test"]}
        by_split_chunks = Counter(r["split"] for r in cls_rows)
        split_summary.append([cls, len(by_split_records["train"]), len(by_split_records["val"]), len(by_split_records["test"]), by_split_chunks["train"], by_split_chunks["val"], by_split_chunks["test"]])
    snapshot = load_optional(CONFIGS / "best_snapshot_params.json")
    final = load_optional(CONFIGS / "best_final_membrane_params.json")
    locked = load_optional(CONFIGS / "best_strict_recordwise_params_locked.json")
    test_metrics = load_optional(REPORTS / "final_test" / "strict_recordwise_test_metrics.json")
    global_doc = REPO / "docs" / "STRICT_RECORDWISE_GLOBAL_SEARCH_KR.md"
    lines = [
        "# Strict Record-wise Global Search Protocol",
        "",
        "## 1. 왜 strict record-wise가 필요한가",
        "",
        "기존 32/36 = 88.89% 결과는 chunk-level split 기준이다. 같은 원천 ECG record에서 잘린 여러 30분 chunk가 서로 다른 split에 섞이면, 모델이 unseen record 일반화가 아니라 record-specific 특성을 재사용할 수 있다. 이 문서는 `source_record_id` 단위로 train/validation/test를 다시 묶고, parameter search를 train/validation에만 제한한 절차를 정리한다.",
        "",
        "## 2. Manifest와 source_record_id",
        "",
        md_table(["class", "chunks", "unique_source_records"], manifest_summary),
        "",
        "`source_record_id`는 요구사항에 맞춰 `<class>_<source_db>_<record_id>` 형식으로 기록한다. 예: `ARR_mitdb_100`, `AFF_afdb_04043`, `NSR_nsrdb_16265`, `CHF_chfdb_chf01`. 추가로 class label을 제거한 `physical_record_id = <source_db>_<record_id>`를 두어 동일 물리 record가 class prefix 차이 때문에 split을 넘나들지 않는지 별도 audit한다.",
        "",
        "## 3. Strict split",
        "",
        md_table(["class", "train_records", "val_records", "test_records", "train_chunks", "val_chunks", "test_chunks"], split_summary),
        "",
        "본 strict record-wise protocol에서는 source_record_id 단위로 train/validation/test를 분리하며, 동일 source record에서 나온 chunk가 서로 다른 split에 들어가지 않도록 구성한다. Snapshot 및 final membrane parameter는 train/validation set에서만 선택하고, held-out test records는 최종 lock 이후 1회 평가에만 사용한다.",
        "",
        "## 4. Search space",
        "",
        "- Snapshot search: `configs/recordwise/search_space_snapshot.json`",
        "- Final membrane search: `configs/recordwise/search_space_final_membrane.json`",
        "- Parameter inventory: `reports/strict_recordwise/parameter_inventory.md`",
        "",
        "## 5. Test leakage 방지",
        "",
        "- Split lock: `reports/strict_recordwise/strict_recordwise_split_lock.json`",
        "- source_record_id 및 physical_record_id overlap check를 모두 수행한다.",
        "- Locked params: `configs/recordwise/best_strict_recordwise_params_locked.json`",
        "- Search scripts explicitly write `test_used_for_selection: false`.",
        "- Final test script records `test_evaluation_count`.",
        "",
        "## 6. 한계",
        "",
        "- Feature cache는 기존 window dump를 재사용한다. 원천 `.mem`부터 feature extraction을 새 split 이름으로 재실행한 것은 아니다.",
        "- RTL feature threshold 전체와 ARR-focus random post-search 전체 공간은 이번 strict pass에서 모두 재탐색하지 못했다. 해당 항목은 inventory에서 fixed/TODO로 분리했다.",
    ]
    if snapshot:
        lines.extend(["", "## 7. Snapshot selected result", "", f"- Trials: `{snapshot['trial_count']}`", f"- Best validation macro-F1: `{snapshot['val_metrics']['macro_f1']:.6f}`", f"- Best validation accuracy: `{snapshot['val_metrics']['accuracy']:.6f}`"])
    if final:
        lines.extend(["", "## 8. Final membrane selected result", "", f"- Trials: `{final['trial_count']}`", f"- Best validation macro-F1: `{final['val_metrics']['macro_f1']:.6f}`", f"- Best validation accuracy: `{final['val_metrics']['accuracy']:.6f}`"])
    if locked:
        lines.extend(["", "## 9. Locked params", "", "- Path: `configs/recordwise/best_strict_recordwise_params_locked.json`", f"- test_used_for_selection: `{locked['test_used_for_selection']}`"])
    global_doc.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    outputs.append(global_doc)

    final_doc = REPO / "docs" / "STRICT_RECORDWISE_FINAL_RESULT_KR.md"
    lines = [
        "# Strict Record-wise Final Result",
        "",
        "## 1. Protocol",
        "",
        "이 결과는 기존 chunk-level split 결과와 별도이다. `source_record_id` 단위로 train/validation/test를 분리하고, snapshot 및 final membrane parameter를 train/validation에서 lock한 뒤 held-out test records를 1회 평가한다.",
        "",
        "## 2. Split Summary",
        "",
        md_table(["class", "train_records", "val_records", "test_records", "train_chunks", "val_chunks", "test_chunks"], split_summary),
        "",
        "## 3. Test Source Records",
        "",
    ]
    lines.extend(f"- `{record}`" for record in record_lists["test"])
    if test_metrics:
        chunk = test_metrics["chunk_level"]
        rec = test_metrics["record_level_majority"]
        lines.extend(
            [
                "",
                "## 4. Final Test Metrics",
                "",
                md_table(
                    ["level", "accuracy", "macro-F1", "balanced accuracy", "total"],
                    [
                        ["chunk", pct(chunk["accuracy"]), pct(chunk["macro_f1"]), pct(chunk["balanced_accuracy"]), chunk["total"]],
                        ["record-majority", pct(rec["accuracy"]), pct(rec["macro_f1"]), pct(rec["balanced_accuracy"]), rec["total"]],
                        ["record-final_mem_sum", pct(test_metrics["record_level_final_mem_sum"]["accuracy"]), pct(test_metrics["record_level_final_mem_sum"]["macro_f1"]), pct(test_metrics["record_level_final_mem_sum"]["balanced_accuracy"]), test_metrics["record_level_final_mem_sum"]["total"]],
                    ],
                ),
                "",
                "## 5. Per-class Chunk Recall",
                "",
                md_table(["class", "recall", "precision", "f1", "support"], [[cls, pct(float(chunk["per_class"][cls]["recall"])), pct(float(chunk["per_class"][cls]["precision"])), pct(float(chunk["per_class"][cls]["f1"])), chunk["per_class"][cls]["support"]] for cls in CLASSES]),
                "",
                "## 6. Existing chunk-level result와의 관계",
                "",
                "기존 32/36 = 88.89%는 chunk-level split 기준 결과이고, 이 문서의 strict record-wise 결과는 unseen source record 평가이다. 두 수치는 protocol이 다르므로 같은 성능 지표처럼 직접 비교하지 않는다.",
                "",
                "## 7. Evidence Paths",
                "",
                "- Predictions: `reports/strict_recordwise/final_test/strict_recordwise_test_predictions.csv`",
                "- Confusion matrix: `reports/strict_recordwise/final_test/strict_recordwise_test_confusion_matrix.csv`",
                "- Metrics JSON: `reports/strict_recordwise/final_test/strict_recordwise_test_metrics.json`",
                "- Test evaluation count: `reports/strict_recordwise/final_test/test_evaluation_count.json`",
            ]
        )
    else:
        lines.extend(["", "## 4. Final Test Metrics", "", "Final test has not been executed yet. Do not claim strict record-wise test performance until `strict_recordwise_test_metrics.json` exists."])
    lines.extend(
        [
            "",
            "## 8. Limits",
            "",
            "- 본 결과는 model-based digital verification이며 clinical validation이 아니다.",
            "- source ECG는 already digitized record이다.",
            "- Strict parameter export는 생성했지만 RTL에 자동 연결되지는 않는다.",
        ]
    )
    final_doc.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    outputs.append(final_doc)
    return outputs


def upsert_section(path: Path, marker: str, title: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    begin = f"<!-- {marker}:BEGIN -->"
    end = f"<!-- {marker}:END -->"
    block = f"{begin}\n\n## {title}\n\n{body.rstrip()}\n\n{end}"
    if begin in text and end in text:
        before, rest = text.split(begin, 1)
        _, after = rest.split(end, 1)
        text = before.rstrip() + "\n\n" + block + after
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def update_readme_and_final_report() -> list[Path]:
    metrics = load_optional(REPORTS / "final_test" / "strict_recordwise_test_metrics.json")
    if metrics:
        chunk = metrics["chunk_level"]
        rec = metrics["record_level_majority"]
        result_sentence = (
            f"Strict record-wise held-out test 결과는 chunk-level accuracy {pct(chunk['accuracy'])}, "
            f"chunk macro-F1 {pct(chunk['macro_f1'])}, record-majority accuracy {pct(rec['accuracy'])}, "
            f"record-majority macro-F1 {pct(rec['macro_f1'])}이다."
        )
    else:
        result_sentence = "Strict record-wise final test는 아직 실행 전이므로 성능 수치를 주장하지 않는다."
    readme_body = "\n".join(
        [
            "기존 `32/36 = 88.89%` 결과는 chunk-level split 기준이다. 제출 직전 검증에서는 같은 원천 ECG record의 chunk가 서로 다른 split에 섞이지 않도록 `source_record_id` 기준 strict split을 별도로 구성했다.",
            "",
            result_sentence,
            "",
            "- Protocol: [docs/STRICT_RECORDWISE_GLOBAL_SEARCH_KR.md](docs/STRICT_RECORDWISE_GLOBAL_SEARCH_KR.md)",
            "- Final result: [docs/STRICT_RECORDWISE_FINAL_RESULT_KR.md](docs/STRICT_RECORDWISE_FINAL_RESULT_KR.md)",
            "- Integrity check: [reports/strict_recordwise/integrity_check.md](reports/strict_recordwise/integrity_check.md)",
        ]
    )
    final_body = "\n".join(
        [
            "기존 chunk-level split 결과와 별도로, source record leakage를 줄이기 위해 `source_record_id` 단위 strict record-wise split을 추가 구성했다. Snapshot parameter와 final membrane parameter는 train/validation records에서만 search하고, selected params를 lock한 뒤 held-out test records를 1회 평가한다.",
            "",
            result_sentence,
            "",
            "이 결과는 기존 88.89% chunk-level result와 protocol이 다르다. 따라서 strict record-wise 결과는 unseen source-record stress test로 해석하고, chunk-level test accuracy처럼 직접 비교하지 않는다.",
        ]
    )
    upsert_section(REPO / "README.md", "STRICT_RECORDWISE", "Strict Record-wise Validation", readme_body)
    upsert_section(REPO / "FINAL_REPORT_KR.md", "STRICT_RECORDWISE", "Strict Record-wise 탐색 및 최종 평가", final_body)
    return [REPO / "README.md", REPO / "FINAL_REPORT_KR.md"]


def write_integrity_check() -> Path:
    path = REPORTS / "integrity_check.md"
    checks: list[tuple[str, str, str]] = []
    split_rows = load_strict_split()
    split_json = load_optional(CONFIGS / "strict_recordwise_split_seed2026.json") or {}
    seen = defaultdict(set)
    for row in split_rows:
        seen[row["source_record_id"]].add(row["split"])
    overlaps = {rec: splits for rec, splits in seen.items() if len(splits) > 1}
    checks.append(("train/val/test source_record_id overlap", "PASS" if not overlaps else "FAIL", "empty intersections" if not overlaps else str(overlaps)))
    physical_seen = defaultdict(set)
    for row in split_rows:
        physical_seen[row.get("physical_record_id", "")].add(row["split"])
    physical_overlaps = {rec: splits for rec, splits in physical_seen.items() if rec and len(splits) > 1}
    checks.append(("train/val/test physical_record_id overlap", "PASS" if not physical_overlaps else "FAIL", "empty intersections" if not physical_overlaps else str(physical_overlaps)))
    locked_path = CONFIGS / "best_strict_recordwise_params_locked.json"
    locked = read_json(locked_path) if locked_path.exists() else {}
    checks.append(("locked params exist", "PASS" if locked_path.exists() else "FAIL", str(locked_path.relative_to(REPO))))
    checks.append(("test_used_for_selection", "PASS" if locked.get("test_used_for_selection") is False else "FAIL", str(locked.get("test_used_for_selection"))))
    checks.append(("split hash embedded in lock", "PASS" if locked.get("split_hash") == split_json.get("split_hash") else "FAIL", str(locked.get("split_hash"))))
    record_lists = record_lists_from_split(split_rows)
    hash_checks = {
        "train_record_list_hash": sha256_json(record_lists["train"]),
        "val_record_list_hash": sha256_json(record_lists["val"]),
        "test_record_list_hash": sha256_json(record_lists["test"]),
    }
    for key, expected in hash_checks.items():
        checks.append((key, "PASS" if locked.get(key) == expected else "FAIL", expected))
    count_path = REPORTS / "final_test" / "test_evaluation_count.json"
    count = read_json(count_path) if count_path.exists() else {}
    checks.append(("test evaluation count", "PASS" if count.get("test_evaluation_count") == 1 else "WARN", str(count.get("test_evaluation_count", "missing"))))
    metrics_path = REPORTS / "final_test" / "strict_recordwise_test_metrics.json"
    checks.append(("final metrics json exists", "PASS" if metrics_path.exists() else "FAIL", str(metrics_path.relative_to(REPO))))
    if metrics_path.exists():
        metrics = read_json(metrics_path)
        pred_path = REPORTS / "final_test" / "strict_recordwise_test_predictions.csv"
        confusion_path = REPORTS / "final_test" / "strict_recordwise_test_confusion_matrix.csv"
        pred_count = csv_rows(pred_path)
        checks.append(("prediction row count matches chunk total", "PASS" if pred_count == metrics["chunk_level"]["total"] else "FAIL", f"{pred_count} vs {metrics['chunk_level']['total']}"))
        if confusion_path.exists():
            with confusion_path.open(newline="", encoding="utf-8-sig") as f:
                conf_total = 0
                for row in csv.DictReader(f):
                    conf_total += sum(int(row.get(cls, 0)) for cls in CLASSES)
            checks.append(("confusion total matches chunk total", "PASS" if conf_total == metrics["chunk_level"]["total"] else "FAIL", f"{conf_total} vs {metrics['chunk_level']['total']}"))
        checks.append(("metrics test_used_for_selection", "PASS" if metrics.get("test_used_for_selection") is False else "FAIL", str(metrics.get("test_used_for_selection"))))
    for label, file_name in [
        ("snapshot search test flag", "best_snapshot_params.json"),
        ("final search test flag", "best_final_membrane_params.json"),
    ]:
        payload = load_optional(CONFIGS / file_name) or {}
        checks.append((label, "PASS" if payload.get("test_used_for_selection") is False else "FAIL", str(payload.get("test_used_for_selection"))))
    docs = [REPO / "docs" / "STRICT_RECORDWISE_GLOBAL_SEARCH_KR.md", REPO / "docs" / "STRICT_RECORDWISE_FINAL_RESULT_KR.md", REPO / "README.md", REPO / "FINAL_REPORT_KR.md"]
    checks.append(("strict docs updated", "PASS" if all(doc.exists() for doc in docs) else "FAIL", ", ".join(str(doc.relative_to(REPO)) for doc in docs if doc.exists())))
    lines = [
        "# Strict Record-wise Integrity Check",
        "",
        md_table(["check", "status", "evidence"], checks),
        "",
        "## Notes",
        "",
        "- A WARN on test evaluation count means the test script was run more than once or not yet run; it should be explained before submission.",
        "- Integrity check verifies file/protocol consistency. It does not prove clinical validity.",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write strict record-wise audit/config/docs/integrity reports.")
    parser.add_argument("--final-preview", type=int, default=20000)
    parser.add_argument("--skip-integrity", action="store_true")
    args = parser.parse_args()
    outputs = [write_repo_audit()]
    outputs.extend(write_search_spaces(args.final_preview))
    outputs.extend(write_docs())
    outputs.extend(update_readme_and_final_report())
    if not args.skip_integrity:
        outputs.append(write_integrity_check())
    write_log("write_strict_recordwise_reports", sys.argv, outputs, {"final_preview": args.final_preview})
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
