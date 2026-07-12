from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
BOARD = REPO / "benchmarks" / "accelerator_benefit" / "board"
RESULTS = BOARD / "build"
SW_SRC = BOARD / "instrumented_source"
XSA = REPO / "results" / "board_replay" / "microblaze_full_replay" / "snn_ecg_mb_full_replay.xsa"
WORK_ROOT = REPO.parent / "_snn_ecg_accelerator_benchmark_app_work"
WORKSPACE = WORK_ROOT / "vitis_workspace"
SHADOW_XSA = WORK_ROOT / "hw" / "snn_ecg_mb_full_replay.xsa"
SHADOW_SRC = WORK_ROOT / "src"
WORKSPACE_ELF = WORKSPACE / "snn_ecg_mb_full_replay_benchmark" / "Debug" / "snn_ecg_mb_full_replay_benchmark.elf"
RESULT_ELF = RESULTS / "snn_ecg_mb_full_replay_benchmark.elf"
LEGACY_WORKSPACE = REPO.parent / "_snn_ecg_microblaze_full_replay_app_work" / "vitis_workspace"
LEGACY_PLATFORM = LEGACY_WORKSPACE / "snn_ecg_mb_full_replay_platform"
LEGACY_PLATFORM_XSA = LEGACY_PLATFORM / "hw" / "snn_ecg_mb_full_replay.xsa"
LEGACY_APP_ELF = LEGACY_WORKSPACE / "snn_ecg_mb_full_replay_benchmark" / "Debug" / "snn_ecg_mb_full_replay_benchmark.elf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def which(name: str) -> Path | None:
    for item in os.environ.get("PATH", "").split(os.pathsep):
        path = Path(item) / name
        if path.exists():
            return path
    return None


def first_existing(patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return Path(matches[0])
    return None


def find_executable(name: str, patterns: list[str]) -> Path | None:
    found = which(name)
    if found:
        return found
    return first_existing(patterns)


def find_xsct() -> Path | None:
    return find_executable(
        "xsct.bat",
        [
            r"C:\Xilinx\Vitis\*\bin\xsct.bat",
            r"C:\Xilinx\SDK\*\bin\xsct.bat",
            r"C:\Xilinx\Vivado\*\bin\xsct.bat",
        ],
    )


def find_microblaze_gcc() -> Path | None:
    for name, patterns in {
        "microblazeel-xilinx-elf-gcc.exe": [
            r"C:\Xilinx\Vitis\*\gnu\microblaze\nt\bin\microblazeel-xilinx-elf-gcc.exe",
            r"C:\Xilinx\SDK\*\gnu\microblaze\nt\bin\microblazeel-xilinx-elf-gcc.exe",
        ],
        "microblaze-xilinx-elf-gcc.exe": [
            r"C:\Xilinx\Vitis\*\gnu\microblaze\nt\bin\microblaze-xilinx-elf-gcc.exe",
            r"C:\Xilinx\SDK\*\gnu\microblaze\nt\bin\microblaze-xilinx-elf-gcc.exe",
        ],
        "mb-gcc.exe": [
            r"C:\Xilinx\Vitis\*\gnu\microblaze\nt\bin\mb-gcc.exe",
            r"C:\Xilinx\SDK\*\gnu\microblaze\nt\bin\mb-gcc.exe",
        ],
    }.items():
        found = find_executable(name, patterns)
        if found:
            return found
    return None


def prepare_shadow_inputs() -> None:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    SHADOW_XSA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(XSA, SHADOW_XSA)
    if SHADOW_SRC.exists():
        shutil.rmtree(SHADOW_SRC)
    shutil.copytree(SW_SRC, SHADOW_SRC)
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)


