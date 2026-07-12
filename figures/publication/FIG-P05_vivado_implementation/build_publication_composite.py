#!/usr/bin/env python3
"""Build publication assets only from Vivado exports and fixed reports."""

from __future__ import annotations

import base64
import csv
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def parse_hierarchy() -> list[dict[str, object]]:
    rows = []
    for line in (HERE / "hierarchical_utilization.rpt").read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|") or "Total LUTs" in line:
            continue
        fields = [item.strip() for item in line.strip().strip("|").split("|")]
        if len(fields) != 10 or not fields[2].isdigit():
            continue
        instance, module = fields[0], fields[1]
        rows.append(
            {
                "instance": instance,
                "module": module,
                "lut": int(fields[2]),
                "ff": int(fields[6]),
                "ramb36": int(fields[7]),
                "ramb18": int(fields[8]),
                "dsp": int(fields[9]),
            }
        )

    selectors = [
        ("MicroBlaze system", lambda r: r["instance"] == "snn_ecg_mb_full_replay_i"),
        ("MicroBlaze processor", lambda r: r["instance"] == "microblaze_0" and r["module"].endswith("microblaze_0_0")),
        ("AXI sample feeder", lambda r: r["instance"] == "sample_feeder_0"),
        ("SNN accelerator AXI wrapper", lambda r: r["instance"] == "snn_ecg_axi_accelerator_0"),
        ("Pure classifier core in system", lambda r: "snn_ecg_30min_final_top" in r["module"] and r["instance"] == "u_core"),
        ("60 s Snapshot hierarchy", lambda r: "snn_ecg_3feat_top" in r["module"] and r["instance"] == "u_snapshot"),
        ("Final Membrane hierarchy", lambda r: "final_membrane_layer" in r["module"] and r["instance"] == "u_final"),
    ]
    selected = []
    for label, selector in selectors:
        match = next((row for row in rows if selector(row)), None)
        if match is None:
            raise RuntimeError(f"Hierarchy row not found: {label}")
        selected.append({"scope": "MicroBlaze integrated post-route", "hierarchy": label, **match})

    metrics = json.loads((REPO / "components/digital_accelerator/reports/final/final_metrics.json").read_text(encoding="utf-8"))
    pure = metrics["pure_rtl_vivado"]
    selected.append(
        {
            "scope": "Fixed standalone pure RTL reference",
            "hierarchy": "Pure RTL accelerator total",
            "instance": "standalone implemented design",
            "module": "snn_ecg_30min_final_top",
            "lut": pure["lut"],
            "ff": pure["ff"],
            "ramb36": pure["bram"],
            "ramb18": 0,
            "dsp": pure["dsp"],
        }
    )
    with (HERE / "hierarchical_utilization.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["scope", "hierarchy", "instance", "module", "LUT", "FF", "BRAM_36K_equivalent", "DSP", "WNS_ns", "claim_note"])
        for row in selected:
            bram = row["ramb36"] + row["ramb18"] / 2
            if row["scope"].startswith("Fixed"):
                wns, note = pure["wns_ns"], "Fixed pure RTL claim; not MicroBlaze system timing"
            elif row["hierarchy"] == "MicroBlaze system":
                wns, note = metrics["microblaze_full_replay_system"]["setup_wns_ns"], "Reproduced integrated-system post-route scope"
            else:
                wns, note = "", "Hierarchical resources within integrated-system run"
            writer.writerow([row["scope"], row["hierarchy"], row["instance"], row["module"], row["lut"], row["ff"], f"{bram:g}", row["dsp"], wns, note])
    return selected


def orient_and_crop_images() -> None:
    bd = Image.open(HERE / "microblaze_block_design.png").convert("RGB")
    if bd.height > bd.width:
        bd = bd.rotate(270, expand=True)
    gray = bd.convert("L")
    content = ImageOps.invert(gray).point(lambda p: 255 if p > 18 else 0)
    bbox = content.getbbox()
    if bbox:
        pad = 40
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(bd.width, bbox[2] + pad), min(bd.height, bbox[3] + pad))
        bd = bd.crop(bbox)
    bd.save(HERE / "microblaze_block_design.png", quality=95)

    zoom = Image.open(HERE / "device_view_accelerator_zoom.png").convert("RGB")
    # Deterministic crop of the actual Vivado Device View. No placement data is
    # synthesized; the crop merely enlarges the highlighted fabric region.
    if zoom.width > zoom.height:
        left = int(zoom.width * 0.77)
        top = int(zoom.height * 0.27)
        zoom = zoom.crop((left, top, zoom.width, zoom.height))
        zoom = zoom.resize((zoom.width * 2, zoom.height * 2), Image.Resampling.LANCZOS)
    zoom.save(HERE / "device_view_accelerator_zoom.png")


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def image_panel_svg(label: str, path: Path, x: int, y: int, w: int, h: int) -> str:
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    rw, rh = iw * scale, ih * scale
    rx, ry = x + (w - rw) / 2, y + 34 + (h - 34 - rh) / 2
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#ffffff" stroke="#cbd5e1"/>'
        f'<text x="{x + 16}" y="{y + 25}" class="panel">{label}</text>'
        f'<image x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" href="{data_uri(path)}" preserveAspectRatio="xMidYMid meet"/>'
    )


