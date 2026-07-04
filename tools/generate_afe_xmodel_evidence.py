from __future__ import annotations

import argparse
import json
import math
import zlib
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw

from award_readiness_common import DATASET, FIGURES, REPORTS, write_json


COLORS = {
    "blue": (32, 96, 180),
    "red": (190, 60, 45),
    "green": (40, 140, 85),
    "orange": (220, 140, 35),
    "purple": (120, 80, 180),
    "gray": (90, 90, 90),
    "grid": (224, 224, 224),
    "axis": (40, 40, 40),
}


def read_signed_mem(path: Path, max_samples: int | None = None) -> np.ndarray:
    values: list[int] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            token = line.strip().split()[0] if line.strip() else ""
            if not token:
                continue
            raw = int(token, 16)
            if raw >= 0x800:
                raw -= 0x1000
            values.append(raw)
            if max_samples is not None and len(values) >= max_samples:
                break
    return np.asarray(values, dtype=float)


def find_chunk(dataset_root: Path, split: str, class_label: str, record_id: str | None) -> Path:
    root = dataset_root / split / class_label
    if record_id:
        candidates = sorted((root / record_id).glob("*.mem"))
    else:
        candidates = sorted(root.glob("*/*.mem"))
    if not candidates:
        raise FileNotFoundError(f"no .mem chunk found under {root}")
    return candidates[0]


def first_order_lowpass(x: np.ndarray, fs: float, fc: float) -> np.ndarray:
    dt = 1.0 / fs
    rc = 1.0 / (2.0 * math.pi * fc)
    alpha = dt / (rc + dt)
    y = np.zeros_like(x)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = y[i - 1] + alpha * (x[i] - y[i - 1])
    return y


def first_order_highpass(x: np.ndarray, fs: float, fc: float) -> np.ndarray:
    dt = 1.0 / fs
    rc = 1.0 / (2.0 * math.pi * fc)
    alpha = rc / (rc + dt)
    y = np.zeros_like(x)
    for i in range(1, len(x)):
        y[i] = alpha * (y[i - 1] + x[i] - x[i - 1])
    return y


def notch_60(x: np.ndarray, fs: float, f0: float = 60.0, q: float = 5.0) -> np.ndarray:
    w0 = 2.0 * math.pi * f0 / fs
    alpha = math.sin(w0) / (2.0 * q)
    b0, b1, b2 = 1.0, -2.0 * math.cos(w0), 1.0
    a0, a1, a2 = 1.0 + alpha, -2.0 * math.cos(w0), 1.0 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, sample in enumerate(x):
        out = b0 * sample + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        y[i] = out
        x2, x1 = x1, sample
        y2, y1 = y1, out
    return y


def nominal_afe(vin: np.ndarray, fs: float) -> dict[str, np.ndarray]:
    hpf = first_order_highpass(vin, fs, 0.482)
    gained = hpf * 201.0
    notched = notch_60(gained, fs)
    lpf = first_order_lowpass(notched, fs, 150.0)
    return {"vin": vin, "hpf": hpf, "gain": gained, "notch": notched, "lpf": lpf}


