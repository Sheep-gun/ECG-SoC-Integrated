from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    SPLITS,
    class_counts,
    load_recordwise_manifest,
    md_table,
    record_lists_from_split,
    sha256_json,
    split_csv_path,
    split_json_path,
    stable_bucket,
    write_csv,
    write_json,
    write_log,
)


def assign_class_records(records: list[str], seed: int | str) -> dict[str, str]:
    ordered = sorted(records, key=lambda rec: (stable_bucket(rec, seed), rec))
    n = len(ordered)
    if n <= 1:
        counts = {"train": n, "val": 0, "test": 0}
    elif n == 2:
        counts = {"train": 1, "val": 0, "test": 1}
    elif n <= 4:
        counts = {"train": n - 2, "val": 1, "test": 1}
    else:
        test_n = max(1, round(n * 0.18))
        val_n = max(1, round(n * 0.18))
        train_n = n - val_n - test_n
        if train_n < 1:
            train_n = 1
            if val_n > test_n:
                val_n -= 1
            else:
                test_n -= 1
        counts = {"train": train_n, "val": val_n, "test": test_n}
    assignment: dict[str, str] = {}
    idx = 0
    for split in SPLITS:
        for record in ordered[idx : idx + counts[split]]:
            assignment[record] = split
        idx += counts[split]
    return assignment


def assign_class_records_by_chunk_target(
    record_weights: dict[str, int],
    target_chunks: dict[str, int],
    seed: int | str,
) -> dict[str, str]:
    """Assign whole records to splits while exactly matching split chunk counts.

    This keeps the record-wise no-leakage property but restores the class-balanced
    chunk counts of the original 30-minute dataset split.
    """

    total_weight = sum(record_weights.values())
    total_target = sum(target_chunks.values())
    if total_weight != total_target:
        raise ValueError(f"chunk target total mismatch: records={total_weight}, target={total_target}")

    ordered = sorted(record_weights, key=lambda rec: (-record_weights[rec], stable_bucket(rec, seed), rec))
    suffix = [0] * (len(ordered) + 1)
    for idx in range(len(ordered) - 1, -1, -1):
        suffix[idx] = suffix[idx + 1] + record_weights[ordered[idx]]

    target_tuple = tuple(int(target_chunks[split]) for split in SPLITS)
    memo: set[tuple[int, tuple[int, int, int]]] = set()

    def rec(idx: int, remaining: tuple[int, int, int]) -> dict[str, str] | None:
        state = (idx, remaining)
        if state in memo:
            return None
        if idx == len(ordered):
            return {} if all(value == 0 for value in remaining) else None
        if sum(remaining) != suffix[idx]:
            memo.add(state)
            return None
        record = ordered[idx]
        weight = record_weights[record]
        for split_idx, split in sorted(enumerate(SPLITS), key=lambda item: (-remaining[item[0]], item[1])):
            if remaining[split_idx] < weight:
                continue
            next_remaining = list(remaining)
            next_remaining[split_idx] -= weight
            tail = rec(idx + 1, tuple(next_remaining))  # type: ignore[arg-type]
            if tail is not None:
                tail[record] = split
                return tail
        memo.add(state)
        return None

    assignment = rec(0, target_tuple)
    if assignment is None:
        raise RuntimeError(f"cannot build exact chunk-balanced record assignment for targets={target_chunks}")
    return assignment


def assert_no_overlap(rows: list[dict[str, Any]], key: str = "source_record_id") -> None:
    seen: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        seen[str(row[key])].add(str(row["split"]))
    overlaps = {record: splits for record, splits in seen.items() if len(splits) > 1}
    if overlaps:
        first = next(iter(overlaps.items()))
        raise RuntimeError(f"{key} overlap detected: {first[0]} -> {sorted(first[1])}")


def target_chunk_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    targets: dict[str, Counter[str]] = {cls: Counter() for cls in CLASSES}
    for row in rows:
        current = row.get("current_chunk_split", "")
        if current not in SPLITS:
            raise RuntimeError(f"row has invalid current_chunk_split={current!r}: {row.get('chunk_id')}")
        targets[row["class_label"]][current] += 1
    return {cls: {split: targets[cls][split] for split in SPLITS} for cls in CLASSES}


