from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from award_readiness_common import CLASSES, DATASET, MANIFEST, REPORTS, SPLITS, md_table, read_csv, split_chunks, write_csv


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    by_split = split_chunks(SPLITS)
    chunks = [chunk for split in SPLITS for chunk in by_split[split]]
    manifest_rows = read_csv(MANIFEST) if MANIFEST.exists() else []

    class_records: dict[str, set[str]] = {cls: set() for cls in CLASSES}
    split_records: dict[tuple[str, str], set[str]] = defaultdict(set)
    chunk_counts = Counter()
    for chunk in chunks:
        class_records[chunk.class_label].add(chunk.record_id)
        split_records[(chunk.class_label, chunk.split)].add(chunk.record_id)
        chunk_counts[chunk.class_label] += 1

    rows = []
    leakage_detail = []
    for cls in CLASSES:
        overlap = set()
        for record in class_records[cls]:
            present = [split for split in SPLITS if record in split_records[(cls, split)]]
            if len(present) > 1:
                overlap.add(record)
                leakage_detail.append(
                    {
                        "class": cls,
                        "record_id": record,
                        "current_splits": "|".join(present),
                        "split_count": len(present),
                    }
                )
        rows.append(
            {
                "class": cls,
                "chunks": chunk_counts[cls],
                "unique_records": len(class_records[cls]),
                "train_records": len(split_records[(cls, "train")]),
                "val_records": len(split_records[(cls, "val")]),
                "test_records": len(split_records[(cls, "test")]),
                "overlapping_records": "|".join(sorted(overlap)),
                "overlapping_record_count": len(overlap),
            }
        )

    manifest_overlap = []
    if manifest_rows:
        by_record = defaultdict(lambda: {"current": set(), "original": set(), "class": ""})
        for row in manifest_rows:
            key = (row.get("class_label", ""), row.get("record_id", ""))
            by_record[key]["class"] = row.get("class_label", "")
            by_record[key]["current"].add(row.get("split", ""))
            by_record[key]["original"].add(row.get("original_split", ""))
        for (cls, record), info in sorted(by_record.items()):
            current = sorted(s for s in info["current"] if s)
            original = sorted(s for s in info["original"] if s)
            if len(current) > 1 or len(original) > 1 or current != original:
                manifest_overlap.append(
                    {
                        "class": cls,
                        "record_id": record,
                        "manifest_current_splits": "|".join(current),
                        "manifest_original_splits": "|".join(original),
                        "note": "record-level split differs or spans multiple split labels",
                    }
                )

    write_csv(REPORTS / "dataset_split_audit.csv", rows)
    write_csv(REPORTS / "dataset_split_leakage_detail.csv", leakage_detail)
    write_csv(REPORTS / "dataset_manifest_split_trace.csv", manifest_overlap)

    total_chunks = sum(chunk_counts.values())
    total_records = len({(chunk.class_label, chunk.record_id) for chunk in chunks})
    leaked_records = sum(int(row["overlapping_record_count"]) for row in rows)
    md = [
        "# Dataset Split Audit",
        "",
        "This audit uses the current 30-minute dataset and the fixed Python chunk loader.",
        "",
        f"- Dataset root: `{DATASET}`",
        f"- Manifest: `{MANIFEST}`",
        f"- Chunks inspected: {total_chunks}",
        f"- Class-record pairs inspected: {total_records}",
        f"- Class-record pairs spanning multiple current splits: {leaked_records}",
        "",
        md_table(
            [
                "class",
                "chunks",
                "unique_records",
                "train_records",
                "val_records",
                "test_records",
                "overlap_count",
            ],
            [
                [
                    row["class"],
                    row["chunks"],
                    row["unique_records"],
                    row["train_records"],
                    row["val_records"],
                    row["test_records"],
                    row["overlapping_record_count"],
                ]
                for row in rows
            ],
        ),
        "",
        "## Interpretation",
        "",
        "The earlier chunk-level organization is not used as the final model evidence. Final reporting uses the locked strict record-wise protocol only.",
        "",
        "Detailed record overlap tables:",
        "",
        "- `reports/award_readiness/dataset_split_leakage_detail.csv`",
        "- `reports/award_readiness/dataset_manifest_split_trace.csv`",
    ]
    (REPORTS / "dataset_split_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "dataset_split_audit.md")


if __name__ == "__main__":
    main()
