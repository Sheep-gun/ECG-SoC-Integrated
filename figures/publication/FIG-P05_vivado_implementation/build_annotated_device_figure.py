#!/usr/bin/env python3
"""Build a publication figure from the real Vivado Device View screenshot.

The color overlay is derived from hierarchy-specific placed primitive tile
coordinates extracted from the fixed routed checkpoint. It is not a hand-drawn
physical partition and does not imply pblock constraints.
"""

from __future__ import annotations

import base64
import csv
import html
import math
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
SCREENSHOT = HERE / "device_view_full_original.png"
OCCUPANCY = HERE / "hierarchy_tile_occupancy.csv"
ZOOM_PNG = HERE / "device_view_accelerator_inset.png"
OUT_SVG = HERE / "device_view_annotated_publication.svg"
OUT_PDF = HERE / "device_view_annotated_publication.pdf"

FONT = Path("C:/Windows/Fonts/malgun.ttf")
BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")

PAGE_W = 1600
PAGE_H = 1000

# Affine registration from routed GRID_POINT_X/Y to the supplied Device View.
# The fit was solved against the cyan placed-cell pixels in the 1212x1357
# screenshot; mean nearest-pixel error is approximately 0.96 px.
GRID_TO_IMAGE = (8.0281168, 18.3474064, 9.1350283, -574.17034435)

COLORS = {
    "accelerator": "#ff4fd8",
    "microblaze": "#ffd54a",
    "local_memory": "#69e06f",
    "sample_feeder": "#ff7043",
    "control_interconnect": "#40c4ff",
}

LABELS = {
    "accelerator": ("1", "SNN ECG accelerator", "10,485 LUT / 6,652 FF"),
    "microblaze": ("2", "MicroBlaze processor", "1,477 LUT / 1,212 FF / 3 DSP"),
    "local_memory": ("3", "Local memory", "16 BRAM"),
    "sample_feeder": ("4", "Sample feeder", "122 LUT / 176 FF"),
    "control_interconnect": ("5", "AXI / UART / interrupt", "control and result transport"),
}


def read_occupancy() -> dict[str, Counter[tuple[int, int]]]:
    scopes: dict[str, Counter[tuple[int, int]]] = defaultdict(Counter)
    with OCCUPANCY.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            scopes[row["scope"]][(int(row["grid_x"]), int(row["grid_y"]))] += int(
                row["placed_primitives"]
            )
    missing = set(COLORS) - set(scopes)
    if missing:
        raise RuntimeError(f"hierarchy_tile_occupancy.csv is missing scopes: {sorted(missing)}")
    return scopes


def grid_to_image(point: tuple[int, int]) -> tuple[float, float]:
    ax, bx, ay, by = GRID_TO_IMAGE
    return ax * point[0] + bx, ay * point[1] + by


def weighted_center(counter: Counter[tuple[int, int]]) -> tuple[float, float]:
    total = sum(counter.values())
    x = sum(grid_to_image(p)[0] * n for p, n in counter.items()) / total
    y = sum(grid_to_image(p)[1] * n for p, n in counter.items()) / total
    return x, y


def point_size(count: int) -> float:
    return 4.2 + min(3.2, math.log2(count + 1) * 0.85)


def make_zoom() -> tuple[int, int, int, int]:
    crop = (70, 70, 1000, 1160)
    with Image.open(SCREENSHOT) as image:
        image.crop(crop).save(ZOOM_PNG, dpi=(144, 144))
    return crop


def svg_image(path: Path, x: float, y: float, w: float, h: float) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
        f'preserveAspectRatio="none" href="data:image/png;base64,{data}"/>'
    )


