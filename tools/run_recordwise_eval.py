from __future__ import annotations

import argparse
import hashlib
from collections import Counter, defaultdict

from award_readiness_common import (
    CLASSES,
    REPORTS,
    all_chunks,
    confusion_rows,
    infer_many,
    md_table,
    metrics,
    pct,
    prediction_rows,
    write_csv,
    write_json,
)


def stable_bucket(record_id: str, seed: str) -> int:
    digest = hashlib.sha256(f"{seed}:{record_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def make_recordwise_splits(chunks: list[object], seed: str) -> dict[str, str]:
    by_class: dict[str, set[str]] = defaultdict(set)
    for chunk in chunks:
        by_class[chunk.class_label].add(chunk.record_id)
    assignment: dict[str, str] = {}
    for cls in CLASSES:
        records = sorted(by_class[cls], key=lambda rec: (stable_bucket(rec, seed), rec))
        n = len(records)
        if n <= 1:
            train_n, val_n = n, 0
        elif n == 2:
            train_n, val_n = 1, 0
        elif n == 3:
            train_n, val_n = 1, 1
        else:
            train_n = max(1, round(n * 0.50))
            val_n = max(1, round(n * 0.25))
            if train_n + val_n >= n:
                val_n = max(1, n - train_n - 1)
        for idx, record in enumerate(records):
            split = "train" if idx < train_n else "val" if idx < train_n + val_n else "test"
            assignment[f"{cls}:{record}"] = split
    return assignment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a fixed-model retrospective record-wise ECG chunk evaluation.")
    parser.add_argument("--seed", default="award_readiness_recordwise_v1")
    args = parser.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    chunks = all_chunks()
    assignment = make_recordwise_splits(chunks, args.seed)
    pred, detail = infer_many(chunks, mode="full")

    split_chunks: dict[str, list[object]] = {split: [] for split in ["train", "val", "test"]}
    for chunk in chunks:
        split_chunks[assignment[f"{chunk.class_label}:{chunk.record_id}"]].append(chunk)

    rows = []
    summary: dict[str, object] = {
        "note": "Retrospective fixed-model regrouping by source record. The model/rules were not retrained and were originally selected using existing chunk-level development data, so this is a leakage stress-test, not an unbiased record-wise training protocol.",
        "seed": args.seed,
        "splits": {},
    }
    for split, split_items in split_chunks.items():
        metric = metrics(split_items, pred)
        summary["splits"][split] = metric
        rows.extend({**row, "recordwise_split": split} for row in prediction_rows(split_items, pred, detail))
        if split == "test":
            write_csv(REPORTS / "recordwise_confusion_matrix.csv", confusion_rows(metric))

    write_csv(REPORTS / "recordwise_predictions.csv", rows)
    write_json(REPORTS / "recordwise_eval_summary.json", summary)

    split_rows = []
    for split, split_items in split_chunks.items():
        metric = summary["splits"][split]
        record_count = len({(chunk.class_label, chunk.record_id) for chunk in split_items})
        split_rows.append(
            [
                split,
                len(split_items),
                record_count,
                f"{metric['correct']}/{metric['total']}",
                pct(metric["accuracy"]),
                pct(metric["macro_f1"]),
                pct(metric["per_class"]["ARR"]["recall"]),
                pct(metric["per_class"]["AFF"]["recall"]),
            ]
        )

    class_rows = []
    for split, split_items in split_chunks.items():
        counts = Counter(chunk.class_label for chunk in split_items)
        recs = {cls: len({chunk.record_id for chunk in split_items if chunk.class_label == cls}) for cls in CLASSES}
        class_rows.append([split, *(f"{counts[cls]} chunks / {recs[cls]} recs" for cls in CLASSES)])

    md = [
        "# Record-Wise Fixed-Model Evaluation",
        "",
        "This is a retrospective source-record regrouping of the existing 136 chunks. It applies the already frozen Python golden rule set; it does not retrain or reselect thresholds.",
        "",
        md_table(
            ["split", "chunks", "class-record pairs", "correct", "accuracy", "macro-F1", "ARR recall", "AFF recall"],
            split_rows,
        ),
        "",
        "## Split Composition",
        "",
        md_table(["split", *CLASSES], class_rows),
        "",
        "## Limitation",
        "",
        "Because the final rule set was selected before this audit and the current repo contains chunk-level train/validation/test artifacts, this result is best treated as a record-wise leakage stress-test. A publishable strict record-wise claim would require freezing the protocol before model/rule search.",
    ]
    (REPORTS / "recordwise_eval_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "recordwise_eval_summary.md")


if __name__ == "__main__":
    main()
