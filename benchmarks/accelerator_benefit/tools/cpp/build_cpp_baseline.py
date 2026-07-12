#!/usr/bin/env python3
"""Build the exact single-thread C++ RTL translation with Verilator."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RTL = REPO / "rtl"
OUT = HERE / "bin" / "cpp_baseline.exe"
BUILD_INFO = HERE / "cpp_build_environment.json"
VERILATOR_ROOT = Path(os.environ.get("OSS_CAD_SUITE", r"C:\oss-cad-suite-20260711"))
MINGW = Path(r"C:\Xilinx\Vitis_HLS\2020.2\tps\win64\msys64")
GCC_BIN = MINGW / "mingw64" / "bin"
USR_BIN = MINGW / "usr" / "bin"
BUILD = Path(tempfile.gettempdir()) / "snn_ecg_verilator_cpp"

SOURCES = [
    "rtl/core/ecg_event_encoder.v",
    "rtl/core/ecg_event_encoder_adaptive.v",
    "rtl/core/snn_ecg_input_normalizer.v",
    "rtl/core/qrs_lif_detector.v",
    "rtl/core/pnn_rhythm_predictor.v",
    "rtl/core/dscr_spike_counter.v",
    "rtl/core/ram_peak_accumulator.v",
    "rtl/core/rdm_variability_neuron.v",
    "rtl/core/ectopic_pair_neuron.v",
    "rtl/core/qrs_maf_neuron.v",
    "rtl/core/rbbb_qrs_delay_bank.v",
    "rtl/core/abandoned_feature_stubs.v",
    "rtl/core/class_score_neurons.v",
    "rtl/core/snn_ecg_3feat_top.v",
    "rtl/final_membrane_layer.v",
    "rtl/snn_ecg_30min_final_top.v",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(command: list[str], env: dict[str, str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout


def main() -> int:
    verilator = VERILATOR_ROOT / "bin" / "verilator_bin.exe"
    make = GCC_BIN / "make.exe"
    compiler = GCC_BIN / "g++.exe"
    for path in (verilator, make, compiler):
        if not path.exists():
            raise SystemExit(f"required build tool missing: {path}")

    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    shutil.copytree(RTL, BUILD / "rtl")
    shutil.copy2(HERE / "cpp_baseline.cpp", BUILD / "cpp_baseline.cpp")
    env = os.environ.copy()
    env["VERILATOR_ROOT"] = str(VERILATOR_ROOT / "share" / "verilator")
    env["PATH"] = os.pathsep.join([str(USR_BIN), str(GCC_BIN), str(VERILATOR_ROOT / "bin"), str(VERILATOR_ROOT / "lib"), env.get("PATH", "")])

    verilator_command = [
        str(verilator), "--cc", "--exe", "-Wno-fatal",
        "--top-module", "snn_ecg_30min_final_top", "-Irtl",
        "--Mdir", "obj", "cpp_baseline.cpp", *SOURCES,
    ]
    verilator_log = run(verilator_command, env, BUILD)
    make_command = [
        str(make), "-C", str(BUILD / "obj"), "-f", "Vsnn_ecg_30min_final_top.mk", "-j", "4",
        "CFG_CXXFLAGS_NO_UNUSED=",
        f"SHELL={str(USR_BIN / 'bash.exe').replace(os.sep, '/')}",
        "LDLIBS=-pthread -lpthread -latomic -lpsapi",
        "OPT_FAST=-O3", "OPT_SLOW=-O3", "OPT_GLOBAL=-O3",
    ]
    make_log = run(make_command, env, BUILD)
    built = BUILD / "obj" / "Vsnn_ecg_30min_final_top.exe"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, OUT)
    version = run([str(verilator), "--version"], env, BUILD).strip()
    compiler_version = run([str(compiler), "--version"], env, BUILD).splitlines()[0]
    payload = {
        "status": "BUILT",
        "translation": "Verilator exact cycle-accurate C++ translation of locked RTL",
        "single_thread_model": True,
        "optimization": "-O3",
        "verilator_version": version,
        "compiler_version": compiler_version,
        "binary": str(OUT.relative_to(REPO)).replace("\\", "/"),
        "binary_sha256": sha256(OUT),
        "source_sha256": sha256(HERE / "cpp_baseline.cpp"),
        "rtl_source_hashes": {path: sha256(REPO / path) for path in SOURCES},
        "verilator_command": verilator_command,
        "make_command": make_command,
        "notes": "Generated model advances the canonical RTL clock and is not a hand-optimized algorithmic rewrite.",
        "verilator_log_tail": verilator_log.splitlines()[-5:],
        "make_log_tail": make_log.splitlines()[-10:],
    }
    BUILD_INFO.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
