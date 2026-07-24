#!/usr/bin/env python3
"""Build screenshot-free publication assets from Vivado vector exports."""

from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FONT = Path("C:/Windows/Fonts/malgun.ttf")
BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


def read_placed_cells() -> tuple[Counter, Counter]:
    system: Counter[tuple[int, int]] = Counter()
    accelerator: Counter[tuple[int, int]] = Counter()
    with (HERE / "placed_tile_occupancy.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            point = (int(row["grid_x"]), int(row["grid_y"]))
            if row["scope"] == "accelerator_core":
                accelerator[point] += int(row["placed_primitives"])
            else:
                system[point] += int(row["placed_primitives"])
    if not system or not accelerator:
        raise RuntimeError("placed_tile_occupancy.csv does not contain both scopes")
    return system, accelerator


def bounds(points: set[tuple[int, int]], pad: int = 2) -> tuple[int, int, int, int]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad


def map_geometry(box: tuple[int, int, int, int], x: float, y: float, w: float, h: float):
    xmin, xmax, ymin, ymax = box
    sx = w / max(1, xmax - xmin + 1)
    sy = h / max(1, ymax - ymin + 1)

    def project(point: tuple[int, int]) -> tuple[float, float]:
        px = x + (point[0] - xmin) * sx
        py = y + h - (point[1] - ymin + 1) * sy
        return px, py

    return project, sx, sy


def svg_rects(counter: Counter, project, sx: float, sy: float, color: str) -> str:
    chunks = []
    peak = max(counter.values())
    for point, count in sorted(counter.items()):
        x, y = project(point)
        opacity = 0.35 + 0.65 * math.sqrt(count / peak)
        chunks.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(0.8, sx):.2f}" height="{max(0.8, sy):.2f}" fill="{color}" fill-opacity="{opacity:.3f}"/>'
        )
    return "".join(chunks)


def build_placement_svg(system: Counter, accelerator: Counter) -> None:
    all_points = set(system) | set(accelerator)
    full_box = bounds(all_points, 2)
    accel_box = bounds(set(accelerator), 3)
    fp, fsx, fsy = map_geometry(full_box, 70, 150, 900, 620)
    zp, zsx, zsy = map_geometry(accel_box, 1030, 150, 500, 620)
    metrics = json.loads((REPO / "design/digital/reports/final/final_metrics.json").read_text(encoding="utf-8"))
    pure = metrics["pure_rtl_vivado"]
    system_metrics = metrics["microblaze_full_replay_system"]
    body = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">',
        '<style>.t{font:700 28px "Malgun Gothic",sans-serif;fill:#e2e8f0}.p{font:700 18px "Malgun Gothic",sans-serif;fill:#f8fafc}.b{font:15px "Malgun Gothic",sans-serif;fill:#cbd5e1}.s{font:13px "Malgun Gothic",sans-serif;fill:#94a3b8}</style>',
        '<rect width="1600" height="900" fill="#020617"/>',
        '<text x="50" y="52" class="t">Routed FPGA tile placement map</text>',
        '<text x="50" y="84" class="b">Vivado 2020.2 routed checkpoint의 GRID_POINT_X/Y를 벡터로 표시</text>',
        '<rect x="50" y="115" width="940" height="690" rx="12" fill="#0f172a" stroke="#334155"/>',
        '<rect x="1010" y="115" width="540" height="690" rx="12" fill="#0f172a" stroke="#334155"/>',
        '<text x="70" y="142" class="p">(a) 전체 MicroBlaze 통합 system</text>',
        '<text x="1030" y="142" class="p">(b) accelerator core 확대</text>',
        svg_rects(system, fp, fsx, fsy, "#22d3ee"),
        svg_rects(accelerator, fp, fsx, fsy, "#f0abfc"),
        svg_rects(accelerator, zp, zsx, zsy, "#f0abfc"),
        '<rect x="62" y="828" width="18" height="12" fill="#22d3ee"/><text x="90" y="840" class="b">system other</text>',
        '<rect x="220" y="828" width="18" height="12" fill="#f0abfc"/><text x="248" y="840" class="b">pure classifier core</text>',
        f'<text x="500" y="840" class="b">Pure RTL: {pure["lut"]:,} LUT / {pure["ff"]:,} FF / {pure["bram"]} BRAM / {pure["dsp"]} DSP / WNS {pure["wns_ns"]:.3f} ns</text>',
        f'<text x="500" y="866" class="b">MicroBlaze system: {system_metrics["lut"]:,} LUT / {system_metrics["slice_reg"]:,} FF / {system_metrics["bram"]} BRAM / {system_metrics["dsp"]} DSP / WNS {system_metrics["setup_wns_ns"]:.3f} ns</text>',
        '<text x="1030" y="840" class="s">Vivado Device View의 native PDF/SVG export가 없어</text>',
        '<text x="1030" y="862" class="s">화면을 캡처하지 않고 routed tile 좌표를 사용했다.</text>',
        '</svg>',
    ]
    svg = "".join(body)
    (HERE / "device_placement_map.svg").write_text(svg, encoding="utf-8")
    (HERE / "vivado_implementation_composite.svg").write_text(svg, encoding="utf-8")


def draw_map_pdf(c: canvas.Canvas, counter: Counter, project, sx: float, sy: float, color):
    peak = max(counter.values())
    for point, count in counter.items():
        x, y = project(point)
        alpha = 0.35 + 0.65 * math.sqrt(count / peak)
        c.setFillAlpha(alpha)
        c.setFillColorRGB(*color)
        c.rect(x, y, max(0.45, sx), max(0.45, sy), fill=1, stroke=0)
    c.setFillAlpha(1)


