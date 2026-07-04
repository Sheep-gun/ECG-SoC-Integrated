from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from award_readiness_common import CLASSES, FIGURES, REPORTS, all_chunks, infer_many, md_table, metrics, pct, write_csv, write_json


EXPERIMENTS = [
    ("full_model", "full", "Measured", "Frozen final Python golden rule set."),
    ("arr_focus_no_margin", "arr_focus_no_margin", "Measured", "Final model without the last AFF->ARR margin evidence rescue."),
    ("base_final", "base_final", "Measured", "Base final membrane rule set before ARR-focus post rules."),
    ("snapshot_majority", "snapshot_majority", "Measured", "30 snapshot WTA votes only; no final membrane evidence currents."),
    ("snapshot_mem_sum", "snapshot_mem_sum", "Measured", "Sum of 60s snapshot class membranes only."),
    ("feature_sum_zeroed", "feature_sum_zeroed", "Limited", "Final-layer evidence sums zeroed; does not remove snapshot RTL feature extraction."),
]


def draw_bar(path: Path, rows: list[dict[str, object]]) -> None:
    width, height = 980, 560
    left, right, top, bottom = 250, 40, 50, 70
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((left, 18), "Ablation accuracy summary", fill=(30, 30, 30))
    plot_w = width - left - right
    plot_h = height - top - bottom
    for i in range(6):
        x = left + int(plot_w * i / 5)
        draw.line((x, top, x, height - bottom), fill=(225, 225, 225))
        draw.text((x - 12, height - bottom + 10), f"{i*20}", fill=(90, 90, 90))
    measured = [row for row in rows if row["status"] != "TODO"]
    bar_h = max(22, int(plot_h / max(1, len(measured)) * 0.55))
    gap = max(12, int(plot_h / max(1, len(measured)) * 0.35))
    y = top + 14
    for row in measured:
        acc = float(row["accuracy"])
        bar_w = int(plot_w * acc)
        color = (32, 96, 180) if row["status"] == "Measured" else (220, 140, 35)
        draw.text((10, y + 2), str(row["experiment"])[:38], fill=(30, 30, 30))
        draw.rectangle((left, y, left + bar_w, y + bar_h), fill=color)
        draw.text((left + bar_w + 6, y + 2), f"{acc*100:.1f}%", fill=(30, 30, 30))
        y += bar_h + gap
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    chunks = all_chunks()
    rows: list[dict[str, object]] = []
    baseline_acc = None
    for experiment, mode, status, notes in EXPERIMENTS:
        pred, _ = infer_many(chunks, mode=mode)
        m = metrics(chunks, pred)
        if baseline_acc is None:
            baseline_acc = m["accuracy"]
        rows.append(
            {
                "experiment": experiment,
                "status": status,
                "correct": m["correct"],
                "total": m["total"],
                "accuracy": m["accuracy"],
                "delta_vs_full": m["accuracy"] - baseline_acc,
                "macro_f1": m["macro_f1"],
                "ARR_recall": m["per_class"]["ARR"]["recall"],
                "AFF_recall": m["per_class"]["AFF"]["recall"],
                "notes": notes,
            }
        )

    todo_rows = [
        {
            "experiment": "afe_off_raw_mem",
            "status": "TODO",
            "correct": "",
            "total": "",
            "accuracy": "",
            "delta_vs_full": "",
            "macro_f1": "",
            "ARR_recall": "",
            "AFF_recall": "",
            "notes": "Raw-converted non-AFE full-record .mem set is not present in the repo.",
        },
        {
            "experiment": "hpf_notch_lpf_off",
            "status": "TODO",
            "correct": "",
            "total": "",
            "accuracy": "",
            "delta_vs_full": "",
            "macro_f1": "",
            "ARR_recall": "",
            "AFF_recall": "",
            "notes": "Requires regenerating full-record .mem variants through the AFE/XMODEL conversion pipeline.",
        },
        {
            "experiment": "rtl_feature_module_synthesis_ablation",
            "status": "TODO",
            "correct": "",
            "total": "",
            "accuracy": "",
            "delta_vs_full": "",
            "macro_f1": "",
            "ARR_recall": "",
            "AFF_recall": "",
            "notes": "Would require separate RTL variants and synthesis runs; not fabricated here.",
        },
    ]
    rows.extend(todo_rows)
    write_csv(REPORTS / "ablation_summary.csv", rows)
    write_json(REPORTS / "ablation_summary.json", rows)
    draw_bar(FIGURES / "ablation_accuracy_bar.png", rows)

    table_rows = []
    for row in rows:
        if row["status"] == "TODO":
            table_rows.append([row["experiment"], row["status"], "-", "-", "-", row["notes"]])
        else:
            table_rows.append(
                [
                    row["experiment"],
                    row["status"],
                    f"{row['correct']}/{row['total']}",
                    pct(float(row["accuracy"])),
                    f"{float(row['delta_vs_full'])*100:+.2f} pp",
                    row["notes"],
                ]
            )
    md = [
        "# Ablation Summary",
        "",
        "Measured rows reuse the fixed Python golden model and existing chunk feature dumps. TODO rows identify ablations that require regenerating input data or RTL variants and are not claimed as completed.",
        "",
        md_table(["experiment", "status", "correct", "accuracy", "delta_vs_full", "notes"], table_rows),
        "",
        "Figure: `reports/award_readiness/figures/ablation_accuracy_bar.png`",
    ]
    (REPORTS / "ablation_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "ablation_summary.md")


if __name__ == "__main__":
    main()
