from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "datasets" / "afe_output_xmodelmatch_curated_v2_50_25_25"
RESULTS = REPO / "results" / "c24_rtl_equivalence"
SIM_SRC = REPO / "SNN_ECG.srcs" / "sources_1" / "new"
SIM_TB = REPO / "SNN_ECG.srcs" / "sim_1" / "new" / "tb_snn_ecg_3feat_dataset.v"
XSIM_WORK = REPO / "results" / "c24_rtl_equivalence" / "xsim_work"

XVLOG = Path(r"C:\Xilinx\Vivado\2020.2\bin\xvlog.bat")
XELAB = Path(r"C:\Xilinx\Vivado\2020.2\bin\xelab.bat")
XSIM = Path(r"C:\Xilinx\Vivado\2020.2\bin\xsim.bat")


SOURCES = [
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
    "snn_ecg_model_a_plus_core.v",
]


def slash(path: Path) -> str:
    return path.resolve().as_posix()


def run(cmd: list[str], cwd: Path, log_path: Path) -> None:
    print("$ " + " ".join(cmd), flush=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
        raise SystemExit(f"command failed: {' '.join(cmd)}\nlog: {log_path}\n" + "\n".join(tail))


def build_manifest(split: str) -> Path:
    manifest_csv = DATASET / f"afe_manifest_{split}.csv"
    out = RESULTS / f"xsim_{split}_manifest.txt"
    rows = list(csv.DictReader(manifest_csv.open("r", encoding="utf-8-sig", newline="")))
    signed_dir = DATASET / "signed" / split
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            mem_name = Path(row["afe_adc_signed_file"]).name
            mem_path = signed_dir / mem_name
            if not mem_path.exists():
                raise FileNotFoundError(mem_path)
            label = row["class_label"]
            class_id = int(row["class_id"])
            n_samples = int(row.get("n_samples") or 60000)
            f.write(f"{class_id} {label} {n_samples} {slash(mem_path)}\n")
    return out


def write_wrapper(split: str, manifest: Path) -> Path:
    wrapper = XSIM_WORK / f"tb_c24_afe_{split}.v"
    result_csv = RESULTS / f"xsim_{split}_result.csv"
    subwindow_csv = RESULTS / f"xsim_{split}_subwindow.csv"
    wrapper.write_text(
        f"""`timescale 1ns/1ps

module tb_c24_afe_{split};
    tb_snn_ecg_3feat_dataset #(
        .MAX_SAMPLES(60000),
        .MANIFEST_FILE("{slash(manifest)}"),
        .WRITE_CASE_CSV(1),
        .RESULT_CSV("{slash(result_csv)}"),
        .WRITE_SUBWINDOW_CSV(0),
        .SUBWINDOW_CSV("{slash(subwindow_csv)}"),
        .MANIFEST_HAS_SAMPLE_COUNT(1),
        .ENABLE_INPUT_NORMALIZER(0)
    ) tb();
endmodule
""",
        encoding="utf-8",
        newline="\n",
    )
    return wrapper


def write_project(wrapper: Path, split: str) -> tuple[Path, Path]:
    prj = XSIM_WORK / f"sources_{split}.prj"
    lines = [f'verilog work "{slash(SIM_SRC / source)}"' for source in SOURCES]
    lines.append(f'verilog work "{slash(SIM_TB)}"')
    lines.append(f'verilog work "{slash(wrapper)}"')
    prj.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    tcl = XSIM_WORK / f"run_{split}.tcl"
    tcl.write_text("run all\nquit\n", encoding="utf-8", newline="\n")
    return prj, tcl


def run_split(split: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    XSIM_WORK.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(split)
    wrapper = write_wrapper(split, manifest)
    prj, tcl = write_project(wrapper, split)
    snapshot = f"tb_c24_afe_{split}_behav"
    top = f"tb_c24_afe_{split}"

    run([str(XVLOG), "--nolog", "-prj", slash(prj)], XSIM_WORK, RESULTS / f"xvlog_{split}.log")
    run([str(XELAB), "--nolog", "-debug", "typical", top, "-s", snapshot], XSIM_WORK, RESULTS / f"xelab_{split}.log")
    run([str(XSIM), snapshot, "--nolog", "-tclbatch", slash(tcl)], XSIM_WORK, RESULTS / f"xsim_{split}.log")

    result_csv = RESULTS / f"xsim_{split}_result.csv"
    if not result_csv.exists():
        raise SystemExit(f"missing result csv: {result_csv}")
    with result_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    correct = sum(1 for row in rows if row["correct"] == "1")
    print(f"{split}: {correct}/{total} = {correct / total * 100:.2f}%", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["train", "val", "test"], action="append")
    args = parser.parse_args()
    splits = args.split or ["test", "val", "train"]
    for tool in [XVLOG, XELAB, XSIM]:
        if not tool.exists():
            raise FileNotFoundError(tool)
    for split in splits:
        run_split(split)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