def build_svg() -> None:
    full = HERE / "device_view_full.png"
    bd = HERE / "microblaze_block_design.png"
    timing = HERE / "worst_setup_path.png"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120">',
        '<style>.title{font:700 28px "Malgun Gothic",sans-serif;fill:#0f172a}.panel{font:700 19px "Malgun Gothic",sans-serif;fill:#0f172a}.body{font:15px "Malgun Gothic",sans-serif;fill:#1e293b}.small{font:13px "Malgun Gothic",sans-serif;fill:#475569}.head{font:700 14px "Malgun Gothic",sans-serif;fill:#fff}</style>',
        '<rect width="1600" height="1120" fill="#f8fafc"/>',
        '<text x="40" y="42" class="title">Vivado FPGA 구현 결과: 배치·배선, 시스템 연결, timing path와 자원</text>',
        image_panel_svg("(a) Post-route Device View", full, 40, 65, 740, 480),
        image_panel_svg("(b) MicroBlaze IP Integrator Block Design", bd, 820, 65, 740, 480),
        image_panel_svg("(c) Worst Setup Timing Path (Vivado Schematic)", timing, 40, 570, 900, 500),
        '<rect x="980" y="570" width="580" height="500" rx="12" fill="#ffffff" stroke="#cbd5e1"/>',
        '<text x="996" y="595" class="panel">(d) Resource / Timing Summary</text>',
        '<rect x="1000" y="620" width="540" height="34" fill="#334155"/>',
        '<text x="1012" y="643" class="head">Scope</text><text x="1285" y="643" class="head">LUT</text><text x="1360" y="643" class="head">FF</text><text x="1430" y="643" class="head">BRAM</text><text x="1500" y="643" class="head">DSP</text>',
    ]
    table = [
        ("Pure RTL fixed", "9,719", "5,038", "0", "0"),
        ("MicroBlaze system", "12,494", "8,494", "16", "3"),
        ("SNN AXI wrapper", "10,485", "6,652", "0", "0"),
        ("Classifier core in system", "9,712", "5,789", "0", "0"),
        ("Snapshot hierarchy", "7,689", "3,565", "0", "0"),
        ("Final Membrane", "1,798", "1,042", "0", "0"),
    ]
    for i, row in enumerate(table):
        y = 680 + i * 42
        fill = "#f1f5f9" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="1000" y="{y-25}" width="540" height="42" fill="{fill}"/>')
        parts.append(f'<text x="1012" y="{y}" class="body">{row[0]}</text><text x="1285" y="{y}" class="body">{row[1]}</text><text x="1360" y="{y}" class="body">{row[2]}</text><text x="1438" y="{y}" class="body">{row[3]}</text><text x="1510" y="{y}" class="body">{row[4]}</text>')
    parts.extend(
        [
            '<text x="1010" y="948" class="body">Pure RTL fixed WNS: 8.184 ns</text>',
            '<text x="1010" y="978" class="body">MicroBlaze system WNS: 0.097 ns</text>',
            '<text x="1010" y="1010" class="small">두 WNS는 서로 다른 구현 범위이며 처리 지연시간이 아니다.</text>',
            '<text x="1010" y="1035" class="small">Device View는 FPGA placement/routing이며 ASIC layout이 아니다.</text>',
            '<text x="40" y="1100" class="small">Vivado 2020.2 · xc7a100tcsg324-1 · 실제 routed checkpoint 및 고정 보고서 기반</text>',
            '</svg>',
        ]
    )
    (HERE / "vivado_implementation_composite.svg").write_text("".join(parts), encoding="utf-8")


