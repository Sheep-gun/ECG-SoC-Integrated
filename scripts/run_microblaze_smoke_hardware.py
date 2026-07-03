from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "final_membrane_v2_snn" / "microblaze_smoke"
BIT = RESULTS / "snn_ecg_mb_smoke.bit"
DEFAULT_ELF = RESULTS / "vitis_workspace" / "snn_ecg_mb_smoke_app" / "Debug" / "snn_ecg_mb_smoke_app.elf"
XSDB_TCL = RESULTS / "program_microblaze_smoke_board.tcl"
TRANSCRIPT = RESULTS / "uart_transcript.txt"


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


def find_xsdb() -> Path | None:
    found = which("xsdb.bat")
    if found:
        return found
    return first_existing([r"C:\Xilinx\Vivado\*\bin\xsdb.bat", r"C:\Xilinx\Vitis\*\bin\xsdb.bat"])


def find_hw_server() -> Path | None:
    found = which("hw_server.bat")
    if found:
        return found
    return first_existing([r"C:\Xilinx\Vivado\*\bin\hw_server.bat", r"C:\Xilinx\Vitis\*\bin\hw_server.bat"])


def write_xsdb_tcl(bit: Path, elf: Path) -> Path:
    XSDB_TCL.write_text(
        f"""connect -url tcp:127.0.0.1:3121
puts "XSDB targets after connect:"
targets
targets -set -nocase -filter {{name =~ "*xc7a100t*"}}
fpga -file "{bit.as_posix()}"
after 1000
puts "XSDB targets after fpga:"
targets
targets -set -nocase -filter {{name =~ "*MicroBlaze*#0"}}
rst -processor
dow "{elf.as_posix()}"
con
puts "SNN_ECG_MB_XSDB_PROGRAM_DONE"
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return XSDB_TCL


def write_uart_capture_ps1(port: str, baud: int, seconds: int, out_path: Path) -> Path:
    ps1 = RESULTS / "capture_uart_transcript.ps1"
    ps1.write_text(
        f"""$ErrorActionPreference = 'Stop'
$portName = '{port}'
$baud = {baud}
$seconds = {seconds}
$outPath = '{str(out_path).replace("'", "''")}'
$sp = [System.IO.Ports.SerialPort]::new($portName, $baud, 'None', 8, 'One')
$sp.ReadTimeout = 250
$sp.Open()
$deadline = [DateTime]::UtcNow.AddSeconds($seconds)
$buf = New-Object System.Text.StringBuilder
try {{
  while ([DateTime]::UtcNow -lt $deadline) {{
    try {{
      $chunk = $sp.ReadExisting()
      if ($chunk.Length -gt 0) {{
        [void]$buf.Append($chunk)
        Write-Host $chunk -NoNewline
        if ($buf.ToString().Contains('SNN_ECG_MB_SMOKE_PASS') -or
            $buf.ToString().Contains('SNN_ECG_MB_SMOKE_FAIL')) {{
          break
        }}
      }}
    }} catch [TimeoutException] {{
    }}
    Start-Sleep -Milliseconds 50
  }}
}} finally {{
  $sp.Close()
}}
$buf.ToString() | Set-Content -Path $outPath -Encoding ASCII
if ($buf.ToString().Contains('SNN_ECG_MB_SMOKE_PASS')) {{ exit 0 }}
if ($buf.ToString().Contains('SNN_ECG_MB_SMOKE_FAIL')) {{ exit 1 }}
exit 3
""",
        encoding="utf-8",
        newline="\n",
    )
    return ps1


def status(bit: Path, elf: Path, uart: str | None) -> dict[str, object]:
    xsdb = find_xsdb()
    hw_server = find_hw_server()
    return {
        "bit": str(bit),
        "bit_exists": bit.exists(),
        "elf": str(elf),
        "elf_exists": elf.exists(),
        "xsdb": str(xsdb) if xsdb else None,
        "hw_server": str(hw_server) if hw_server else None,
        "uart_port": uart,
        "xsdb_tcl": str(XSDB_TCL),
        "transcript": str(TRANSCRIPT),
        "ready_to_program": bool(bit.exists() and elf.exists() and xsdb),
    }


def run_hw_server(hw_server: Path) -> subprocess.Popen[str]:
    log = RESULTS / "hw_server.log"
    f = log.open("w", encoding="utf-8", errors="replace")
    return subprocess.Popen([str(hw_server), "-s", "tcp::3121"], stdout=f, stderr=subprocess.STDOUT, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Program the MicroBlaze smoke bit/ELF and optionally capture UART.")
    parser.add_argument("--bit", type=Path, default=BIT)
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--uart", default=None, help="optional UART COM port, for example COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--uart-seconds", type=int, default=15)
    parser.add_argument("--check", action="store_true", help="only report tool/artifact availability")
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    args.bit = args.bit.resolve()
    args.elf = args.elf.resolve()
    write_xsdb_tcl(args.bit, args.elf)
    payload = status(args.bit, args.elf, args.uart)
    if args.check:
        print(json.dumps({**payload, "status": "checked"}, indent=2))
        return 0
    if not payload["ready_to_program"]:
        print(json.dumps({**payload, "status": "not_ready"}, indent=2))
        return 2

    hw_proc = None
    if payload["hw_server"]:
        hw_proc = run_hw_server(Path(str(payload["hw_server"])))
        time.sleep(2.0)

    xsdb_log = RESULTS / "xsdb_program.log"
    with xsdb_log.open("w", encoding="utf-8", errors="replace") as f:
        xsdb_proc = subprocess.run([str(payload["xsdb"]), str(XSDB_TCL)], cwd=REPO, stdout=f, stderr=subprocess.STDOUT, text=True)

    uart_status = None
    if args.uart:
        ps1 = write_uart_capture_ps1(args.uart, args.baud, args.uart_seconds, TRANSCRIPT)
        uart_proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
            cwd=REPO,
            text=True,
        )
        uart_status = uart_proc.returncode

    if hw_proc is not None:
        hw_proc.terminate()

    payload = {
        **status(args.bit, args.elf, args.uart),
        "status": "ran",
        "xsdb_returncode": xsdb_proc.returncode,
        "xsdb_log": str(xsdb_log),
        "uart_returncode": uart_status,
        "pass_seen": TRANSCRIPT.exists() and ("SNN_ECG_MB_SMOKE_PASS" in TRANSCRIPT.read_text(encoding="utf-8", errors="replace")),
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["xsdb_returncode"] == 0 and (uart_status in (None, 0)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