def quantize_adc(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    clipped = np.clip(v, -1.65, 1.65)
    unsigned = np.rint((clipped + 1.65) / 3.3 * 4095.0).astype(int)
    signed = unsigned - 2048
    return unsigned, signed


def draw_plot(path: Path, title: str, xs: np.ndarray, series: list[tuple[str, np.ndarray, tuple[int, int, int]]]) -> None:
    width, height = 1100, 620
    left, right, top, bottom = 86, 30, 58, 70
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    plot_w = width - left - right
    plot_h = height - top - bottom
    draw.text((left, 18), title, fill=COLORS["axis"])

    vals = np.concatenate([np.asarray(y, dtype=float) for _, y, _ in series])
    finite = vals[np.isfinite(vals)]
    ymin, ymax = float(np.min(finite)), float(np.max(finite))
    if ymin == ymax:
        ymin -= 1.0
        ymax += 1.0
    pad = (ymax - ymin) * 0.08
    ymin -= pad
    ymax += pad
    xmin, xmax = float(xs[0]), float(xs[-1])

    for i in range(6):
        y = top + int(plot_h * i / 5)
        draw.line((left, y, width - right, y), fill=COLORS["grid"])
        label = ymax - (ymax - ymin) * i / 5
        draw.text((8, y - 7), f"{label:.3g}", fill=COLORS["gray"])
    for i in range(6):
        x = left + int(plot_w * i / 5)
        draw.line((x, top, x, height - bottom), fill=COLORS["grid"])
        label = xmin + (xmax - xmin) * i / 5
        draw.text((x - 20, height - bottom + 10), f"{label:.2f}", fill=COLORS["gray"])
    draw.rectangle((left, top, width - right, height - bottom), outline=COLORS["axis"])

    def map_point(xv: float, yv: float) -> tuple[int, int]:
        x = left + int((xv - xmin) / (xmax - xmin) * plot_w) if xmax != xmin else left
        y = top + int((ymax - yv) / (ymax - ymin) * plot_h)
        return x, y

    step = max(1, len(xs) // 1400)
    legend_x = left + 10
    for idx, (name, y, color) in enumerate(series):
        points = [map_point(float(xs[i]), float(y[i])) for i in range(0, len(xs), step)]
        if len(points) >= 2:
            draw.line(points, fill=color, width=2)
        ly = top + 12 + idx * 18
        draw.line((legend_x, ly + 7, legend_x + 24, ly + 7), fill=color, width=3)
        draw.text((legend_x + 30, ly), name, fill=COLORS["axis"])
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def draw_hist(path: Path, title: str, values: np.ndarray, bins: int = 64) -> None:
    hist, edges = np.histogram(values, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2.0
    draw_plot(path, title, centers, [("count", hist.astype(float), COLORS["purple"])])


def frequency_response(fs: float = 1000.0) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    f = np.linspace(0.1, 500.0, 1400)
    hp = f / np.sqrt(f * f + 0.482 * 0.482)
    lp = 150.0 / np.sqrt(f * f + 150.0 * 150.0)
    # Magnitude of the RBJ notch response on the unit circle.
    f0, q = 60.0, 5.0
    w0 = 2.0 * math.pi * f0 / fs
    alpha = math.sin(w0) / (2.0 * q)
    b = np.array([1.0, -2.0 * math.cos(w0), 1.0]) / (1.0 + alpha)
    a = np.array([1.0, -2.0 * math.cos(w0) / (1.0 + alpha), (1.0 - alpha) / (1.0 + alpha)])
    z = np.exp(-1j * 2.0 * np.pi * f / fs)
    notch = np.abs((b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z))
    total = hp * notch * lp
    return f, {"HPF": hp, "notch": notch, "LPF": lp, "total": total}


def crc32(path: Path) -> str:
    return f"{zlib.crc32(path.read_bytes()) & 0xFFFFFFFF:08x}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AFE+ADC XMODEL evidence figures from available signed 12-bit ECG .mem data.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET)
    parser.add_argument("--split", default="test")
    parser.add_argument("--class-label", default="ARR")
    parser.add_argument("--record-id", default="111")
    parser.add_argument("--chunk-file", type=Path, default=None)
    parser.add_argument("--start-sec", type=float, default=0.0)
    parser.add_argument("--duration-sec", type=float, default=10.0)
    parser.add_argument("--fs", type=float, default=1000.0)
    parser.add_argument("--scale-den", type=float, default=200000.0)
    parser.add_argument("--output-dir", type=Path, default=FIGURES)
    args = parser.parse_args()

    chunk = args.chunk_file or find_chunk(args.dataset_root, args.split, args.class_label, args.record_id)
    start = int(args.start_sec * args.fs)
    count = int(args.duration_sec * args.fs)
    signed = read_signed_mem(chunk, max_samples=start + count)[start : start + count]
    if len(signed) == 0:
        raise RuntimeError(f"no samples loaded from {chunk}")
    t = np.arange(len(signed), dtype=float) / args.fs + args.start_sec
    vin = signed / args.scale_den

    analog_fs = args.fs * 10.0
    analog_t = np.arange(0.0, min(args.duration_sec, len(signed) / args.fs), 1.0 / analog_fs) + args.start_sec
    analog_vin = np.interp(analog_t, t, vin)
    chain = nominal_afe(vin, args.fs)
    unsigned, adc_signed = quantize_adc(chain["lpf"])
    no_afe_unsigned, no_afe_signed = quantize_adc(vin)

    noisy = vin + 0.00035 * np.sin(2.0 * np.pi * 60.0 * t)
    notch_only = notch_60(noisy, args.fs)

    out = args.output_dir
    draw_plot(
        out / "afe_vin_reconstruction.png",
        "Digitized signed .mem samples and PWL-equivalent vin reconstruction",
        analog_t,
        [
            ("PWL vin_v", analog_vin, COLORS["blue"]),
            ("sample hold reference", np.interp(analog_t, t, vin), COLORS["orange"]),
        ],
    )
    draw_plot(
        out / "afe_chain_waveform.png",
        "Nominal AFE chain waveform: vin, HPF, gain, notch, LPF",
        t,
        [
            ("vin_v", chain["vin"], COLORS["blue"]),
            ("HPF", chain["hpf"], COLORS["green"]),
            ("gain x201", chain["gain"], COLORS["orange"]),
            ("LPF output", chain["lpf"], COLORS["red"]),
        ],
    )
    draw_plot(
        out / "notch_60hz_effect.png",
        "60 Hz injection and nominal notch response",
        t,
        [("vin + 60Hz", noisy, COLORS["red"]), ("after notch", notch_only, COLORS["blue"])],
    )
    draw_hist(out / "adc_quantization_hist.png", "12-bit ADC signed code histogram", adc_signed, bins=80)
    draw_plot(
        out / "afe_on_off_comparison.png",
        "AFE-on nominal ADC code vs direct quantization",
        t,
        [
            ("AFE-on signed code", adc_signed.astype(float), COLORS["blue"]),
            ("AFE-off direct code", no_afe_signed.astype(float), COLORS["gray"]),
        ],
    )
    f, resp = frequency_response(args.fs)
    draw_plot(
        out / "afe_frequency_response.png",
        "Documented nominal AFE frequency response",
        f,
        [
            ("HPF", 20.0 * np.log10(np.maximum(resp["HPF"], 1e-6)), COLORS["green"]),
            ("60Hz notch", 20.0 * np.log10(np.maximum(resp["notch"], 1e-6)), COLORS["red"]),
            ("LPF", 20.0 * np.log10(np.maximum(resp["LPF"], 1e-6)), COLORS["orange"]),
            ("total", 20.0 * np.log10(np.maximum(resp["total"], 1e-6)), COLORS["blue"]),
        ],
    )

    clipping = int(np.sum((chain["lpf"] <= -1.65) | (chain["lpf"] >= 1.65)))
    summary = {
        "source_chunk": str(chunk),
        "source_chunk_crc32": crc32(chunk),
        "samples_used": int(len(signed)),
        "sample_rate_hz": args.fs,
        "vin_scaling": "vin_v = signed_code / 200000",
        "nominal_chain": {
            "hpf_hz": 0.482,
            "ia_gain": 201,
            "notch_hz": 60,
            "notch_q": 5,
            "lpf_hz": 150,
            "adc_bits": 12,
            "adc_ref_v": "+/-1.65",
        },
        "adc": {
            "signed_min": int(np.min(adc_signed)),
            "signed_max": int(np.max(adc_signed)),
            "clipping_samples": clipping,
        },
        "figures": sorted(str(p) for p in out.glob("*.png")),
        "limitation": "These figures are generated from available signed .mem data and a documented nominal AFE model. They are model-evidence figures, not measured PCB/silicon or transistor-level XMODEL transient proof.",
    }
    write_json(REPORTS / "afe_xmodel_evidence_summary.json", summary)
    md = [
        "# AFE XMODEL Evidence Run",
        "",
        f"- Source chunk: `{chunk}`",
        f"- Samples used: {len(signed)} at {args.fs:g} Hz",
        "- Scaling: `vin_v = signed_code / 200000`",
        "- Chain: HPF 0.482 Hz -> gain x201 -> 60 Hz notch -> LPF 150 Hz -> 12-bit ADC",
        "",
        "## Generated Figures",
        "",
        *[f"- `reports/award_readiness/figures/{Path(path).name}`" for path in summary["figures"]],
        "",
        "## Limitation",
        "",
        summary["limitation"],
    ]
    (REPORTS / "afe_xmodel_evidence_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(REPORTS / "afe_xmodel_evidence_summary.md")


if __name__ == "__main__":
    main()
