from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    SPLITS,
    load_strict_split,
    md_table,
    read_json,
    record_lists_from_split,
    sha256_json,
    split_json_path,
    write_json,
    write_log,
)


def final_test_lock_paths() -> tuple[Path, Path]:
    return (
        CONFIGS / "final_test_records_locked.json",
        REPORTS / "final_test_records_lock_summary.md",
    )


def build_lock(seed: int) -> dict[str, Any]:
    split_payload = read_json(split_json_path(seed))
    split_rows = load_strict_split()
    record_lists = record_lists_from_split(split_rows)
    test_rows = [row for row in split_rows if row["split"] == "test"]
    train_val_rows = [row for row in split_rows if row["split"] in {"train", "val"}]
    lock_payload = {
        "locked": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "split_hash": split_payload["split_hash"],
        "rule": "final_test records are locked before structure search and parameter search; do not use final_test chunks, labels, predictions, or features before locked-parameter evaluation.",
        "allowed_before_final_test": ["train", "val"],
        "forbidden_before_lock": ["test"],
        "test_used_for_structure_selection": False,
        "test_used_for_parameter_search": False,
        "test_used_for_chatgpt_context": False,
        "test_record_list_hash": sha256_json(record_lists["test"]),
        "train_record_list_hash": sha256_json(record_lists["train"]),
        "val_record_list_hash": sha256_json(record_lists["val"]),
        "train_val_chunk_file_hash": sha256_json(sorted(row["chunk_file"] for row in train_val_rows)),
        "test_chunk_file_hash": sha256_json(sorted(row["chunk_file"] for row in test_rows)),
        "test_source_records": record_lists["test"],
        "test_physical_records": sorted({row["physical_record_id"] for row in test_rows}),
        "test_record_count_by_class": {cls: len({row["source_record_id"] for row in test_rows if row["class_label"] == cls}) for cls in CLASSES},
        "test_chunk_count_by_class": dict(Counter(row["class_label"] for row in test_rows)),
    }
    lock_payload["lock_hash"] = sha256_json(
        {
            "seed": lock_payload["seed"],
            "split_hash": lock_payload["split_hash"],
            "test_record_list_hash": lock_payload["test_record_list_hash"],
            "test_chunk_file_hash": lock_payload["test_chunk_file_hash"],
            "rule": lock_payload["rule"],
        }
    )
    return lock_payload


def write_summary(path: Path, payload: dict[str, Any]) -> None:
    rows = [
        [cls, payload["test_record_count_by_class"].get(cls, 0), payload["test_chunk_count_by_class"].get(cls, 0)]
        for cls in CLASSES
    ]
    lines = [
        "# Final Test Records Lock",
        "",
        f"- Seed: `{payload['seed']}`",
        f"- Split hash: `{payload['split_hash']}`",
        f"- Final-test record-list hash: `{payload['test_record_list_hash']}`",
        f"- Final-test chunk-file hash: `{payload['test_chunk_file_hash']}`",
        f"- Lock hash: `{payload['lock_hash']}`",
        "- Test used for structure selection: `false`",
        "- Test used for parameter search: `false`",
        "- Test used for ChatGPT context: `false`",
        "",
        md_table(["class", "test_records", "test_chunks"], rows),
        "",
        "The readable final_test record list is sealed in `configs/recordwise_resplit_seed20260808/final_test_records_locked.json` for reproducibility. It must not be sent to ChatGPT or used by train/validation search.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lock strict final_test records before any final membrane search.")
    parser.add_argument("--seed", type=int, default=20260808)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    lock_path, summary_path = final_test_lock_paths()
    if lock_path.exists() and not args.force:
        raise SystemExit(f"final_test lock exists: {lock_path}. Use --force only before structure/parameter search starts.")
    payload = build_lock(args.seed)
    write_json(lock_path, payload)
    write_summary(summary_path, payload)
    write_log("lock_final_test_records", sys.argv, [lock_path, summary_path], {"lock_hash": payload["lock_hash"]})
    print(lock_path)
    print(summary_path)


if __name__ == "__main__":
    main()
