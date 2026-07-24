"""Compose two direct Vivado exports into one publication inset figure.

The source schematics are not redrawn. Figure A is used as the top-level
overview and Figure B as the expanded view of the real ``u_snapshot`` RTL
hierarchy. Only panel borders, labels, and the expansion arrow are added.
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


REPOSITORY = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPOSITORY / "vivado" / "pure_rtl" / "evidence"
FIGURE_A_PDF = ARTIFACT_DIR / "FIG-RTL-A_top_hierarchy.pdf"
FIGURE_A_PNG = ARTIFACT_DIR / "FIG-RTL-A_top_hierarchy.png"
FIGURE_B_PDF = ARTIFACT_DIR / "FIG-RTL-B_snapshot_core_hierarchy.pdf"
FIGURE_B_PNG = ARTIFACT_DIR / "FIG-RTL-B_snapshot_core_hierarchy.png"
OUTPUT_PDF = ARTIFACT_DIR / "FIG-RTL-AB_top_with_snapshot_expansion.pdf"


def content_box(png_path: Path, pdf_width: float, pdf_height: float) -> tuple[float, float, float, float]:
    image = Image.open(png_path).convert("RGB")
    difference = ImageChops.difference(image, Image.new("RGB", image.size, "white"))
    bbox = difference.getbbox()
    if bbox is None:
        raise RuntimeError(f"No non-white schematic content found in {png_path}")
    left, top, right, bottom = bbox
    margin_px = max(12, int(min(image.size) * 0.012))
    left = max(0, left - margin_px)
    top = max(0, top - margin_px)
    right = min(image.width, right + margin_px)
    bottom = min(image.height, bottom + margin_px)
    return (
        left / image.width * pdf_width,
        (image.height - bottom) / image.height * pdf_height,
        right / image.width * pdf_width,
        (image.height - top) / image.height * pdf_height,
    )


def place_pdf(
    destination: PageObject,
    source_pdf: Path,
    source_png: Path,
    panel: tuple[float, float, float, float],
) -> None:
    source = PdfReader(str(source_pdf)).pages[0]
    width = float(source.mediabox.width)
    height = float(source.mediabox.height)
    left, bottom, right, top = content_box(source_png, width, height)
    source.cropbox.lower_left = (left, bottom)
    source.cropbox.upper_right = (right, top)
    source.trimbox.lower_left = (left, bottom)
    source.trimbox.upper_right = (right, top)
    content_width = right - left
    content_height = top - bottom
    panel_x, panel_y, panel_width, panel_height = panel
    scale = min(panel_width / content_width, panel_height / content_height)
    x = panel_x + (panel_width - content_width * scale) / 2 - left * scale
    y = panel_y + (panel_height - content_height * scale) / 2 - bottom * scale
    transform = Transformation().scale(scale).translate(x, y)
    destination.merge_transformed_page(source, transform, expand=False, over=True)


def decoration_page(page_width: float, page_height: float) -> PageObject:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    pdf.setStrokeColorRGB(0.55, 0.59, 0.64)
    pdf.setLineWidth(0.8)
    pdf.roundRect(24, 500, page_width - 48, 280, 6, fill=0, stroke=1)
    pdf.roundRect(24, 50, page_width - 48, 410, 6, fill=0, stroke=1)

    pdf.setFillColorRGB(0.08, 0.12, 0.18)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(24, page_height - 25, "Pure RTL top hierarchy with expanded Snapshot core")
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, 754, "(a) snn_ecg_30min_final_top")
    pdf.drawString(36, 434, "(b) Expanded u_snapshot: snn_ecg_3feat_top")

    pdf.setStrokeColorRGB(0.16, 0.38, 0.68)
    pdf.setFillColorRGB(0.16, 0.38, 0.68)
    pdf.setLineWidth(1.4)
    arrow_x = page_width / 2
    pdf.line(arrow_x, 494, arrow_x, 466)
    pdf.line(arrow_x, 466, arrow_x - 4, 473)
    pdf.line(arrow_x, 466, arrow_x + 4, 473)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(arrow_x + 8, 477, "u_snapshot expanded below")

    pdf.setFillColorRGB(0.30, 0.33, 0.37)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(
        28,
        28,
        "Both panels are direct Vivado RTL Elaborated Schematic exports; only panel layout and the expansion callout were added.",
    )
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdftoppm", help="Path to Poppler pdftoppm executable")
    parser.add_argument("--dpi", type=int, default=240)
    args = parser.parse_args()

    for path in (FIGURE_A_PDF, FIGURE_A_PNG, FIGURE_B_PDF, FIGURE_B_PNG):
        if not path.is_file():
            raise FileNotFoundError(path)

    page_width, page_height = A4
    destination = decoration_page(page_width, page_height)
    place_pdf(destination, FIGURE_A_PDF, FIGURE_A_PNG, (40, 518, page_width - 80, 210))
    place_pdf(destination, FIGURE_B_PDF, FIGURE_B_PNG, (40, 72, page_width - 80, 340))

    writer = PdfWriter()
    writer.add_page(destination)
    with OUTPUT_PDF.open("wb") as handle:
        writer.write(handle)

    pdftoppm = args.pdftoppm or shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm is required to render the PNG preview")
    subprocess.run(
        [
            pdftoppm,
            "-png",
            "-r",
            str(args.dpi),
            "-singlefile",
            str(OUTPUT_PDF),
            str(OUTPUT_PDF.with_suffix("")),
        ],
        check=True,
    )
    print(f"PASS {OUTPUT_PDF.name}")
    print(f"PASS {OUTPUT_PDF.with_suffix('.png').name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