def fit_image(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    rw, rh = iw * scale, ih * scale
    c.drawImage(str(path), x + (w - rw) / 2, y + (h - rh) / 2, rw, rh, preserveAspectRatio=True, mask="auto")


def build_pdf() -> None:
    font = Path("C:/Windows/Fonts/malgun.ttf")
    bold = Path("C:/Windows/Fonts/malgunbd.ttf")
    pdfmetrics.registerFont(TTFont("Malgun", str(font)))
    pdfmetrics.registerFont(TTFont("MalgunB", str(bold)))
    page = landscape(A4)
    c = canvas.Canvas(str(HERE / "vivado_implementation_composite.pdf"), pagesize=page)
    W, H = page
    c.setFillColorRGB(0.973, 0.98, 0.988)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColorRGB(0.06, 0.09, 0.16)
    c.setFont("MalgunB", 15)
    c.drawString(22, H - 24, "Vivado FPGA 구현 결과: 배치·배선, 시스템 연결, timing path와 자원")
    panels = [
        ("(a) Post-route Device View", HERE / "device_view_full.png", 22, H / 2 + 10, 380, 250),
        ("(b) MicroBlaze IP Integrator Block Design", HERE / "microblaze_block_design.png", 430, H / 2 + 10, 390, 250),
        ("(c) Worst Setup Timing Path", HERE / "worst_setup_path.png", 22, 40, 480, 245),
    ]
    for title, path, x, y, w, h in panels:
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
        c.setFillColorRGB(0.06, 0.09, 0.16)
        c.setFont("MalgunB", 10)
        c.drawString(x + 8, y + h - 14, title)
        fit_image(c, path, x + 7, y + 7, w - 14, h - 28)
    x, y, w, h = 525, 40, 295, 245
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
    c.setFillColorRGB(0.06, 0.09, 0.16)
    c.setFont("MalgunB", 10)
    c.drawString(x + 8, y + h - 14, "(d) Resource / Timing Summary")
    c.setFont("Malgun", 8)
    lines = [
        "Pure RTL fixed: 9,719 LUT / 5,038 FF / 0 BRAM / 0 DSP",
        "Pure RTL fixed WNS: 8.184 ns",
        "MicroBlaze system: 12,494 LUT / 8,494 FF / 16 BRAM / 3 DSP",
        "MicroBlaze system WNS: 0.097 ns",
        "SNN AXI wrapper: 10,485 LUT / 6,652 FF / 0 BRAM / 0 DSP",
        "Classifier core in system: 9,712 LUT / 5,789 FF",
        "Worst path: 9.810 ns / requirement 10.000 ns / slack 0.097 ns",
        "주의: 두 WNS는 서로 다른 구현 범위이며 처리 지연시간이 아니다.",
        "Device View는 FPGA placement/routing이며 ASIC layout이 아니다.",
    ]
    yy = y + h - 36
    for line in lines:
        c.drawString(x + 10, yy, line)
        yy -= 20
    c.save()


if __name__ == "__main__":
    parse_hierarchy()
    orient_and_crop_images()
    build_svg()
    build_pdf()
    print("P05 publication assets generated")