def svg_overlay(
    scopes: dict[str, Counter[tuple[int, int]]],
    keys: list[str],
    source_box: tuple[float, float, float, float],
    target_box: tuple[float, float, float, float],
    opacity: float,
) -> str:
    sx0, sy0, sx1, sy1 = source_box
    tx, ty, tw, th = target_box
    scale_x = tw / (sx1 - sx0)
    scale_y = th / (sy1 - sy0)
    chunks: list[str] = []
    for key in keys:
        color = COLORS[key]
        for point, count in scopes[key].items():
            px, py = grid_to_image(point)
            if not (sx0 <= px <= sx1 and sy0 <= py <= sy1):
                continue
            size = point_size(count)
            x = tx + (px - sx0) * scale_x - size * scale_x / 2
            y = ty + (py - sy0) * scale_y - size * scale_y / 2
            chunks.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" '
                f'width="{size * scale_x:.2f}" height="{size * scale_y:.2f}" '
                f'rx="1" fill="{color}" fill-opacity="{opacity:.2f}"/>'
            )
    return "".join(chunks)


def build_svg(scopes: dict[str, Counter[tuple[int, int]]], crop: tuple[int, int, int, int]) -> None:
    image_w, image_h = Image.open(SCREENSHOT).size
    left = (38, 110, 742, 830)
    zoom = (825, 145, 405, 445)
    legend_x = 1250
    keys = list(COLORS)

    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}" height="{PAGE_H}" viewBox="0 0 {PAGE_W} {PAGE_H}">',
        '<rect width="1600" height="1000" fill="#f8fafc"/>',
        '<style>.t{font:700 34px "Malgun Gothic",sans-serif;fill:#0f172a}.st{font:17px "Malgun Gothic",sans-serif;fill:#475569}.ph{font:700 21px "Malgun Gothic",sans-serif;fill:#0f172a}.lb{font:700 17px "Malgun Gothic",sans-serif;fill:#0f172a}.sm{font:14px "Malgun Gothic",sans-serif;fill:#475569}.xs{font:12px "Malgun Gothic",sans-serif;fill:#64748b}.wm{font:700 15px "Malgun Gothic",sans-serif;fill:#fff}</style>',
        '<text x="38" y="48" class="t">Post-route FPGA implementation and hierarchy placement</text>',
        '<text x="38" y="78" class="st">Vivado 2020.2 · Artix-7 XC7A100T · fixed routed checkpoint의 실제 Device View</text>',
        '<rect x="28" y="94" width="762" height="856" rx="12" fill="#0b1020" stroke="#94a3b8"/>',
        '<text x="48" y="126" class="wm">(a) 전체 MicroBlaze 통합 system</text>',
        svg_image(SCREENSHOT, *left),
        svg_overlay(scopes, keys, (0, 0, image_w, image_h), left, 0.80),
        '<rect x="810" y="94" width="762" height="516" rx="12" fill="#ffffff" stroke="#cbd5e1"/>',
        '<text x="830" y="126" class="ph">(b) SNN accelerator에 속한 배치 셀만 분리 표시</text>',
        svg_image(ZOOM_PNG, *zoom),
        '<rect x="825" y="145" width="405" height="445" fill="#020617" fill-opacity="0.25"/>',
        svg_overlay(scopes, ["accelerator"], crop, zoom, 0.92),
    ]

    for idx, key in enumerate(keys):
        number, title, detail = LABELS[key]
        y = 170 + idx * 78
        chunks.extend(
            [
                f'<rect x="{legend_x}" y="{y-19}" width="20" height="20" rx="4" fill="{COLORS[key]}"/>',
                f'<text x="{legend_x+10}" y="{y-4}" text-anchor="middle" class="wm">{number}</text>',
                f'<text x="{legend_x+32}" y="{y-5}" class="lb">{html.escape(title)}</text>',
                f'<text x="{legend_x+32}" y="{y+18}" class="sm">{html.escape(detail)}</text>',
            ]
        )

    # Numbered markers on the real placement image.
    for key in keys:
        number, _, _ = LABELS[key]
        cx, cy = weighted_center(scopes[key])
        mx = left[0] + cx / image_w * left[2]
        my = left[1] + cy / image_h * left[3]
        chunks.extend(
            [
                f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="14" fill="#0f172a" stroke="{COLORS[key]}" stroke-width="4"/>',
                f'<text x="{mx:.1f}" y="{my+5:.1f}" text-anchor="middle" class="wm">{number}</text>',
            ]
        )

    chunks.extend(
        [
            '<rect x="810" y="630" width="762" height="320" rx="12" fill="#ffffff" stroke="#cbd5e1"/>',
            '<text x="830" y="670" class="ph">(c) 구현 범위와 정량 결과</text>',
            '<rect x="835" y="700" width="710" height="54" rx="8" fill="#eef2ff"/>',
            '<text x="855" y="733" class="lb">signed 12-bit stream → Snapshot evidence → Final membrane / WTA decision</text>',
            '<text x="835" y="790" class="lb">Pure RTL accelerator</text>',
            '<text x="835" y="816" class="sm">9,719 LUT · 5,038 FF · 0 BRAM · 0 DSP · WNS 8.184 ns</text>',
            '<text x="835" y="855" class="lb">MicroBlaze integrated post-route system</text>',
            '<text x="835" y="881" class="sm">12,494 LUT · 8,494 FF · 16 BRAM · 3 DSP · WNS 0.097 ns</text>',
            '<text x="835" y="918" class="xs">색상은 routed checkpoint의 실제 placed primitive 좌표이다. 기능 블록을 pblock으로 고정했다는 의미는 아니다.</text>',
            '<text x="38" y="978" class="xs">Post-route FPGA Device View. ASIC layout이 아니며, 물리 AFE·ADC silicon 또는 post-layout 결과를 의미하지 않는다.</text>',
            '</svg>',
        ]
    )
    OUT_SVG.write_text("".join(chunks), encoding="utf-8")


