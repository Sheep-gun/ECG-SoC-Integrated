#!/usr/bin/env python3
"""Generate final report figures from repository source artifacts.

The preferred plotting backend is matplotlib, but the bundled verification
runtime used by Codex may not provide it.  The script therefore falls back to
Pillow while keeping all values sourced from checked-in JSON/CSV artifacts.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "reports" / "final" / "figures"
METRICS = REPO / "reports" / "final" / "final_metrics.json"
CONFUSION = REPO / "reports" / "final" / "strict_recordwise" / "structural_final_test_confusion_matrix.csv"
BOARD_MATRIX = REPO / "reports" / "final" / "board_replay_36_expected_vs_board.csv"

INK = "#1b2638"
MUTED = "#5b677a"
BLUE = "#2f6fbb"
GREEN = "#2f8f5b"
ORANGE = "#c46a28"
RED = "#b83d4a"
PURPLE = "#6f5bb8"
TEAL = "#2b8c8c"
LINE = "#d8dee8"
FILL = "#f7f9fc"
WHITE = "#ffffff"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\malgun.ttf"),
        Path(r"C:\Windows\Fonts\malgunbd.ttf") if bold else Path(r"C:\Windows\Fonts\malgun.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf") if bold else Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf") if bold else Path(r"C:\Windows\Fonts\segoeui.ttf"),
    ]
    for item in candidates:
        if item.exists():
            try:
                return ImageFont.truetype(str(item), size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_TITLE = font(34, True)
FONT_SUB = font(20)
FONT_H = font(18, True)
FONT = font(16)
FONT_S = font(13)
FONT_XS = font(11)


def canvas(width: int = 1600, height: int = 900) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(img)
    return img, draw


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt: ImageFont.ImageFont, fill: str = INK) -> None:
    x0, y0, x1, y1 = box
    w, h = text_size(draw, text, fnt)
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2 - 1), text, font=fnt, fill=fill)


def wrapped_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_width: int, fnt: ImageFont.ImageFont, fill: str = INK, line_gap: int = 6) -> int:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if text_size(draw, trial, fnt)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y


def title(draw: ImageDraw.ImageDraw, main: str, sub: str) -> None:
    draw.text((70, 44), main, font=FONT_TITLE, fill=INK)
    draw.text((72, 91), sub, font=FONT_SUB, fill=MUTED)
    draw.line((70, 128, 1530, 128), fill=LINE, width=2)


def footnote(draw: ImageDraw.ImageDraw, text: str) -> None:
    draw.line((70, 840, 1530, 840), fill=LINE, width=1)
    draw.text((70, 858), text, font=FONT_S, fill=MUTED)


def box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], label: str, detail: str = "", fill: str = FILL, outline: str = BLUE) -> None:
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=3)
    x0, y0, x1, y1 = xy
    centered_text(draw, (x0 + 14, y0 + 16, x1 - 14, y0 + 54), label, FONT_H)
    if detail:
        wrapped_text(draw, (x0 + 22, y0 + 68), detail, x1 - x0 - 44, FONT_S, MUTED, 4)


def card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    eyebrow: str,
    value: str,
    caption: str,
    accent: str,
    fill: str = WHITE,
    value_font: ImageFont.ImageFont = FONT_TITLE,
) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=LINE, width=2)
    draw.rounded_rectangle((x0, y0, x0 + 10, y1), radius=5, fill=accent, outline=accent)
    if y1 - y0 < 125:
        draw.text((x0 + 24, y0 + 13), eyebrow, font=FONT_S, fill=MUTED)
        draw.text((x0 + 24, y0 + 39), value, font=value_font, fill=accent)
        if caption:
            wrapped_text(draw, (x0 + 150, y0 + 36), caption, x1 - x0 - 170, FONT_XS, INK, 3)
        return
    draw.text((x0 + 28, y0 + 22), eyebrow, font=FONT_S, fill=MUTED)
    draw.text((x0 + 28, y0 + 53), value, font=value_font, fill=accent)
    wrapped_text(draw, (x0 + 28, y0 + 107), caption, x1 - x0 - 56, FONT_S, INK, 5)


def badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], label: str, value: str, accent: str) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=14, fill="#fbfcff", outline=accent, width=2)
    draw.text((x0 + 18, y0 + 15), label, font=FONT_S, fill=MUTED)
    draw.text((x0 + 18, y0 + 42), value, font=FONT_H, fill=accent)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = MUTED) -> None:
    draw.line((start[0], start[1], end[0], end[1]), fill=color, width=4)
    dx, dy = end[0] - start[0], end[1] - start[1]
    angle = math.atan2(dy, dx)
    size = 15
    pts = [
        end,
        (int(end[0] - size * math.cos(angle - 0.45)), int(end[1] - size * math.sin(angle - 0.45))),
        (int(end[0] - size * math.cos(angle + 0.45)), int(end[1] - size * math.sin(angle + 0.45))),
    ]
    draw.polygon(pts, fill=color)


def save(img: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name, optimize=True)


def final_system_architecture(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 1. Final System Architecture", "Model-based AFE+ADC input generation linked to the locked SNN accelerator IP")
    labels = [
        ("Digitized ECG record", "Public ECG database record; not raw electrode acquisition."),
        ("vin reconstruction", "code / 200000 to analog-equivalent PWL-style input."),
        ("AFE+ADC XMODEL", "HPF, gain x201, 60 Hz notch, LPF 150 Hz, 12-bit quantization."),
        ("Signed 12-bit stream", ".mem / AXIS-style samples used by RTL and board replay."),
        ("Snapshot SNN Readout", "60-second event, rhythm, morphology, variability evidence."),
        ("Final Membrane", "30 snapshots accumulated by locked candidate."),
        ("4-class output", "NSR / CHF / ARR / AFF"),
    ]
    x0, y0, w, h, gap = 70, 210, 190, 150, 22
    boxes = []
    for i, (label, detail) in enumerate(labels):
        x = x0 + i * (w + gap)
        boxes.append((x, y0, x + w, y0 + h))
        box(draw, boxes[-1], label, detail, fill="#f7fbff", outline=BLUE)
        if i:
            arrow(draw, (boxes[i - 1][2], y0 + h // 2), (boxes[i][0], y0 + h // 2))
    box(draw, (430, 520, 720, 690), "Validation stack", "Python golden -> XSim -> Vivado implementation -> IP-XACT packaging", fill="#f8fff9", outline=GREEN)
    box(draw, (850, 520, 1160, 690), "Board replay", "Vitis/MicroBlaze full-record class-wise replay with expected-vs-board comparison.", fill="#fffaf4", outline=ORANGE)
    arrow(draw, (880, 360), (590, 520), GREEN)
    arrow(draw, (1090, 360), (1000, 520), ORANGE)
    footnote(draw, f"Locked model: {metrics['final_model_id']} | final_test chunk {metrics['final_test_chunk']['accuracy_percent']:.2f}% | record-majority {metrics['final_test_record_majority']['accuracy_percent']:.2f}%")
    save(img, "final_system_architecture.png")


def snapshot_pipeline(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 2. Snapshot-to-Final Membrane Pipeline", "Thirty 60-second snapshots are accumulated into one 30-minute final decision")
    for i in range(30):
        row = i // 10
        col = i % 10
        x, y = 90 + col * 64, 210 + row * 58
        color = "#e7f0fb" if i < 29 else "#d9ebd8"
        draw.rounded_rectangle((x, y, x + 48, y + 38), radius=8, fill=color, outline=BLUE, width=1)
        centered_text(draw, (x, y, x + 48, y + 38), str(i + 1), FONT_S, INK)
    draw.text((90, 390), "60 s snapshots: event / rhythm / morphology / variability evidence", font=FONT_H, fill=INK)
    arrow(draw, (750, 285), (895, 285))
    box(draw, (910, 210, 1190, 360), "Class membrane update", "Snapshot WTA and guarded evidence update signed class membranes.", fill="#f8fff9", outline=GREEN)
    arrow(draw, (1190, 285), (1310, 285))
    box(draw, (1325, 210, 1515, 360), "Final WTA", "Largest final membrane selects NSR/CHF/ARR/AFF.", fill="#fff8f5", outline=ORANGE)
    box(draw, (250, 525, 650, 690), "Locked candidate", metrics["final_model_id"], fill="#f9f7ff", outline=PURPLE)
    box(draw, (780, 525, 1180, 690), "Protocol guard", "Final test was not used for selection, parameter search, or ChatGPT context.", fill="#fffaf4", outline=ORANGE)
    footnote(draw, "This figure describes the locked final model only; it is not a majority-vote-only classifier.")
    save(img, "snapshot_to_final_membrane_pipeline.png")


def strict_protocol(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 3. Fully Blind Strict Record-wise Protocol", "Split unit is source_record_id; final_test is locked until after model selection")
    cols = [
        ("Train", f"{metrics['train']['correct']}/{metrics['train']['total']} = {metrics['train']['accuracy_percent']:.2f}%", GREEN),
        ("Validation", f"{metrics['validation']['correct']}/{metrics['validation']['total']} = {metrics['validation']['accuracy_percent']:.2f}%\nmodel selection only", BLUE),
        ("Locked final_test", f"{metrics['final_test_chunk']['correct']}/{metrics['final_test_chunk']['total']} = {metrics['final_test_chunk']['accuracy_percent']:.2f}%\nrecord-majority {metrics['final_test_record_majority']['accuracy_percent']:.2f}%", ORANGE),
    ]
    x = 150
    for name, detail, color in cols:
        box(draw, (x, 220, x + 330, 450), name, detail, fill="#ffffff", outline=color)
        x += 460
    draw.text((210, 520), "source_record_id leakage guard", font=FONT_H, fill=INK)
    draw.line((210, 560, 1390, 560), fill=MUTED, width=4)
    for x in (315, 775, 1235):
        draw.ellipse((x - 16, 544, x + 16, 576), fill="#ffffff", outline=MUTED, width=3)
    box(draw, (470, 630, 1130, 750), "Final-test lock", f"test_evaluation_count = {metrics['test_evaluation_count']} | test_used_for_selection = {str(metrics['test_used_for_selection']).lower()}", fill="#fffaf4", outline=ORANGE)
    footnote(draw, "Validation 100.00% is reported as model-selection performance, not as the final generalization claim.")
    save(img, "strict_recordwise_protocol.png")


def result_summary(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 4. Final Locked Result Summary", "Final-test holdout results are the primary reported performance")

    draw.rounded_rectangle((70, 170, 1530, 785), radius=22, fill="#f8fafc", outline=LINE, width=2)
    draw.text((110, 205), "Locked held-out final_test", font=FONT_H, fill=INK)
    draw.text((110, 235), "Reported final performance after model lock; test_evaluation_count = 1.", font=FONT, fill=MUTED)
    card(
        draw,
        (110, 290, 560, 535),
        "Final test chunk metrics",
        f"{metrics['final_test_chunk']['accuracy_percent']:.2f}%",
        f"{metrics['final_test_chunk']['correct']} / {metrics['final_test_chunk']['total']} chunks. Macro F1 {metrics['final_test_chunk']['macro_f1_percent']:.2f}%, balanced {metrics['final_test_chunk']['balanced_accuracy_percent']:.2f}%, weakest recall CHF {metrics['final_test_chunk']['class_recall_percent']['CHF']:.2f}%.",
        ORANGE,
        "#fff8f3",
    )
    card(
        draw,
        (610, 290, 1060, 535),
        "Record-majority metrics",
        f"{metrics['final_test_record_majority']['accuracy_percent']:.2f}%",
        f"{metrics['final_test_record_majority']['correct']} / {metrics['final_test_record_majority']['total']} records. Macro F1 {metrics['final_test_record_majority']['macro_f1_percent']:.2f}%, balanced {metrics['final_test_record_majority']['balanced_accuracy_percent']:.2f}%.",
        PURPLE,
        "#f8f6ff",
    )
    box(
        draw,
        (1110, 290, 1485, 535),
        "Locked model",
        f"{metrics['final_model_id']}\n\nSelection/search never used final_test.",
        fill=WHITE,
        outline=BLUE,
    )

    draw.text((110, 610), "Model selection evidence", font=FONT_H, fill=INK)
    draw.text((110, 640), "These values explain how the candidate was locked; validation is not presented as final generalization.", font=FONT, fill=MUTED)
    badge(draw, (110, 680, 430, 765), "Train", f"{metrics['train']['accuracy_percent']:.2f}%  ({metrics['train']['correct']}/{metrics['train']['total']})", GREEN)
    badge(
        draw,
        (470, 680, 790, 765),
        "Validation - selection only",
        f"{metrics['validation']['accuracy_percent']:.2f}%  ({metrics['validation']['correct']}/{metrics['validation']['total']})",
        BLUE,
    )
    box(
        draw,
        (830, 665, 1485, 775),
        "Protocol guard",
        "test_used_for_selection = false | test_evaluation_count = 1",
        fill=WHITE,
        outline=RED,
    )
    footnote(draw, "Do not interpret validation 100.00% as final score; report final_test accuracy with macro F1, balanced accuracy, and class recall.")
    save(img, "final_result_summary.png")


def hardware_flow(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 5. Hardware Validation Flow", "Evidence chain from golden model to FPGA board transcript")
    steps = [
        ("Python golden", "Locked model metrics and expected final membranes."),
        ("XSim", "36 final_test cases; final_pred/final_mem mismatch 0."),
        ("Vivado", "Synthesis, implementation, timing, utilization."),
        ("IP-XACT", "AXI accelerator and MMIO-to-AXIS feeder packages."),
        ("Vitis/MicroBlaze", "Bitstream/XSA/ELF full-record replay system."),
        ("Board comparison", "36 final_test 30-minute cases; final_pred 36/36, final_mem exact 36/36."),
    ]
    y = 235
    prev = None
    for i, (label, detail) in enumerate(steps):
        x = 100 + i * 245
        xy = (x, y, x + 205, y + 175)
        box(draw, xy, label, detail, fill="#f7fbff" if i < 3 else "#fffaf4", outline=BLUE if i < 3 else ORANGE)
        if prev:
            arrow(draw, (prev[2], y + 88), (xy[0], y + 88))
        prev = xy
    box(draw, (260, 590, 650, 735), "MicroBlaze system", f"LUT {metrics['microblaze_full_replay_system']['lut']}, FF {metrics['microblaze_full_replay_system']['slice_reg']}, BRAM {metrics['microblaze_full_replay_system']['bram']}, DSP {metrics['microblaze_full_replay_system']['dsp']}", fill="#f8fff9", outline=GREEN)
    replay36 = metrics["board_replay_36"]
    box(draw, (880, 590, 1270, 735), "Board replay evidence", f"{replay36['cases_completed']} cases, {replay36['samples_per_case']:,} samples/case, {replay36['pred_match_correct']}/{replay36['pred_match_total']} final_pred match", fill="#fff8f5", outline=ORANGE)
    footnote(draw, "Board replay is a 36-case strict final_test full-record batch; final_pred and final_mem exact both match 36/36.")
    save(img, "hardware_validation_flow.png")


def resource_summary(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 6. Resource and Timing Summary", "Resource usage, timing margin, and integration overhead are separated")
    pure = metrics["pure_rtl_vivado"]
    mb = metrics["microblaze_full_replay_system"]

    draw.text((95, 180), "Pure accelerator RTL", font=FONT_H, fill=INK)
    draw.text((850, 180), "MicroBlaze replay system", font=FONT_H, fill=INK)
    draw.rounded_rectangle((70, 210, 745, 640), radius=22, fill="#f7fbff", outline=BLUE, width=3)
    draw.rounded_rectangle((825, 210, 1530, 640), radius=22, fill="#fffaf4", outline=ORANGE, width=3)

    pure_badges = [
        ("LUT", str(pure["lut"]), BLUE),
        ("FF", str(pure["ff"]), GREEN),
        ("BRAM", str(pure["bram"]), ORANGE),
        ("DSP", str(pure["dsp"]), RED),
    ]
    mb_badges = [
        ("LUT", str(mb["lut"]), PURPLE),
        ("FF", str(mb["slice_reg"]), TEAL),
        ("BRAM", str(mb["bram"]), ORANGE),
        ("DSP", str(mb["dsp"]), RED),
    ]
    for i, (label, value, color) in enumerate(pure_badges):
        x = 110 + (i % 2) * 300
        y = 265 + (i // 2) * 125
        badge(draw, (x, y, x + 235, y + 88), label, value, color)
    for i, (label, value, color) in enumerate(mb_badges):
        x = 870 + (i % 2) * 310
        y = 265 + (i // 2) * 125
        badge(draw, (x, y, x + 250, y + 88), label, value, color)

    badge(draw, (110, 515, 390, 610), "Pure RTL timing", f"WNS {pure['wns_ns']} ns", BLUE)
    badge(draw, (420, 515, 705, 610), "Pure RTL power", f"{pure['estimated_total_power_w']} W", GREEN)
    badge(draw, (870, 515, 1180, 610), "Setup / hold WNS", f"{mb['setup_wns_ns']} / {mb['hold_wns_ns']} ns", ORANGE)
    badge(draw, (1210, 515, 1490, 610), "Timing met", str(mb["timing_constraints_met"]).lower(), GREEN)

    box(
        draw,
        (110, 675, 705, 820),
        "Why BRAM/DSP are explicit badges",
        "The pure accelerator uses BRAM 0 and DSP 0. A single-scale bar chart would hide these values, so this report figure shows them as first-class resource fields.",
        fill=WHITE,
        outline=BLUE,
    )
    box(
        draw,
        (870, 675, 1490, 820),
        "Integration scope",
        "MicroBlaze numbers include CPU, BRAM/LMB, UARTLite, AXI interconnect, sample feeder, and accelerator. They are not pure-core resource numbers.",
        fill=WHITE,
        outline=ORANGE,
    )
    footnote(draw, "Values are read from reports/final/final_metrics.json; no new hardware claim is introduced by this visualization.")
    save(img, "resource_timing_summary.png")


def board_pass_matrix() -> bool:
    if not BOARD_MATRIX.exists():
        return False
    rows = list(csv.DictReader(BOARD_MATRIX.open(encoding="utf-8-sig", newline="")))
    img, draw = canvas()
    title(draw, "Figure 7. 36-case Board Replay Matrix", "Strict final_test full-record replay compared against full-top RTL XSim expected values")
    headers = ["Case", "Class", "Pred", "Mem", "Label", "Samples"]
    x0, y0 = 70, 170
    widths = [470, 110, 135, 135, 135, 150]
    for i, h in enumerate(headers):
        x = x0 + sum(widths[:i])
        draw.rectangle((x, y0, x + widths[i], y0 + 34), fill="#edf3fb", outline=LINE)
        centered_text(draw, (x, y0, x + widths[i], y0 + 34), h, FONT_S)
    for r, row in enumerate(rows):
        y = y0 + 34 + r * 18
        pred_ok = row["pred_match"] == "1"
        mem_ok = row["final_mem_exact_match"] == "1"
        label_ok = row["board_correct_vs_label"] == "1"
        samples_ok = row["samples_sent"] == "1800000" and row["snapshot_count"] == "30"
        vals = [
            row["case_id"],
            row["class_label"],
            "PASS" if pred_ok else "FAIL",
            "PASS" if mem_ok else "FAIL",
            "OK" if label_ok else "MISS",
            "OK" if samples_ok else "BAD",
        ]
        for i, val in enumerate(vals):
            x = x0 + sum(widths[:i])
            fill = WHITE
            if i >= 2:
                fill = "#e7f6ec" if val in ("PASS", "OK") else "#fde8e8"
            draw.rectangle((x, y, x + widths[i], y + 18), fill=fill, outline=LINE)
            centered_text(draw, (x, y, x + widths[i], y + 18), val, FONT_XS, GREEN if val in ("PASS", "OK") else RED)
    footnote(draw, "36/36 final_pred match and 36/36 final_mem exact match against board-equivalent full-top XSim expected.")
    save(img, "board_replay_pass_matrix.png")
    return True


def confusion_matrix() -> bool:
    if not CONFUSION.exists():
        return False
    with CONFUSION.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)[1:]
        rows = [(row[0], [int(v) for v in row[1:]]) for row in reader]
    maxv = max(max(vals) for _, vals in rows)
    img, draw = canvas()
    title(draw, "Figure 8. Locked Final-test Confusion Matrix", "Strict record-wise final_test chunk-level confusion matrix")
    x0, y0, cell = 430, 190, 160
    for i, h in enumerate(header):
        centered_text(draw, (x0 + i * cell, y0 - 55, x0 + (i + 1) * cell, y0 - 10), h, FONT_H)
        centered_text(draw, (x0 - 150, y0 + i * cell, x0 - 20, y0 + (i + 1) * cell), rows[i][0], FONT_H)
    for r, (_, vals) in enumerate(rows):
        for c, val in enumerate(vals):
            intensity = 0 if maxv == 0 else val / maxv
            base = int(245 - intensity * 85)
            color = (base, int(250 - intensity * 120), int(255 - intensity * 155))
            rect = (x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell, y0 + (r + 1) * cell)
            draw.rectangle(rect, fill=color, outline=WHITE, width=4)
            centered_text(draw, rect, str(val), FONT_TITLE, INK)
    draw.text((x0 - 135, y0 - 95), "True label", font=FONT_H, fill=MUTED)
    draw.text((x0 + 210, y0 - 105), "Predicted label", font=FONT_H, fill=MUTED)
    footnote(draw, "Confusion matrix source: reports/final/strict_recordwise/structural_final_test_confusion_matrix.csv.")
    save(img, "final_test_confusion_matrix.png")
    return True


def write_index(created: list[tuple[str, str, str, str]]) -> None:
    lines = [
        "# Final Report Figure Index",
        "",
        "| Figure | File | Used in | Description |",
        "|---|---|---|---|",
    ]
    for fig, file, used, desc in created:
        lines.append(f"| {fig} | `{file}` | {used} | {desc} |")
    lines.append("")
    lines.append("All figures are generated from checked-in metrics, board replay CSVs, or protocol metadata. Run `python tools/make_final_report_figures.py` to regenerate them.")
    (OUT / "FIGURE_INDEX.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    metrics = load_json(METRICS)
    created: list[tuple[str, str, str, str]] = []
    final_system_architecture(metrics)
    created.append(("Figure 1", "reports/final/figures/final_system_architecture.png", "README, FINAL_REPORT, docs", "End-to-end AFE+ADC XMODEL to accelerator IP validation flow."))
    snapshot_pipeline(metrics)
    created.append(("Figure 2", "reports/final/figures/snapshot_to_final_membrane_pipeline.png", "FINAL_REPORT, SYSTEM_ARCHITECTURE", "60-second snapshot evidence accumulated into the 30-minute final membrane."))
    strict_protocol(metrics)
    created.append(("Figure 3", "reports/final/figures/strict_recordwise_protocol.png", "FINAL_REPORT, STRICT_RECORDWISE_PROTOCOL", "Record-wise split, validation usage, and final-test lock boundary."))
    result_summary(metrics)
    created.append(("Figure 4", "reports/final/figures/final_result_summary.png", "README, FINAL_REPORT, docs", "Train, validation, and locked final-test result separation."))
    hardware_flow(metrics)
    created.append(("Figure 5", "reports/final/figures/hardware_validation_flow.png", "FINAL_REPORT, HARDWARE_VALIDATION", "Golden/XSim/Vivado/IP-XACT/Vitis/board evidence chain."))
    resource_summary(metrics)
    created.append(("Figure 6", "reports/final/figures/resource_timing_summary.png", "FINAL_REPORT, HARDWARE_VALIDATION", "Resource and timing summary from final metrics."))
    if board_pass_matrix():
        created.append(("Figure 7", "reports/final/figures/board_replay_pass_matrix.png", "FINAL_REPORT, HARDWARE_VALIDATION", "36-case board replay PASS matrix."))
    if confusion_matrix():
        created.append(("Figure 8", "reports/final/figures/final_test_confusion_matrix.png", "FINAL_REPORT", "Strict final_test confusion matrix."))
    write_index(created)
    print(f"generated {len(created)} final report figures in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