def write_xsct_tcl() -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    tcl = RESULTS / "build_instrumented_app.tcl"
    tcl.write_text(
        f"""setws "{WORKSPACE.as_posix()}"
platform create -name snn_ecg_mb_full_replay_platform -hw "{SHADOW_XSA.as_posix()}" -proc microblaze_0 -os standalone
platform active snn_ecg_mb_full_replay_platform
domain active standalone_domain
catch {{bsp config stdin axi_uartlite_0}} stdin_msg
if {{$stdin_msg ne ""}} {{puts "WARN BSP stdin config: $stdin_msg"}}
catch {{bsp config stdout axi_uartlite_0}} stdout_msg
if {{$stdout_msg ne ""}} {{puts "WARN BSP stdout config: $stdout_msg"}}
catch {{bsp regenerate}} bsp_msg
if {{$bsp_msg ne ""}} {{puts "WARN BSP regenerate: $bsp_msg"}}
platform generate
app create -name snn_ecg_mb_full_replay_benchmark -platform snn_ecg_mb_full_replay_platform -domain standalone_domain -template {{Empty Application}}
importsources -name snn_ecg_mb_full_replay_benchmark -path "{SHADOW_SRC.as_posix()}"
app build -name snn_ecg_mb_full_replay_benchmark
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def write_reuse_platform_tcl() -> Path:
    """Reuse the previously generated platform only when its XSA is identical."""
    tcl = RESULTS / "build_instrumented_app_reuse_platform.tcl"
    tcl.write_text(
        f"""setws "{LEGACY_WORKSPACE.as_posix()}"
platform active snn_ecg_mb_full_replay_platform
catch {{app remove -name snn_ecg_mb_full_replay_benchmark}}
app create -name snn_ecg_mb_full_replay_benchmark -platform snn_ecg_mb_full_replay_platform -domain standalone_domain -template {{Empty Application}}
importsources -name snn_ecg_mb_full_replay_benchmark -path "{SHADOW_SRC.as_posix()}"
app build -name snn_ecg_mb_full_replay_benchmark
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def update_summary_after_build() -> None:
    summary_path = RESULTS / "instrumented_build_summary.json"
    if not summary_path.exists():
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(
        {
            "baremetal_elf": str(RESULT_ELF),
            "baremetal_elf_exists": RESULT_ELF.exists(),
        }
    )
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def status_payload() -> dict[str, object]:
    xsct = find_xsct()
    gcc = find_microblaze_gcc()
    return {
        "xsa": str(XSA),
        "xsa_exists": XSA.exists(),
        "source_dir": str(SW_SRC),
        "source_exists": (SW_SRC / "main.c").exists(),
        "work_root": str(WORK_ROOT),
        "workspace": str(WORKSPACE),
        "shadow_xsa": str(SHADOW_XSA),
        "shadow_source_dir": str(SHADOW_SRC),
        "xsct": str(xsct) if xsct else None,
        "microblaze_gcc": str(gcc) if gcc else None,
        "toolchain_available": bool(xsct and gcc),
        "workspace_elf": str(WORKSPACE_ELF),
        "workspace_elf_exists": WORKSPACE_ELF.exists(),
        "elf": str(RESULT_ELF),
        "elf_exists": RESULT_ELF.exists(),
        "reusable_platform": str(LEGACY_PLATFORM),
        "reusable_platform_xsa_match": (
            LEGACY_PLATFORM_XSA.exists() and XSA.exists() and sha256(LEGACY_PLATFORM_XSA) == sha256(XSA)
        ),
    }


def build_app() -> int:
    payload = status_payload()
    if not payload["xsa_exists"]:
        print(json.dumps({**payload, "status": "missing_xsa"}, indent=2))
        return 2
    if not payload["toolchain_available"]:
        print(json.dumps({**payload, "status": "missing_vitis_or_microblaze_gcc"}, indent=2))
        return 2

    tcl = write_xsct_tcl()
    log = RESULTS / "build_instrumented_app.log"
    prepare_shadow_inputs()
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(
            [str(payload["xsct"]), str(tcl)],
            cwd=REPO,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
        )
    build_method = "fresh_platform"
    built_elf = WORKSPACE_ELF
    if (proc.returncode != 0 or not WORKSPACE_ELF.exists()) and payload["reusable_platform_xsa_match"]:
        fallback_tcl = write_reuse_platform_tcl()
        with log.open("a", encoding="utf-8", errors="replace") as f:
            f.write("\nBENCHMARK_BUILD_FALLBACK: reusing prior platform with byte-identical XSA\n")
            proc = subprocess.run(
                [str(payload["xsct"]), str(fallback_tcl)],
                cwd=REPO,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )
        build_method = "reused_byte_identical_platform"
        built_elf = LEGACY_APP_ELF
    if proc.returncode == 0 and built_elf.exists():
        shutil.copy2(built_elf, RESULT_ELF)
        update_summary_after_build()
    payload = status_payload()
    payload["status"] = "built" if proc.returncode == 0 and payload["elf_exists"] else "build_failed"
    payload["build_method"] = build_method
    payload["log"] = str(log)
    if RESULT_ELF.exists():
        payload["elf_sha256"] = sha256(RESULT_ELF)
        payload["elf_bytes"] = RESULT_ELF.stat().st_size
    (RESULTS / "build_status.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "built" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or inspect the MicroBlaze full-record replay bare-metal app.")
    parser.add_argument("--check-tools", action="store_true", help="only report XSA/toolchain/ELF availability")
    args = parser.parse_args()
    write_xsct_tcl()
    if args.check_tools:
        print(json.dumps({**status_payload(), "status": "checked"}, indent=2))
        return 0
    return build_app()


if __name__ == "__main__":
    raise SystemExit(main())
