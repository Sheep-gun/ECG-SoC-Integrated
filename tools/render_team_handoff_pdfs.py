#!/usr/bin/env python3
"""Render the two AF-normalized team-handoff Markdown files as Korean PDFs."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "components" / "afe_xmodel" / "docs" / "team_handoff"
SOURCES = [
    HANDOFF / "ECG_SoC_알고리즘팀_전달.md",
    HANDOFF / "ECG_SoC_팀전달_통합검증.md",
]
FONT_DIR = Path(r"C:\Windows\Fonts")
FONT_REGULAR = FONT_DIR / "malgun.ttf"
FONT_BOLD = FONT_DIR / "malgunbd.ttf"
PAGE_WIDTH = A4[0] - 34 * mm


def register_fonts() -> None:
    if not FONT_REGULAR.is_file() or not FONT_BOLD.is_file():
        raise FileNotFoundError("Malgun Gothic fonts are required in C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("Malgun", str(FONT_REGULAR)))
    pdfmetrics.registerFont(TTFont("Malgun-Bold", str(FONT_BOLD)))
    pdfmetrics.registerFontFamily(
        "Malgun",
        normal="Malgun",
        bold="Malgun-Bold",
        italic="Malgun",
        boldItalic="Malgun-Bold",
    )


def clean_text(value: str) -> str:
    return (
        value.replace("\u2011", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00a0", " ")
    )


def inline_markup(value: str, *, break_paths: bool = False) -> str:
    value = clean_text(value.strip())
    if break_paths:
        value = value.replace("/", "/\u200b").replace("_", "_\u200b")
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`(.+?)`", r"<font color='#234a75'>\1</font>", value)
    return value


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleKR",
            parent=base["Title"],
            fontName="Malgun-Bold",
            fontSize=18,
            leading=26,
            textColor=colors.HexColor("#17365D"),
            alignment=TA_CENTER,
            spaceAfter=9 * mm,
        ),
        "h2": ParagraphStyle(
            "H2KR",
            parent=base["Heading2"],
            fontName="Malgun-Bold",
            fontSize=13,
            leading=19,
            textColor=colors.HexColor("#1F4E79"),
            spaceBefore=5 * mm,
            spaceAfter=2.2 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3KR",
            parent=base["Heading3"],
            fontName="Malgun-Bold",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor("#385D8A"),
            spaceBefore=3.2 * mm,
            spaceAfter=1.6 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyKR",
            parent=base["BodyText"],
            fontName="Malgun",
            fontSize=9.2,
            leading=14.7,
            textColor=colors.HexColor("#20262E"),
            wordWrap="CJK",
            spaceAfter=1.8 * mm,
        ),
        "bullet": ParagraphStyle(
            "BulletKR",
            parent=base["BodyText"],
            fontName="Malgun",
            fontSize=9.1,
            leading=14.4,
            leftIndent=5 * mm,
            firstLineIndent=-3 * mm,
            wordWrap="CJK",
            spaceAfter=1.2 * mm,
        ),
        "quote": ParagraphStyle(
            "QuoteKR",
            parent=base["BodyText"],
            fontName="Malgun",
            fontSize=8.8,
            leading=14,
            leftIndent=6 * mm,
            rightIndent=4 * mm,
            borderColor=colors.HexColor("#9DB2C8"),
            borderWidth=0,
            borderLeft=2,
            borderPadding=4,
            backColor=colors.HexColor("#F4F7FA"),
            wordWrap="CJK",
            spaceAfter=2 * mm,
        ),
        "table": ParagraphStyle(
            "TableKR",
            parent=base["BodyText"],
            fontName="Malgun",
            fontSize=7.2,
            leading=10.6,
            wordWrap="CJK",
        ),
        "table_head": ParagraphStyle(
            "TableHeadKR",
            parent=base["BodyText"],
            fontName="Malgun-Bold",
            fontSize=7.3,
            leading=10.8,
            textColor=colors.white,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "CodeKR",
            parent=base["BodyText"],
            fontName="Malgun",
            fontSize=7.6,
            leading=11.2,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            backColor=colors.HexColor("#F1F3F5"),
            borderPadding=5,
            wordWrap="CJK",
            spaceAfter=2 * mm,
        ),
    }


def is_separator(row: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row)


def table_flowable(rows: list[list[str]], style: dict[str, ParagraphStyle]) -> LongTable:
    rows = [row for row in rows if not is_separator(row)]
    column_count = max(len(row) for row in rows)
    rows = [row + [""] * (column_count - len(row)) for row in rows]
    weights = []
    for index in range(column_count):
        longest = max(len(clean_text(row[index])) for row in rows)
        weights.append(min(max(longest, 12), 42))
    scale = PAGE_WIDTH / sum(weights)
    widths = [weight * scale for weight in weights]
    data = []
    for row_index, row in enumerate(rows):
        paragraph_style = style["table_head"] if row_index == 0 else style["table"]
        data.append(
            [Paragraph(inline_markup(cell, break_paths=True), paragraph_style) for cell in row]
        )
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#355E86")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4CF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
            ]
        )
    )
    return table


def markdown_story(source: Path, style: dict[str, ParagraphStyle]) -> list[object]:
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    story: list[object] = []
    index = 0
    code_mode = False
    code_lines: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            story.append(Paragraph(inline_markup(" ".join(paragraph_lines)), style["body"]))
            paragraph_lines.clear()

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            if code_mode:
                rendered_lines = [inline_markup(line, break_paths=True) for line in code_lines]
                story.append(Paragraph("<br/>".join(rendered_lines), style["code"]))
                code_lines.clear()
            code_mode = not code_mode
            index += 1
            continue
        if code_mode:
            code_lines.append(raw)
            index += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            table_rows: list[list[str]] = []
            while index < len(lines):
                candidate = lines[index].strip()
                if not (candidate.startswith("|") and candidate.endswith("|")):
                    break
                table_rows.append([cell.strip() for cell in candidate.strip("|").split("|")])
                index += 1
            story.extend([table_flowable(table_rows, style), Spacer(1, 2.2 * mm)])
            continue
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped in {"---", "***"}:
            flush_paragraph()
            story.append(Spacer(1, 2 * mm))
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            if story:
                story.append(PageBreak())
            story.append(Paragraph(inline_markup(stripped[2:]), style["title"]))
        elif stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:]), style["h2"]))
        elif stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:]), style["h3"]))
        elif stripped.startswith(">"):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped.lstrip("> ")), style["quote"]))
        elif re.match(r"^[-*] ", stripped):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), style["bullet"], bulletText="-"))
        elif re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            number, text = stripped.split(". ", 1)
            story.append(Paragraph(inline_markup(text), style["bullet"], bulletText=f"{number}."))
        else:
            paragraph_lines.append(stripped)
        index += 1
    flush_paragraph()
    return story


def footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7DEE5"))
    canvas.setLineWidth(0.4)
    canvas.line(17 * mm, 14 * mm, A4[0] - 17 * mm, 14 * mm)
    canvas.setFont("Malgun", 7.5)
    canvas.setFillColor(colors.HexColor("#647280"))
    canvas.drawString(17 * mm, 9.5 * mm, "ECG SoC team handoff - AF class-label normalized")
    canvas.drawRightString(A4[0] - 17 * mm, 9.5 * mm, f"{document.page}")
    canvas.restoreState()


def render(source: Path) -> Path:
    output = source.with_suffix(".pdf")
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title=source.stem,
        author="ECG SoC Team",
        subject="AF-normalized team handoff evidence",
    )
    document.build(markdown_story(source, styles()), onFirstPage=footer, onLaterPages=footer)
    return output


def main() -> int:
    register_fonts()
    for source in SOURCES:
        output = render(source)
        print(f"PASS {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