def build_split(seed: int | str, balance_chunks: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = load_recordwise_manifest()
    by_class: dict[str, set[str]] = {cls: set() for cls in CLASSES}
    weights_by_class: dict[str, Counter[str]] = {cls: Counter() for cls in CLASSES}
    for row in rows:
        by_class[row["class_label"]].add(row["source_record_id"])
        weights_by_class[row["class_label"]][row["source_record_id"]] += 1
    targets = target_chunk_counts(rows)
    record_assignment: dict[str, str] = {}
    for cls in CLASSES:
        if balance_chunks:
            record_assignment.update(assign_class_records_by_chunk_target(dict(weights_by_class[cls]), targets[cls], seed))
        else:
            record_assignment.update(assign_class_records(sorted(by_class[cls]), seed))
    out = []
    for row in rows:
        item = dict(row)
        item["split"] = record_assignment[item["source_record_id"]]
        out.append(item)
    assert_no_overlap(out, "source_record_id")
    if out and "physical_record_id" in out[0]:
        assert_no_overlap(out, "physical_record_id")
    metadata = {
        "balance_chunks": balance_chunks,
        "target_chunk_counts": targets if balance_chunks else None,
    }
    return out, metadata


def write_summary(rows: list[dict[str, Any]], seed: int | str, split_hash: str) -> Path:
    summary = REPORTS / "strict_recordwise_split_summary.md"
    table_rows = []
    for cls in CLASSES:
        cls_rows = [r for r in rows if r["class_label"] == cls]
        recs_by_split = {split: sorted({r["source_record_id"] for r in cls_rows if r["split"] == split}) for split in SPLITS}
        chunks_by_split = Counter(r["split"] for r in cls_rows)
        table_rows.append(
            [
                cls,
                len(recs_by_split["train"]),
                len(recs_by_split["val"]),
                len(recs_by_split["test"]),
                chunks_by_split["train"],
                chunks_by_split["val"],
                chunks_by_split["test"],
            ]
        )
    lines = [
        "# Strict Record-wise Split Summary",
        "",
        f"- Seed: `{seed}`",
        f"- Split hash: `{split_hash}`",
        "- source_record_id overlap check: `PASS`",
        "- physical_record_id overlap check: `PASS`",
        "- Final-test record list: locked separately by `tools/recordwise/lock_final_test_records.py`",
        "",
        md_table(
            [
                "class",
                "train_records",
                "val_records",
                "test_records",
                "train_chunks",
                "val_chunks",
                "test_chunks",
            ],
            table_rows,
        ),
    ]
    summary.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a leakage-free source-record split.")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--balance-chunks", action="store_true", help="Assign whole records while matching the original per-class split chunk counts.")
    parser.add_argument("--allow-existing-lock", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    lock_path = REPORTS / "strict_recordwise_split_lock.json"
    if lock_path.exists() and not (args.allow_existing_lock or args.force):
        raise SystemExit(f"split lock exists: {lock_path}. Use --allow-existing-lock to reuse or --force to rewrite.")

    rows, metadata = build_split(args.seed, balance_chunks=args.balance_chunks)
    record_lists = record_lists_from_split(rows)
    split_payload = {
        "seed": args.seed,
        "policy": "source_record_id grouped split; exact original per-class train/val/test chunk counts" if args.balance_chunks else "source_record_id grouped split; <=4 records/class uses train=n-2,val=1,test=1; otherwise approximate 64/18/18 by record",
        "balance_chunks": args.balance_chunks,
        "target_chunk_counts": metadata["target_chunk_counts"],
        "record_lists": record_lists,
        "test_records_readable_by_search": True,
        "test_records_used_for_search": False,
        "physical_record_overlap_checked": True,
    }
    split_hash = sha256_json(split_payload)
    split_payload["split_hash"] = split_hash
    split_payload["record_list_hashes"] = {split: sha256_json(record_lists[split]) for split in SPLITS}
    split_payload["class_chunk_counts"] = {cls: dict(class_counts([r for r in rows if r["class_label"] == cls], "split")[cls]) for cls in CLASSES}

    CONFIGS.mkdir(parents=True, exist_ok=True)
    out_json = split_json_path(args.seed)
    out_csv = split_csv_path()
    write_json(out_json, split_payload)
    write_csv(out_csv, rows)
    summary = write_summary(rows, args.seed, split_hash)
    lock = {
        "locked": True,
        "seed": args.seed,
        "split_hash": split_hash,
        "split_json": str(out_json),
        "split_csv": str(out_csv),
        "balance_chunks": args.balance_chunks,
        "rule": "Do not change this split after parameter search starts.",
    }
    if not lock_path.exists() or args.force:
        write_json(lock_path, lock)
    write_log("make_strict_recordwise_split", sys.argv, [out_json, out_csv, summary, lock_path], lock)
    print(out_json)
    print(out_csv)
    print(summary)


if __name__ == "__main__":
    main()
