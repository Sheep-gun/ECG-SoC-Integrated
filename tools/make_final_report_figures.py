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
BOARD_MATRIX = REPO / "reports" / "final" / "board_replay" / "locked_class_cases_xsim_vs_board.csv"

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
    title(draw, "Figure 4. Final Locked Result Summary", "Validation and final holdout are separated explicitly")
    bars = [
        ("Train", metrics["train"]["accuracy_percent"], GREEN, "61/68"),
        ("Validation", metrics["validation"]["accuracy_percent"], BLUE, "32/32\nselection only"),
        ("Final test chunk", metrics["final_test_chunk"]["accuracy_percent"], ORANGE, "29/36"),
        ("Final test record", metrics["final_test_record_majority"]["accuracy_percent"], PURPLE, "16/19"),
    ]
    chart = (160, 210, 1440, 690)
    draw.rectangle(chart, outline=LINE, width=2)
    for pct in range(0, 101, 20):
        y = chart[3] - (pct / 100) * (chart[3] - chart[1])
        draw.line((chart[0], y, chart[2], y), fill="#edf1f7", width=1)
        draw.text((105, y - 9), f"{pct}%", font=FONT_S, fill=MUTED)
    bw = 180
    for i, (label, value, color, note) in enumerate(bars):
        x = 245 + i * 300
        y = chart[3] - (value / 100) * (chart[3] - chart[1])
        draw.rounded_rectangle((x, y, x + bw, chart[3]), radius=10, fill=color, outline=color)
        centered_text(draw, (x, y - 45, x + bw, y - 5), f"{value:.2f}%", FONT_H, color)
        centered_text(draw, (x - 40, chart[3] + 18, x + bw + 40, chart[3] + 60), label, FONT, INK)
        wrapped_text(draw, (x - 8, chart[3] + 70), note, bw + 16, FONT_S, MUTED)
    footnote(draw, "Final performance claim uses the locked final_test values: chunk 80.56% and record-majority 84.21%.")
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
        ("Board comparison", "4 class-wise 30-minute cases; final_pred/final_mem 4/4."),
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
    box(draw, (880, 590, 1270, 735), "Board replay evidence", f"{metrics['board_replay']['cases']} cases, {metrics['board_replay']['samples_per_case']:,} samples/case, {metrics['board_replay']['final_pred_match']} final_pred match", fill="#fff8f5", outline=ORANGE)
    footnote(draw, "Board replay is class-wise representative replay, not a full 36-case board batch.")
    save(img, "hardware_validation_flow.png")


def resource_summary(metrics: dict) -> None:
    img, draw = canvas()
    title(draw, "Figure 6. Resource and Timing Summary", "Pure accelerator core and MicroBlaze integration are reported separately")
    pure = metrics["pure_rtl_vivado"]
    mb = metrics["microblaze_full_replay_system"]
    resources = [
        ("Pure RTL LUT", pure["lut"], BLUE),
        ("Pure RTL FF", pure["ff"], GREEN),
        ("Pure RTL BRAM", pure["bram"], ORANGE),
        ("Pure RTL DSP", pure["dsp"], RED),
        ("MB LUT", mb["lut"], PURPLE),
        ("MB FF", mb["slice_reg"], TEAL),
        ("MB BRAM", mb["bram"], ORANGE),
        ("MB DSP", mb["dsp"], RED),
    ]
    chart = (120, 210, 1480, 600)
    maxv = max(v for _, v, _ in resources)
    for i, (label, value, color) in enumerate(resources):
        x = chart[0] + i * 165
        h = 0 if maxv == 0 else int((value / maxv) * 310)
        y = chart[3] - h
        draw.rounded_rectangle((x, y, x + 95, chart[3]), radius=8, fill=color, outline=color)
        centered_text(draw, (x - 18, y - 34, x + 113, y - 6), str(value), FONT_S, color)
        wrapped_text(draw, (x - 20, chart[3] + 18), label, 145, FONT_S, INK)
    box(draw, (200, 705, 540, 800), "Pure RTL timing", f"WNS {pure['wns_ns']} ns | Power {pure['estimated_total_power_w']} W", fill="#f7fbff", outline=BLUE)
    box(draw, (660, 705, 1030, 800), "MicroBlaze timing", f"Setup WNS {mb['setup_wns_ns']} ns | Hold WNS {mb['hold_wns_ns']} ns", fill="#f8fff9", outline=GREEN)
    box(draw, (1150, 705, 1460, 800), "Integration note", "MicroBlaze numbers include CPU, BRAM/LMB, UART, AXI, feeder, and accelerator.", fill="#fffaf4", outline=ORANGE)
    footnote(draw, "Values are read from reports/final/final_metrics.json.")
    save(img, "resource_timing_summary.png")


def board_pass_matrix() -> bool:
    if not BOARD_MATRIX.exists():
        return False
    rows = list(csv.DictReader(BOARD_MATRIX.open(encoding="utf-8-sig", newline="")))
    img, draw = canvas()
    title(draw, "Figure 7. Board Replay PASS Matrix", "Class-wise 30-minute replay compared against XSim/Python expected values")
    headers = ["Case", "Class", "Pred", "Mem", "Transport"]
    x0, y0 = 160, 210
    widths = [360, 150, 170, 170, 190]
    for i, h in enumerate(headers):
        x = x0 + sum(widths[:i])
        draw.rectangle((x, y0, x + widths[i], y0 + 55), fill="#edf3fb", outline=LINE)
        centered_text(draw, (x, y0, x + widths[i], y0 + 55), h, FONT_H)
    class_names = ["NSR", "CHF", "ARR", "AFF"]
    for r, row in enumerate(rows):
        y = y0 + 55 + r * 70
        vals = [
            row["case_name"],
            class_names[int(row["class_id"])],
            "PASS" if row["final_pred_match"] == "1" else "FAIL",
            "PASS" if row["final_mem_match"] == "1" else "FAIL",
            "PASS" if row["transport_ok"] == "1" else "FAIL",
        ]
        for i, val in enumerate(vals):
            x = x0 + sum(widths[:i])
            fill = WHITE
            if i >= 2:
                fill = "#e7f6ec" if val == "PASS" else "#fde8e8"
            draw.rectangle((x, y, x + widths[i], y + 70), fill=fill, outline=LINE)
            centered_text(draw, (x, y, x + widths[i], y + 70), val, FONT if i < 2 else FONT_H, GREEN if val == "PASS" else INK)
    footnote(draw, "Board replay evidence is four representative class-wise full-record cases; this is not a 36-case board batch.")
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
        created.append(("Figure 7", "reports/final/figures/board_replay_pass_matrix.png", "FINAL_REPORT, HARDWARE_VALIDATION", "Four class-wise board replay PASS matrix."))
    if confusion_matrix():
        created.append(("Figure 8", "reports/final/figures/final_test_confusion_matrix.png", "FINAL_REPORT", "Strict final_test confusion matrix."))
    write_index(created)
    print(f"generated {len(created)} final report figures in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