def build_placement_pdf(system: Counter, accelerator: Counter) -> None:
    pdfmetrics.registerFont(TTFont("Malgun", str(FONT)))
    pdfmetrics.registerFont(TTFont("MalgunB", str(BOLD)))
    W, H = landscape(A4)
    c = canvas.Canvas(str(HERE / "device_placement_map.pdf"), pagesize=(W, H))
    c.setFillColorRGB(0.008, 0.024, 0.09)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFont("MalgunB", 17)
    c.setFillColorRGB(0.88, 0.91, 0.95)
    c.drawString(28, H - 28, "Routed FPGA tile placement map")
    c.setFont("Malgun", 9)
    c.setFillColorRGB(0.70, 0.76, 0.84)
    c.drawString(28, H - 44, "Vivado routed checkpoint의 GRID_POINT_X/Y 기반 벡터 표시 - GUI screenshot 아님")
    c.setFillColorRGB(0.06, 0.09, 0.16)
    c.roundRect(24, 60, 490, 470, 7, fill=1, stroke=0)
    c.roundRect(530, 60, 285, 470, 7, fill=1, stroke=0)
    c.setFont("MalgunB", 10)
    c.setFillColorRGB(0.97, 0.98, 1)
    c.drawString(35, 512, "(a) 전체 MicroBlaze 통합 system")
    c.drawString(540, 512, "(b) accelerator core 확대")
    full_box = bounds(set(system) | set(accelerator), 2)
    accel_box = bounds(set(accelerator), 3)
    fp, fsx, fsy = map_geometry(full_box, 35, 80, 465, 410)
    zp, zsx, zsy = map_geometry(accel_box, 540, 80, 265, 410)
    draw_map_pdf(c, system, fp, fsx, fsy, (0.13, 0.83, 0.93))
    draw_map_pdf(c, accelerator, fp, fsx, fsy, (0.94, 0.67, 0.99))
    draw_map_pdf(c, accelerator, zp, zsx, zsy, (0.94, 0.67, 0.99))
    metrics = json.loads((REPO / "design/digital/reports/final/final_metrics.json").read_text(encoding="utf-8"))
    pure = metrics["pure_rtl_vivado"]
    integrated = metrics["microblaze_full_replay_system"]
    c.setFont("Malgun", 8)
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.drawString(28, 42, f"Pure RTL: {pure['lut']:,} LUT / {pure['ff']:,} FF / {pure['bram']} BRAM / {pure['dsp']} DSP / WNS {pure['wns_ns']:.3f} ns")
    c.drawString(360, 42, f"MicroBlaze system: {integrated['lut']:,} LUT / {integrated['slice_reg']:,} FF / {integrated['bram']} BRAM / {integrated['dsp']} DSP / WNS {integrated['setup_wns_ns']:.3f} ns")
    c.drawString(28, 25, "Device View는 native PDF/SVG export를 지원하지 않아, 화면 캡처 없이 실제 routed tile 좌표만 사용했다.")
    c.save()


def normalize_svg(native: Path, output: Path) -> None:
    text = native.read_text(encoding="utf-8")
    match = re.search(r'<svg[^>]*viewBox="0 0 ([0-9.]+) ([0-9.]+)"[^>]*>(.*)</svg>\s*$', text, re.S)
    if not match:
        raise RuntimeError(f"Could not parse Vivado SVG: {native}")
    width = float(match.group(1))
    height = float(match.group(2))
    inner = match.group(3)
    normalized = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {height:g} {width:g}" preserveAspectRatio="xMidYMid meet">'
        f'<g transform="translate({height:g} 0) rotate(90)">{inner}</g></svg>'
    )
    output.write_text(normalized, encoding="utf-8")


def normalize_pdf(native: Path, output: Path, crop: tuple[float, float, float, float]) -> None:
    page = PdfReader(native).pages[0]
    page.rotation = 0
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    left, bottom, right, top = crop
    page.cropbox.lower_left = (left * width, bottom * height)
    page.cropbox.upper_right = (right * width, top * height)
    page.mediabox.lower_left = page.cropbox.lower_left
    page.mediabox.upper_right = page.cropbox.upper_right
    writer = PdfWriter()
    writer.add_page(page)
    with output.open("wb") as f:
        writer.write(f)


def normalize_vivado_vectors() -> None:
    normalize_svg(HERE / "microblaze_block_design_vivado_native.svg", HERE / "microblaze_block_design.svg")
    normalize_svg(HERE / "worst_setup_path_vivado_native.svg", HERE / "worst_setup_path.svg")
    normalize_pdf(
        HERE / "microblaze_block_design_vivado_native.pdf",
        HERE / "microblaze_block_design.pdf",
        (0.034, 0.227, 0.970, 0.773),
    )
    normalize_pdf(
        HERE / "worst_setup_path_vivado_native.pdf",
        HERE / "worst_setup_path.pdf",
        (0.028, 0.400, 0.971, 0.603),
    )


def build_pdf_package() -> None:
    writer = PdfWriter()
    for name in ["device_placement_map.pdf", "microblaze_block_design.pdf", "worst_setup_path.pdf"]:
        reader = PdfReader(HERE / name)
        writer.add_page(reader.pages[0])
    writer.add_metadata(
        {
            "/Title": "Vivado FPGA physical implementation vector package",
            "/Subject": "Routed placement, MicroBlaze block design, and worst setup path",
        }
    )
    with (HERE / "vivado_implementation_composite.pdf").open("wb") as f:
        writer.write(f)


if __name__ == "__main__":
    system_cells, accelerator_cells = read_placed_cells()
    normalize_vivado_vectors()
    build_placement_svg(system_cells, accelerator_cells)
    build_placement_pdf(system_cells, accelerator_cells)
    build_pdf_package()
    print("Screenshot-free Vivado vector publication assets generated")
