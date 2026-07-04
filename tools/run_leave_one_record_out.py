from __future__ import annotations

from collections import Counter, defaultdict

from award_readiness_common import CLASSES, REPORTS, all_chunks, chunk_key, infer_many, md_table, metrics, pct, write_csv, write_json


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    chunks = all_chunks()
    pred, detail = infer_many(chunks, mode="full")
    by_record: dict[tuple[str, str], list[object]] = defaultdict(list)
    for chunk in chunks:
        by_record[(chunk.class_label, chunk.record_id)].append(chunk)

    rows = []
    summary_rows = []
    for (cls, record_id), items in sorted(by_record.items()):
        m = metrics(items, pred)
        dist = Counter(pred[chunk_key(item)] for item in items)
        row = {
            "class": cls,
            "record_id": record_id,
            "chunks": len(items),
            "correct": m["correct"],
            "accuracy": m["accuracy"],
            "pred_NSR": dist[0],
            "pred_CHF": dist[1],
            "pred_ARR": dist[2],
            "pred_AFF": dist[3],
        }
        rows.append(row)
        summary_rows.append(
            [
                cls,
                record_id,
                len(items),
                f"{m['correct']}/{m['total']}",
                pct(m["accuracy"]),
                "/".join(str(dist[idx]) for idx in range(4)),
            ]
        )

    class_summary = []
    for cls in CLASSES:
        items = [chunk for chunk in chunks if chunk.class_label == cls]
        m = metrics(items, pred)
        class_summary.append(
            {
                "class": cls,
                "records": len({chunk.record_id for chunk in items}),
                "chunks": len(items),
                "correct": m["correct"],
                "total": m["total"],
                "accuracy": m["accuracy"],
                "recall": m["per_class"][cls]["recall"],
            }
        )

    write_csv(REPORTS / "loro_predictions.csv", rows)
    write_json(
        REPORTS / "loro_eval_summary.json",
        {
            "note": "Leave-one-record-out reporting for a fixed already-selected rule set. No retraining is performed per held-out record.",
            "class_summary": class_summary,
            "records": rows,
        },
    )

    md = [
        "# Leave-One-Record-Out Fixed-Model Report",
        "",
        "Each row holds out one source record conceptually and reports how the already fixed classifier predicts chunks from that record. Because the classifier is not retrained, this is an error localization and record-diversity audit rather than nested LORO model selection.",
        "",
        md_table(
            ["class", "records", "chunks", "correct", "accuracy", "class recall"],
            [
                [
                    row["class"],
                    row["records"],
                    row["chunks"],
                    f"{row['correct']}/{row['total']}",
                    pct(row["accuracy"]),
                    pct(row["recall"]),
                ]
                for row in class_summary
            ],
        ),
        "",
        "Prediction distribution in the last column below is `NSR/CHF/ARR/AFF`.",
        "",
        md_table(["class", "record", "chunks", "correct", "accuracy", "pred_dist"], summary_rows),
    ]
    (REPORTS / "loro_eval_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "loro_eval_summary.md")


if __name__ == "__main__":
    main()