def build_pdf(scopes: dict[str, Counter[tuple[int, int]]], crop: tuple[int, int, int, int]) -> None:
    pdfmetrics.registerFont(TTFont("Malgun", FONT))
    pdfmetrics.registerFont(TTFont("Malgun-Bold", BOLD))
    c = canvas.Canvas(str(OUT_PDF), pagesize=(PAGE_W, PAGE_H), pageCompression=1)

    def rect(x, y, w, h, fill, stroke=None, radius=0, width=1):
        c.setFillColor(HexColor(fill))
        c.setStrokeColor(HexColor(stroke or fill))
        c.setLineWidth(width)
        if radius:
            c.roundRect(x, PAGE_H - y - h, w, h, radius, fill=1, stroke=1 if stroke else 0)
        else:
            c.rect(x, PAGE_H - y - h, w, h, fill=1, stroke=1 if stroke else 0)

    def text(x, y, value, size, bold=False, color="#0f172a"):
        c.setFillColor(HexColor(color))
        c.setFont("Malgun-Bold" if bold else "Malgun", size)
        c.drawString(x, PAGE_H - y, value)

    def image(path, x, y, w, h):
        c.drawImage(ImageReader(str(path)), x, PAGE_H - y - h, w, h, preserveAspectRatio=False, mask="auto")

    def overlay(keys, source_box, target_box, opacity):
        sx0, sy0, sx1, sy1 = source_box
        tx, ty, tw, th = target_box
        scale_x = tw / (sx1 - sx0)
        scale_y = th / (sy1 - sy0)
        for key in keys:
            c.setFillColor(HexColor(COLORS[key]))
            c.setFillAlpha(opacity)
            for point, count in scopes[key].items():
                px, py = grid_to_image(point)
                if not (sx0 <= px <= sx1 and sy0 <= py <= sy1):
                    continue
                size = point_size(count)
                x = tx + (px - sx0) * scale_x - size * scale_x / 2
                y = ty + (py - sy0) * scale_y - size * scale_y / 2
                c.roundRect(x, PAGE_H - y - size * scale_y, size * scale_x, size * scale_y, 0.7, fill=1, stroke=0)
        c.setFillAlpha(1)

    image_w, image_h = Image.open(SCREENSHOT).size
    left = (38, 110, 742, 830)
    zoom = (825, 145, 405, 445)
    keys = list(COLORS)

    rect(0, 0, PAGE_W, PAGE_H, "#f8fafc")
    text(38, 48, "Post-route FPGA implementation and hierarchy placement", 34, True)
    text(38, 78, "Vivado 2020.2 · Artix-7 XC7A100T · fixed routed checkpoint의 실제 Device View", 17, color="#475569")
    rect(28, 94, 762, 856, "#0b1020", "#94a3b8", 12)
    text(48, 126, "(a) 전체 MicroBlaze 통합 system", 15, True, "#ffffff")
    image(SCREENSHOT, *left)
    overlay(keys, (0, 0, image_w, image_h), left, 0.80)

    rect(810, 94, 762, 516, "#ffffff", "#cbd5e1", 12)
    text(830, 126, "(b) SNN accelerator에 속한 배치 셀만 분리 표시", 21, True)
    image(ZOOM_PNG, *zoom)
    c.setFillColor(HexColor("#020617"))
    c.setFillAlpha(0.25)
    c.rect(zoom[0], PAGE_H - zoom[1] - zoom[3], zoom[2], zoom[3], fill=1, stroke=0)
    c.setFillAlpha(1)
    overlay(["accelerator"], crop, zoom, 0.92)

    legend_x = 1250
    for idx, key in enumerate(keys):
        number, title, detail = LABELS[key]
        y = 170 + idx * 78
        rect(legend_x, y - 19, 20, 20, COLORS[key], radius=4)
        c.setFillColor(white)
        c.setFont("Malgun-Bold", 13)
        c.drawCentredString(legend_x + 10, PAGE_H - y + 4, number)
        text(legend_x + 32, y - 5, title, 17, True)
        text(legend_x + 32, y + 18, detail, 14, color="#475569")

    for key in keys:
        number, _, _ = LABELS[key]
        cx, cy = weighted_center(scopes[key])
        mx = left[0] + cx / image_w * left[2]
        my = left[1] + cy / image_h * left[3]
        c.setFillColor(HexColor("#0f172a"))
        c.setStrokeColor(HexColor(COLORS[key]))
        c.setLineWidth(4)
        c.circle(mx, PAGE_H - my, 14, fill=1, stroke=1)
        c.setFillColor(white)
        c.setFont("Malgun-Bold", 14)
        c.drawCentredString(mx, PAGE_H - my - 5, number)

    rect(810, 630, 762, 320, "#ffffff", "#cbd5e1", 12)
    text(830, 670, "(c) 구현 범위와 정량 결과", 21, True)
    rect(835, 700, 710, 54, "#eef2ff", radius=8)
    text(855, 733, "signed 12-bit stream → Snapshot evidence → Final membrane / WTA decision", 17, True)
    text(835, 790, "Pure RTL accelerator", 17, True)
    text(835, 816, "9,719 LUT · 5,038 FF · 0 BRAM · 0 DSP · WNS 8.184 ns", 14, color="#475569")
    text(835, 855, "MicroBlaze integrated post-route system", 17, True)
    text(835, 881, "12,494 LUT · 8,494 FF · 16 BRAM · 3 DSP · WNS 0.097 ns", 14, color="#475569")
    text(835, 918, "색상은 routed checkpoint의 실제 placed primitive 좌표이다. 기능 블록을 pblock으로 고정했다는 의미는 아니다.", 12, color="#64748b")
    text(38, 978, "Post-route FPGA Device View. ASIC layout이 아니며, 물리 AFE·ADC silicon 또는 post-layout 결과를 의미하지 않는다.", 12, color="#64748b")
    c.showPage()
    c.save()


def main() -> None:
    for path in (SCREENSHOT, OCCUPANCY, FONT, BOLD):
        if not path.exists():
            raise FileNotFoundError(path)
    scopes = read_occupancy()
    crop = make_zoom()
    build_svg(scopes, crop)
    build_pdf(scopes, crop)
    print(f"generated {OUT_SVG.name}, {OUT_PDF.name}, {ZOOM_PNG.name}")


if __name__ == "__main__":
    main()
