from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "final_membrane_v2_snn" / "microblaze_smoke"
SW_SRC = REPO / "sw" / "microblaze_smoke" / "src"
XSA = RESULTS / "snn_ecg_mb_smoke.xsa"
WORKSPACE = RESULTS / "vitis_workspace"


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


def write_xsct_tcl() -> Path:
    tcl = RESULTS / "build_microblaze_smoke_app.tcl"
    tcl.write_text(
        f"""setws "{WORKSPACE.as_posix()}"
platform create -name snn_ecg_mb_smoke_platform -hw "{XSA.as_posix()}" -proc microblaze_0 -os standalone
platform active snn_ecg_mb_smoke_platform
domain active standalone_domain
catch {{bsp config stdin axi_uartlite_0}} stdin_msg
if {{$stdin_msg ne ""}} {{puts "WARN BSP stdin config: $stdin_msg"}}
catch {{bsp config stdout axi_uartlite_0}} stdout_msg
if {{$stdout_msg ne ""}} {{puts "WARN BSP stdout config: $stdout_msg"}}
catch {{bsp regenerate}} bsp_msg
if {{$bsp_msg ne ""}} {{puts "WARN BSP regenerate: $bsp_msg"}}
platform generate
app create -name snn_ecg_mb_smoke_app -platform snn_ecg_mb_smoke_platform -domain standalone_domain -template {{Empty Application}}
importsources -name snn_ecg_mb_smoke_app -path "{SW_SRC.as_posix()}"
app build -name snn_ecg_mb_smoke_app
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return tcl


def status_payload() -> dict[str, object]:
    xsct = find_xsct()
    gcc = find_microblaze_gcc()
    elf = WORKSPACE / "snn_ecg_mb_smoke_app" / "Debug" / "snn_ecg_mb_smoke_app.elf"
    return {
        "xsa": str(XSA),
        "xsa_exists": XSA.exists(),
        "source_dir": str(SW_SRC),
        "source_exists": (SW_SRC / "main.c").exists(),
        "workspace": str(WORKSPACE),
        "xsct": str(xsct) if xsct else None,
        "microblaze_gcc": str(gcc) if gcc else None,
        "toolchain_available": bool(xsct and gcc),
        "elf": str(elf),
        "elf_exists": elf.exists(),
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
    log = RESULTS / "build_microblaze_smoke_app.log"
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    with log.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(
            [payload["xsct"], str(tcl)],
            cwd=REPO,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
    payload = status_payload()
    payload["status"] = "built" if proc.returncode == 0 and payload["elf_exists"] else "build_failed"
    payload["log"] = str(log)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "built" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or inspect the MicroBlaze smoke bare-metal app.")
    parser.add_argument("--check-tools", action="store_true", help="only report XSA/toolchain/ELF availability")
    args = parser.parse_args()
    write_xsct_tcl()
    if args.check_tools:
        print(json.dumps({**status_payload(), "status": "checked"}, indent=2))
        return 0
    return build_app()


if __name__ == "__main__":
    raise SystemExit(main())
