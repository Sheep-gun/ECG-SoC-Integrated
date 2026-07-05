from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from recordwise_common import (
    CLASSES,
    DATASET,
    REPO,
    REPORTS,
    SOURCE_MANIFEST,
    CLASS_TO_ID,
    make_source_record_id,
    md_table,
    norm_rel,
    read_csv,
    source_db_for,
    write_csv,
    write_log,
)


FIELDS = [
    "strict_case_id",
    "chunk_id",
    "class_label",
    "class_id",
    "source_database",
    "source_record_id",
    "physical_record_id",
    "record_id",
    "source_file_path",
    "mem_path",
    "chunk_index",
    "start_sec",
    "duration_sec",
    "sample_count",
    "sample_rate",
    "split",
    "current_chunk_split",
    "original_split",
    "uncertain_source_record",
    "notes",
    "chunk_file",
]


def build_rows() -> list[dict[str, Any]]:
    if not SOURCE_MANIFEST.exists():
        raise FileNotFoundError(SOURCE_MANIFEST)
    source_rows = read_csv(SOURCE_MANIFEST)
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(source_rows):
        cls = row.get("class_label", "").strip()
        record_id = row.get("record_id", "").strip()
        source_db = source_db_for(row)
        source_record_id = make_source_record_id(cls, source_db, record_id) if cls and record_id else ""
        physical_record_id = f"{source_db}_{record_id}" if source_db and record_id else ""
        chunk_file = norm_rel(row.get("chunk_file", ""))
        mem_path = DATASET / chunk_file
        uncertain = int(not cls or not record_id or not source_db or not mem_path.exists())
        notes = []
        if not mem_path.exists():
            notes.append("mem_path_missing")
        if row.get("source_notes"):
            notes.append(row["source_notes"])
        out.append(
            {
                "strict_case_id": idx,
                "chunk_id": f"{cls}_{source_db}_{record_id}_w{row.get('chunk_id', '')}",
                "class_label": cls,
                "class_id": CLASS_TO_ID.get(cls, -1),
                "source_database": source_db,
                "source_record_id": source_record_id,
                "physical_record_id": physical_record_id,
                "record_id": record_id,
                "source_file_path": row.get("source_mem_file", ""),
                "mem_path": str(mem_path.relative_to(REPO)).replace("\\", "/") if mem_path.exists() else str(mem_path),
                "chunk_index": row.get("chunk_id", ""),
                "start_sec": row.get("start_sec", ""),
                "duration_sec": row.get("window_sec", ""),
                "sample_count": row.get("window_samples", ""),
                "sample_rate": row.get("sample_rate", ""),
                "split": "",
                "current_chunk_split": row.get("split", ""),
                "original_split": row.get("original_split", ""),
                "uncertain_source_record": uncertain,
                "notes": ";".join(notes),
                "chunk_file": chunk_file,
            }
        )
    out.sort(key=lambda r: (r["class_label"], r["source_record_id"], int(r["strict_case_id"])))
    for idx, row in enumerate(out):
        row["strict_case_id"] = idx
    return out


def write_summary(rows: list[dict[str, Any]]) -> Path:
    summary_path = REPORTS / "recordwise_manifest_summary.md"
    class_rows = []
    by_class_records: dict[str, set[str]] = defaultdict(set)
    by_class_physical_records: dict[str, set[str]] = defaultdict(set)
    by_class_chunks = Counter()
    uncertain_rows = [row for row in rows if str(row["uncertain_source_record"]) not in ("0", "False", "false")]
    for row in rows:
        cls = str(row["class_label"])
        by_class_chunks[cls] += 1
        by_class_records[cls].add(str(row["source_record_id"]))
        by_class_physical_records[cls].add(str(row["physical_record_id"]))
    for cls in CLASSES:
        class_rows.append([cls, by_class_chunks[cls], len(by_class_records[cls])])

    lines = [
        "# Strict Record-wise Manifest Summary",
        "",
        f"- Source manifest: `{SOURCE_MANIFEST.relative_to(REPO)}`",
        f"- Dataset root: `{DATASET.relative_to(REPO)}`",
        f"- Chunks: `{len(rows)}`",
        f"- Uncertain source rows: `{len(uncertain_rows)}`",
        "",
        md_table(["class", "chunks", "unique_source_records"], class_rows),
        "",
        "Class-prefixed `source_record_id` is retained for reporting. The companion `physical_record_id` removes the class label and is used for an additional leakage audit.",
        "",
        "## Source Record IDs",
        "",
    ]
    for cls in CLASSES:
        recs = sorted(by_class_records[cls])
        lines.extend([f"### {cls}", "", ", ".join(f"`{rec}`" for rec in recs), ""])
    lines.extend(["## Physical Record IDs", ""])
    for cls in CLASSES:
        recs = sorted(by_class_physical_records[cls])
        lines.extend([f"### {cls}", "", ", ".join(f"`{rec}`" for rec in recs), ""])
    if uncertain_rows:
        lines.extend(
            [
                "## 확인 필요",
                "",
                "아래 row는 source record 추정 또는 mem path 확인이 불완전하다.",
                "",
                md_table(
                    ["strict_case_id", "class", "record_id", "chunk_file", "notes"],
                    [
                        [r["strict_case_id"], r["class_label"], r["record_id"], r["chunk_file"], r["notes"]]
                        for r in uncertain_rows[:50]
                    ],
                ),
            ]
        )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build source-record-aware 30-minute ECG chunk manifest.")
    parser.add_argument("--output", default=str(REPORTS / "recordwise_manifest.csv"))
    args = parser.parse_args()

    rows = build_rows()
    out_path = Path(args.output)
    write_csv(out_path, rows, FIELDS)
    summary_path = write_summary(rows)
    write_log(
        "build_recordwise_manifest",
        sys.argv,
        [out_path, summary_path],
        {"chunks": len(rows), "unique_source_records": len({r["source_record_id"] for r in rows})},
    )
    print(out_path)
    print(summary_path)


if __name__ == "__main__":
    main()
