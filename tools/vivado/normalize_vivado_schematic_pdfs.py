"""Normalize Vivado schematic PDF rotation and render faithful PNG previews.

Vivado 2020.2 writes vector PDFs with page-rotation metadata. Some renderers
display those pages vertically even when ``-orientation landscape`` was used.
This utility removes only that metadata rotation; it does not redraw, relabel,
or alter the Vivado schematic geometry.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter


REPOSITORY = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPOSITORY / "artifacts" / "rtl_elaborated_schematic"
DEFAULT_PDFS = (
    ARTIFACT_DIR / "FIG-RTL-A_top_hierarchy.pdf",
    ARTIFACT_DIR / "FIG-RTL-B_snapshot_core_hierarchy.pdf",
)


def normalize_rotation(pdf_path: Path) -> int:
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) != 1:
        raise RuntimeError(f"Expected a one-page schematic PDF: {pdf_path}")
    page = reader.pages[0]
    original_rotation = int(page.rotation or 0) % 360
    if original_rotation:
        page.rotate((360 - original_rotation) % 360)

    writer = PdfWriter()
    writer.add_page(page)
    with tempfile.NamedTemporaryFile(
        dir=pdf_path.parent, suffix=".pdf", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with temporary_path.open("wb") as handle:
            writer.write(handle)
        temporary_path.replace(pdf_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return original_rotation


def render_png(pdf_path: Path, pdftoppm: str, dpi: int) -> Path:
    output_base = pdf_path.with_suffix("")
    subprocess.run(
        [
            pdftoppm,
            "-png",
            "-r",
            str(dpi),
            "-singlefile",
            str(pdf_path),
            str(output_base),
        ],
        check=True,
    )
    return output_base.with_suffix(".png")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="*", type=Path, default=list(DEFAULT_PDFS))
    parser.add_argument("--pdftoppm", help="Path to Poppler pdftoppm executable")
    parser.add_argument("--dpi", type=int, default=240)
    args = parser.parse_args()

    pdftoppm = args.pdftoppm or shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm is required to render the PNG previews")

    for pdf_path in args.pdf:
        resolved = pdf_path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        rotation = normalize_rotation(resolved)
        png_path = render_png(resolved, pdftoppm, args.dpi)
        print(f"PASS {resolved.name}: removed rotation={rotation}; PNG={png_path.name}")

    status_path = ARTIFACT_DIR / "automatic_export_status.txt"
    status_lines = status_path.read_text(encoding="utf-8").splitlines()
    status_lines = [
        line
        for line in status_lines
        if not line.startswith(("PDF_PAGE_ROTATION_NORMALIZED=", "PNG_FROM_VIVADO_PDF="))
    ]
    status_lines.extend(
        ["PDF_PAGE_ROTATION_NORMALIZED=PASS", "PNG_FROM_VIVADO_PDF=PASS"]
    )
    status_path.write_text("\n".join(status_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
