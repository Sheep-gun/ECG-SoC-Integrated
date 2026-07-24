"""Generate the publication SVG for the Pure RTL elaborated hierarchy.

The layout is reader-facing, but every displayed instance and handoff signal is
validated against the two Vivado 2020.2 RTL Elaborated Schematic SVG exports
before the figure is written.  The fixed RTL itself is never modified.
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "vivado" / "pure_rtl" / "evidence"
SOURCE_TOP = ARTIFACTS / "FIG-RTL-A_top_hierarchy.svg"
SOURCE_SNAPSHOT = ARTIFACTS / "FIG-RTL-B_snapshot_core_hierarchy.svg"
APPROVED_SVG = ARTIFACTS / "FIG-RTL_top_with_snapshot_expansion_approved.svg"
OUTPUT_SVG = ARTIFACTS / "FIG-RTL_top_with_snapshot_expansion_generated.svg"
OUTPUT_PNG = ARTIFACTS / "FIG-RTL_top_with_snapshot_expansion_generated.png"

FIXED_COMMIT = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
CANVAS_W = 1800
CANVAS_H = 1150

TEXT = "#182230"
MUTED = "#667085"
BORDER = "#98a2b3"
MODULE_FILL = "#eaf2fb"
MODULE_ACCENT = "#2f6fb3"
WIRE = "#2a8b57"
CALLOUT = "#2563a8"


def svg_texts(path: Path) -> set[str]:
    root = ET.parse(path).getroot()
    return {
        "".join(node.itertext()).strip()
        for node in root.iter()
        if node.tag.endswith("text") and "".join(node.itertext()).strip()
    }


def require_source_evidence() -> None:
    top = svg_texts(SOURCE_TOP)
    snapshot = svg_texts(SOURCE_SNAPSHOT)

    required_top = {
        "adc_data[11:0]",
        "u_snapshot",
        "snn_ecg_3feat_top",
        "u_final",
        "final_membrane_layer",
        "class_mem_nsr[63:0]",
        "class_mem_chf[63:0]",
        "class_mem_arr[63:0]",
        "class_mem_aff[63:0]",
        "final_mem_nsr[31:0]",
        "final_mem_chf[31:0]",
        "final_mem_arr[31:0]",
        "final_mem_aff[31:0]",
        "final_pred_class[1:0]",
        "final_valid",
    }
    required_snapshot = {
        "u_event_encoder",
        "ecg_event_encoder_adaptive",
        "u_qrs_detector",
        "qrs_lif_detector",
        "u_dscr",
        "dscr_spike_counter",
        "u_ectopic",
        "ectopic_pair_neuron",
        "u_pnn",
        "pnn_rhythm_predictor",
        "u_ram",
        "ram_peak_accumulator",
        "u_qrs_maf",
        "qrs_maf_neuron",
        "u_rdm",
        "rdm_variability_neuron",
        "u_rbbb_qrs_delay",
        "rbbb_qrs_delay_bank",
        "u_class",
        "class_score_neurons",
        "strong_event",
        "beat_spike",
        "dscr_sign_flip_spike",
        "dscr_valid_slope_spike",
        "ectopic_pair_spike",
        "pnn_match_spike",
        "pnn_mismatch_spike",
        "ram_amp_spike",
        "qrs_maf_valid_spike",
        "rdm_level_spike[14:0]",
        "rbbb_like_beat_spike",
    }
    missing_top = sorted(required_top - top)
    missing_snapshot = sorted(required_snapshot - snapshot)
    if missing_top or missing_snapshot:
        raise RuntimeError(
            "Vivado source evidence mismatch: "
            f"top={missing_top or 'PASS'}, snapshot={missing_snapshot or 'PASS'}"
        )


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def text(x: float, y: float, value: str, size: int, *, weight: int = 400,
         anchor: str = "start", fill: str = TEXT, cls: str = "") -> str:
    class_attr = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{fill}"{class_attr}>{esc(value)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, *, color: str = WIRE,
         width: float = 2.2, marker: bool = False, dash: str = "") -> str:
    marker_attr = ' marker-end="url(#arrow-green)"' if marker else ""
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{width}" fill="none"{marker_attr}{dash_attr}/>'
    )


def path(points: list[tuple[float, float]], *, color: str = WIRE, width: float = 2.2,
         marker: bool = False, dash: str = "") -> str:
    d = "M " + " L ".join(f"{x} {y}" for x, y in points)
    marker_attr = ' marker-end="url(#arrow-green)"' if marker else ""
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
        f'stroke-linejoin="round" stroke-linecap="round"{marker_attr}{dash_attr}/>'
    )


def port(x: float, y: float, *, fill: str = WIRE) -> str:
    return f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="{fill}"/>'


def junction(x: float, y: float) -> str:
    return f'<circle cx="{x}" cy="{y}" r="4.5" fill="{WIRE}"/>'


def module(x: float, y: float, w: float, h: float, instance: str, reference: str,
           *, instance_size: int = 18, reference_size: int = 14) -> str:
    cy = y + h / 2
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="{MODULE_FILL}" stroke="{BORDER}" stroke-width="2"/>',
            f'<rect x="{x+12}" y="{y+12}" width="13" height="13" rx="2" fill="{MODULE_ACCENT}"/>',
            text(x + w / 2, cy - 4, instance, instance_size, weight=700, anchor="middle"),
            text(x + w / 2, cy + 22, reference, reference_size, anchor="middle", fill=MUTED),
        ]
    )


def build_svg() -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" '
        'aria-labelledby="figure-title figure-description">'
    )
    parts.append('<title id="figure-title">Pure RTL top hierarchy with expanded Snapshot core</title>')
    parts.append(
        '<desc id="figure-description">Reader-facing reconstruction of two Vivado RTL Elaborated '
        'Schematic views. The top panel shows snn_ecg_30min_final_top and the lower panel expands '
        'the actual u_snapshot hierarchy.</desc>'
    )
    parts.append(
        f'<metadata>Vivado 2020.2 RTL Elaborated Schematic evidence: '
        f'vivado/pure_rtl/evidence/FIG-RTL-A_top_hierarchy.svg and '
        f'vivado/pure_rtl/evidence/FIG-RTL-B_snapshot_core_hierarchy.svg; '
        f'digital fixed commit {FIXED_COMMIT}; generated by '
        f'tools/vivado/generate_publication_rtl_hierarchy_svg.py</metadata>'
    )
    parts.append(
        '<defs>'
        f'<marker id="arrow-green" markerWidth="10" markerHeight="8" refX="9" refY="4" '
        f'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 Z" fill="{WIRE}"/></marker>'
        f'<marker id="arrow-blue" markerWidth="10" markerHeight="8" refX="9" refY="4" '
        f'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 Z" fill="{CALLOUT}"/></marker>'
        '<style>text{font-family:Arial,Helvetica,sans-serif} .signal{paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}</style>'
        '</defs>'
    )
    parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#ffffff"/>')

    # Overall title and panel frames.
    parts.append(text(45, 54, "Pure RTL top hierarchy with expanded Snapshot core", 32, weight=700))
    parts.append('<rect x="45" y="78" width="1710" height="300" rx="14" fill="#ffffff" stroke="#98a2b3" stroke-width="2"/>')
    parts.append('<rect x="45" y="454" width="1710" height="642" rx="14" fill="#ffffff" stroke="#98a2b3" stroke-width="2"/>')
    parts.append(text(70, 116, "(a) Pure RTL top hierarchy: snn_ecg_30min_final_top", 25, weight=700))
    parts.append(text(70, 494, "(b) Expanded Snapshot core: u_snapshot / snn_ecg_3feat_top", 25, weight=700))

    # Panel (a): the two actual top-level hierarchy instances and their handoff.
    parts.append(module(305, 162, 275, 170, "u_snapshot", "snn_ecg_3feat_top", instance_size=20, reference_size=16))
    parts.append(module(860, 146, 300, 202, "u_final", "final_membrane_layer", instance_size=20, reference_size=16))

    parts.append('<rect x="86" y="218" width="150" height="62" rx="8" fill="#ffffff" stroke="#98a2b3" stroke-width="2"/>')
    parts.append(text(161, 255, "adc_data[11:0]", 16, weight=700, anchor="middle"))
    parts.append(line(236, 249, 305, 249, marker=True))

    class_signals = [
        (190, "class_mem_nsr[63:0]"),
        (228, "class_mem_chf[63:0]"),
        (266, "class_mem_arr[63:0]"),
        (304, "class_mem_aff[63:0]"),
    ]
    for y, label in class_signals:
        parts.append(port(580, y))
        parts.append(line(580, y, 860, y, marker=True))
        parts.append(text(720, y - 8, label, 14, weight=600, anchor="middle", cls="signal"))
        parts.append(port(860, y))

    outputs = [
        (174, "final_mem_nsr[31:0]"),
        (205, "final_mem_chf[31:0]"),
        (236, "final_mem_arr[31:0]"),
        (267, "final_mem_aff[31:0]"),
        (306, "final_pred_class[1:0]"),
        (335, "final_valid"),
    ]
    for y, label in outputs:
        parts.append(port(1160, y))
        parts.append(line(1160, y, 1515, y, marker=True))
        parts.append(text(1190, y - 8, label, 15, weight=600, cls="signal"))

    # Expansion callout.
    parts.append(
        f'<path d="M 442 332 L 442 410 L 900 410 L 900 447" stroke="{CALLOUT}" '
        'stroke-width="3" stroke-dasharray="10 7" fill="none" marker-end="url(#arrow-blue)"/>'
    )
    parts.append('<rect x="718" y="388" width="364" height="42" rx="21" fill="#ffffff" stroke="#2563a8" stroke-width="2"/>')
    parts.append(text(900, 416, "u_snapshot expanded below", 17, weight=700, anchor="middle", fill=CALLOUT))

    # Panel (b): actual elaborated instances. The feature blocks are vertically
    # aligned so every displayed output can retain a separate real handoff net.
    parts.append(module(82, 748, 225, 94, "u_event_encoder", "ecg_event_encoder_adaptive"))
    parts.append(module(355, 748, 210, 94, "u_qrs_detector", "qrs_lif_detector"))

    feature_x = 650
    feature_w = 330
    parts.append(module(feature_x, 520, feature_w, 62, "u_dscr", "dscr_spike_counter"))
    parts.append(module(feature_x, 592, feature_w, 56, "u_ectopic", "ectopic_pair_neuron"))
    parts.append(module(feature_x, 658, feature_w, 72, "u_pnn", "pnn_rhythm_predictor"))
    parts.append(module(feature_x, 740, feature_w, 56, "u_ram", "ram_peak_accumulator"))
    parts.append(module(feature_x, 806, feature_w, 56, "u_qrs_maf", "qrs_maf_neuron"))
    parts.append(module(feature_x, 872, feature_w, 56, "u_rdm", "rdm_variability_neuron"))
    parts.append(module(feature_x, 938, feature_w, 56, "u_rbbb_qrs_delay", "rbbb_qrs_delay_bank"))
    parts.append(module(1450, 510, 265, 494, "u_class", "class_score_neurons", instance_size=20, reference_size=16))

    # Event encoder to QRS detector and two actual fan-out nets.
    strong_y = 788
    beat_y = 818
    parts.append(port(307, strong_y))
    parts.append(line(307, strong_y, 355, strong_y, marker=True))
    parts.append(port(355, strong_y))
    parts.append(port(565, beat_y))

    # strong_event fan-out: qrs_lif_detector, qrs_maf_neuron, rbbb_qrs_delay_bank.
    # The fan-out is routed below the two source modules so that no wire passes
    # through a module body or its instance/reference labels.
    parts.append(path([(307, strong_y), (330, strong_y), (330, 1024), (610, 1024), (610, 826)]))
    parts.append(junction(307, strong_y))
    parts.append(text(470, 1015, "strong_event", 13, weight=600, anchor="middle", cls="signal"))
    parts.append(path([(610, 826), (650, 826)], marker=True))
    parts.append(path([(610, 964), (650, 964)], marker=True))
    parts.append(junction(610, 826))
    parts.append(junction(610, 964))

    # beat_spike fan-out: pnn, ram, and qrs_maf.
    parts.append(path([(565, beat_y), (625, beat_y), (625, 694)]))
    parts.append(text(612, 674, "beat_spike", 13, weight=600, anchor="end", cls="signal"))
    parts.append(path([(625, 694), (650, 694)], marker=True))
    parts.append(path([(625, 768), (650, 768)], marker=True))
    parts.append(path([(625, 844), (650, 844)], marker=True))
    parts.append(junction(625, 694))
    parts.append(junction(625, 768))
    parts.append(junction(625, 844))

    # Feature outputs: independent elaborated handoff nets into u_class.
    feature_outputs = [
        (542, "dscr_sign_flip_spike"),
        (568, "dscr_valid_slope_spike"),
        (620, "ectopic_pair_spike"),
        (682, "pnn_match_spike"),
        (708, "pnn_mismatch_spike"),
        (768, "ram_amp_spike"),
        (834, "qrs_maf_valid_spike"),
        (900, "rdm_level_spike[14:0]"),
        (966, "rbbb_like_beat_spike"),
    ]
    for y, label in feature_outputs:
        parts.append(port(980, y))
        parts.append(line(980, y, 1450, y, marker=True))
        parts.append(text(1215, y - 8, label, 14, weight=600, anchor="middle", cls="signal"))
        parts.append(port(1450, y))

    note = (
        "Both panels are reconstructed from Vivado RTL Elaborated Schematic views. Module instances and signal connectivity "
        "follow the elaborated RTL; only layout, scaling, and nonessential signal-label reduction were applied."
    )
    parts.append(text(48, 1131, note, 15, fill=MUTED))
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render_png(chrome: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="ecg-rtl-svg-render-") as profile:
        command = [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--window-size={CANVAS_W},{CANVAS_H}",
            f"--user-data-dir={profile}",
            f"--screenshot={OUTPUT_PNG}",
            OUTPUT_SVG.resolve().as_uri(),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def validate_output() -> None:
    root = ET.parse(OUTPUT_SVG).getroot()
    if root.attrib.get("viewBox") != f"0 0 {CANVAS_W} {CANVAS_H}":
        raise RuntimeError("Unexpected SVG viewBox")
    data = OUTPUT_SVG.read_text(encoding="utf-8")
    required = [
        "u_snapshot",
        "u_final",
        "u_event_encoder",
        "u_qrs_detector",
        "u_dscr",
        "u_ectopic",
        "u_pnn",
        "u_ram",
        "u_qrs_maf",
        "u_rdm",
        "u_rbbb_qrs_delay",
        "u_class",
        "strong_event",
        "beat_spike",
        "final_pred_class[1:0]",
        "final_valid",
    ]
    missing = [value for value in required if value not in data]
    forbidden = [value for value in ("MicroBlaze", "AXI interconnect", "CARRY4", "LUT6") if value in data]
    if missing or forbidden:
        raise RuntimeError(f"Output validation failed: missing={missing}, forbidden={forbidden}")
    if "rotate(" in data:
        raise RuntimeError("Vertical or rotated labels are not allowed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chrome", type=Path, help="Chrome/Edge executable for the 2x PNG preview")
    parser.add_argument("--skip-png", action="store_true")
    parser.add_argument(
        "--reconstruct",
        action="store_true",
        help="Rebuild the reader-facing SVG instead of installing the approved Inkscape-edited master",
    )
    args = parser.parse_args()

    require_source_evidence()
    OUTPUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    if APPROVED_SVG.is_file() and not args.reconstruct:
        shutil.copyfile(APPROVED_SVG, OUTPUT_SVG)
        print(f"PASS approved SVG installed: {APPROVED_SVG.relative_to(ROOT)}")
    else:
        OUTPUT_SVG.write_text(build_svg(), encoding="utf-8", newline="\n")
        print("PASS reader-facing SVG reconstructed from elaboration evidence")
    validate_output()

    if not args.skip_png:
        chrome = args.chrome or Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        if not chrome.is_file():
            raise FileNotFoundError(f"Chrome/Edge renderer not found: {chrome}")
        render_png(chrome)

    print(f"PASS source validation: {SOURCE_TOP.relative_to(ROOT)}")
    print(f"PASS source validation: {SOURCE_SNAPSHOT.relative_to(ROOT)}")
    print(f"PASS SVG: {OUTPUT_SVG.relative_to(ROOT)}")
    if not args.skip_png:
        print(f"PASS PNG: {OUTPUT_PNG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
