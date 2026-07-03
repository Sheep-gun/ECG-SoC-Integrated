from __future__ import annotations

import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "final_membrane_v2_snn" / "axi_wrapper_smoke"
XVLOG = Path(r"C:\Xilinx\Vivado\2020.2\bin\xvlog.bat")
XELAB = Path(r"C:\Xilinx\Vivado\2020.2\bin\xelab.bat")
XSIM = Path(r"C:\Xilinx\Vivado\2020.2\bin\xsim.bat")

CORE_SOURCES = [
    "ecg_event_encoder.v",
    "ecg_event_encoder_adaptive.v",
    "snn_ecg_input_normalizer.v",
    "qrs_lif_detector.v",
    "pnn_rhythm_predictor.v",
    "dscr_spike_counter.v",
    "ram_peak_accumulator.v",
    "rdm_variability_neuron.v",
    "ectopic_pair_neuron.v",
    "qrs_maf_neuron.v",
    "rbbb_qrs_delay_bank.v",
    "abandoned_feature_stubs.v",
    "class_score_neurons.v",
    "snn_ecg_3feat_top.v",
]


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def run(cmd: list[str], log: Path) -> None:
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(cmd, cwd=REPO, stdout=f, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}; see {log}")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    sources = [REPO / "rtl" / "common" / "reset_sync.v"]
    sources.extend(REPO / "rtl" / "core" / src for src in CORE_SOURCES)
    sources.extend(
        [
            REPO / "rtl" / "final_membrane_layer.v",
            REPO / "rtl" / "snn_ecg_30min_final_top.v",
            REPO / "rtl" / "axi" / "snn_ecg_axi_lite_stream_top.v",
            REPO / "sim" / "tb_snn_ecg_axi_smoke.v",
        ]
    )

    run([str(XVLOG), "--nolog", *[slash(src) for src in sources]], RESULTS / "xvlog.log")
    run([str(XELAB), "--nolog", "tb_snn_ecg_axi_smoke", "-s", "tb_snn_ecg_axi_smoke"], RESULTS / "xelab.log")
    run([str(XSIM), "--nolog", "tb_snn_ecg_axi_smoke", "-R"], RESULTS / "xsim.log")

    text = (RESULTS / "xsim.log").read_text(encoding="utf-8", errors="replace")
    if "AXI_SMOKE_PASS" not in text or "AXI_SMOKE_FAIL" in text:
        raise RuntimeError(f"AXI smoke failed; see {RESULTS / 'xsim.log'}")
    print(RESULTS / "xsim.log")


if __name__ == "__main__":
    main()
