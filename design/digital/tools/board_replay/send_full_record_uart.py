from __future__ import annotations

import argparse
import csv
import json
import os
import re
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "board_replay" / "microblaze_full_replay"
REPORTS = REPO / "reports" / "final" / "board_replay"
TRANSCRIPTS = REPORTS
COMPARISONS = REPORTS
EXPECTED_CASE_CSV = REPO / "reports" / "final" / "fulltop_xsim_locked_class_cases_predictions.csv"

DEFAULT_BIT = RESULTS / "snn_ecg_mb_full_replay.bit"
DEFAULT_ELF = RESULTS / "snn_ecg_mb_full_replay_app.elf"
DEFAULT_BAUD = 230400
EXPECTED_SAMPLES = 1_800_000
EXPECTED_WINDOWS = 30
EXPECTED_DECISIONS = 1
DEFAULT_FLOW_CHUNK_SAMPLES = 4096
FLOW_ACK_BYTE = 0xA5

CLASS_LABELS = ["NSR", "CHF", "ARR", "AFF"]


def import_serial() -> Any:
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "pyserial is required for UART replay. Install it in the active Python environment with: "
            "python -m pip install pyserial"
        ) from exc
    return serial


def which(name: str) -> Path | None:
    for item in os.environ.get("PATH", "").split(os.pathsep):
        path = Path(item) / name
        if path.exists():
            return path
    return None


def first_existing(patterns: list[str]) -> Path | None:
    import glob

    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return Path(matches[0])
    return None


def find_xsdb() -> Path | None:
    found = which("xsdb.bat")
    if found:
        return found
    return first_existing([r"C:\Xilinx\Vitis\*\bin\xsdb.bat", r"C:\Xilinx\Vivado\*\bin\xsdb.bat"])


def find_hw_server() -> Path | None:
    found = which("hw_server.bat")
    if found:
        return found
    return first_existing([r"C:\Xilinx\Vitis\*\bin\hw_server.bat", r"C:\Xilinx\Vivado\*\bin\hw_server.bat"])


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def parse_sample_token(token: str) -> int:
    text = token.strip()
    if not text:
        raise ValueError("empty sample token")
    if text.lower().startswith("0x"):
        raw = int(text, 16)
        if raw & 0x800:
            raw -= 0x1000
        return raw
    if re.fullmatch(r"[0-9a-fA-F]{1,3}", text) and not text.startswith("-"):
        raw = int(text, 16)
        if raw & 0x800:
            raw -= 0x1000
        return raw
    value = int(text, 10)
    if value > 2047 and value <= 4095:
        value -= 4096
    if value < -2048 or value > 2047:
        raise ValueError(f"signed 12-bit sample out of range: {token}")
    return value


def load_mem_payload(path: Path, max_samples: int | None = None) -> tuple[bytes, int]:
    payload = bytearray()
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            line = line.split("#", 1)[0].split("//", 1)[0].strip()
            if not line:
                continue
            token = line.split()[0]
            value = parse_sample_token(token)
            payload.extend(struct.pack("<h", value))
            count += 1
            if max_samples is not None and count >= max_samples:
                break
    return bytes(payload), count


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalize(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").lower()


def expected_from_predictions(case_id: str) -> dict[str, Any] | None:
    pred_csv = EXPECTED_CASE_CSV
    if not pred_csv.exists():
        return None
    for row in read_csv(pred_csv):
        if row.get("case_id") != case_id:
            continue
        return {
            "source": str(pred_csv),
            "case_id": row.get("case_id"),
            "expected_class": int(row["expected_class"]) if row.get("expected_class") else None,
            "final_pred": int(row["final_pred_class"]),
            "final_mem": {
                "NSR": int(row["final_mem_NSR"]),
                "CHF": int(row["final_mem_CHF"]),
                "ARR": int(row["final_mem_ARR"]),
                "AFF": int(row["final_mem_AFF"]),
            },
            "samples": int(row.get("samples_driven") or EXPECTED_SAMPLES),
            "snapshot_count": int(row.get("prof_windows") or EXPECTED_WINDOWS),
            "decision_count": int(row.get("prof_decisions") or EXPECTED_DECISIONS),
        }
    return None


def find_expected_from_repo(mem_path: Path, case_id: str | None) -> dict[str, Any] | None:
    if case_id is not None:
        return expected_from_predictions(case_id)
    return None


def load_expected_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    final_mem = data.get("final_mem")
    if isinstance(final_mem, list):
        final_mem = {cls: int(final_mem[idx]) for idx, cls in enumerate(CLASS_LABELS)}
    elif isinstance(final_mem, dict):
        final_mem = {cls: int(final_mem[cls]) for cls in CLASS_LABELS if cls in final_mem}
    else:
        final_mem = {}
    pred = data.get("final_pred", data.get("final_pred_class"))
    return {
        "source": str(path),
        "case_id": data.get("case_id"),
        "expected_class": data.get("expected_class"),
        "final_pred": int(pred) if pred is not None else None,
        "final_mem": final_mem,
        "samples": int(data.get("samples", EXPECTED_SAMPLES)),
        "snapshot_count": int(data.get("snapshot_count", EXPECTED_WINDOWS)),
        "decision_count": int(data.get("decision_count", EXPECTED_DECISIONS)),
    }


def write_expected_template(path: Path, mem_path: Path, case_name: str) -> None:
    template = {
        "case_name": case_name,
        "mem_file": str(mem_path),
        "samples": None,
        "snapshot_count": None,
        "decision_count": None,
        "final_pred": None,
        "final_mem": {"NSR": None, "CHF": None, "ARR": None, "AFF": None},
        "note": "Fill from Python/XSim golden result only. Do not invent expected values.",
    }
    path.write_text(json.dumps(template, indent=2), encoding="utf-8")


def parse_int(text: str) -> int:
    if text.lower().startswith("-0x"):
        return -int(text[3:], 16)
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text, 10)


def parse_board_values(transcript: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for key, raw in re.findall(r"([A-Za-z0-9_]+)=(-?0x[0-9a-fA-F]+|-?\d+)", transcript):
        values[key] = parse_int(raw)
    return values


def compare(expected: dict[str, Any] | None, board: dict[str, int], internal_pass: bool) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []

    def add(metric: str, expected_value: int | None, board_key: str) -> None:
        board_value = board.get(board_key)
        match = "" if expected_value is None or board_value is None else int(expected_value == board_value)
        rows.append(
            {
                "metric": metric,
                "expected": "" if expected_value is None else expected_value,
                "board": "" if board_value is None else board_value,
                "match": match,
            }
        )

    exp = expected or {}
    add("samples_received", exp.get("samples"), "samples_received")
    add("samples_sent_to_ip", exp.get("samples"), "samples_sent_to_ip")
    add("samples_accepted", exp.get("samples"), "samples_accepted")
    add("samples_consumed", exp.get("samples"), "samples_consumed")
    add("snapshot_count", exp.get("snapshot_count"), "snapshot_count")
    add("decision_count", exp.get("decision_count"), "decision_count")
    add("final_valid", 1, "final_valid")
    add("done", 1, "done")
    add("final_pred", exp.get("final_pred"), "final_pred")
    final_mem = exp.get("final_mem", {}) if isinstance(exp.get("final_mem", {}), dict) else {}
    for cls in CLASS_LABELS:
        add(f"final_mem_{cls}", final_mem.get(cls), f"final_mem_{cls.lower()}")
    add("feeder_tlast_count", 1, "feeder_tlast_count")
    add("snn_error", 0, "snn_error")
    add("feeder_error", 0, "feeder_error")

    comparable = [row for row in rows if row["expected"] != "" and row["board"] != ""]
    all_match = bool(comparable) and all(row["match"] == 1 for row in comparable)
    return rows, bool(internal_pass and expected is not None and all_match)


class SerialMonitor:
    def __init__(self, ser: Any):
        self.ser = ser
        self._buf = bytearray()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            chunk = self.ser.read(4096)
            if chunk:
                with self._lock:
                    self._buf.extend(chunk)

    def text(self) -> str:
        with self._lock:
            return self._buf.decode("utf-8", errors="replace")

    def wait_for(self, needle: str, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if needle in self.text():
                return True
            time.sleep(0.05)
        return False

    def wait_for_any(self, needles: list[str], timeout: float) -> str | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            text = self.text()
            for needle in needles:
                if needle in text:
                    return needle
            time.sleep(0.05)
        return None


def write_program_tcl(bit: Path, elf: Path) -> Path:
    path = RESULTS / "program_microblaze_full_replay_board.tcl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""connect -url tcp:127.0.0.1:3121
puts "XSDB targets after connect:"
targets
targets -set -nocase -filter {{name =~ "*xc7a100t*"}}
fpga -file "{slash(bit)}"
after 1000
puts "XSDB targets after fpga:"
targets
targets -set -nocase -filter {{name =~ "*MicroBlaze*#0"}}
rst -processor
dow "{slash(elf)}"
con
puts "SNN_ECG_FULL_REPLAY_XSDB_PROGRAM_DONE"
exit
""",
        encoding="utf-8",
        newline="\n",
    )
    return path


def program_board(bit: Path, elf: Path) -> int:
    xsdb = find_xsdb()
    if xsdb is None:
        raise RuntimeError("xsdb.bat not found")
    if not bit.exists():
        raise FileNotFoundError(bit)
    if not elf.exists():
        raise FileNotFoundError(elf)
    hw_server = find_hw_server()
    hw_proc: subprocess.Popen[str] | None = None
    if hw_server is not None:
        log = RESULTS / "hw_server_full_replay.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        f = log.open("w", encoding="utf-8", errors="replace")
        hw_proc = subprocess.Popen([str(hw_server), "-s", "tcp::3121"], stdout=f, stderr=subprocess.STDOUT, text=True)
        time.sleep(2.0)
    tcl = write_program_tcl(bit, elf)
    log_path = RESULTS / "xsdb_full_replay_program.log"
    with log_path.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run([str(xsdb), str(tcl)], cwd=REPO, stdout=f, stderr=subprocess.STDOUT, text=True)
    if hw_proc is not None:
        hw_proc.terminate()
    return proc.returncode


def send_payload(
    ser: Any,
    monitor: SerialMonitor,
    payload: bytes,
    flow_chunk_samples: int,
    progress_step: int,
    ack_timeout: float,
) -> None:
    sent = 0
    next_progress = progress_step
    total = len(payload) // 2
    while sent < total:
        next_sent = min(total, sent + flow_chunk_samples)
        chunk = payload[sent * 2 : next_sent * 2]
        ser.write(chunk)
        ser.flush()
        sent = next_sent
        if progress_step > 0 and sent >= next_progress:
            print(f"sent_samples={sent}/{total}")
            next_progress += progress_step
        if sent < total:
            marker = f"BOARD_PROGRESS samples_received={sent} "
            if not monitor.wait_for(marker, ack_timeout):
                raise TimeoutError(f"board progress marker not seen for samples_received={sent}")
            ser.write(bytes([FLOW_ACK_BYTE]))
            ser.flush()


def write_summary(
    path: Path,
    case_name: str,
    mem_path: Path,
    expected: dict[str, Any] | None,
    board: dict[str, int],
    transcript_path: Path,
    comparison_path: Path,
    pass_match: bool,
    internal_pass: bool,
) -> None:
    expected_src = expected.get("source") if expected else "MISSING"
    lines = [
        f"# {case_name} board full-record replay summary",
        "",
        f"- mem: `{mem_path}`",
        f"- expected source: `{expected_src}`",
        f"- transcript: `{transcript_path}`",
        f"- comparison: `{comparison_path}`",
        f"- board internal pass marker: `{internal_pass}`",
        f"- expected-vs-board match: `{pass_match}`",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for key in [
        "samples_received",
        "samples_sent_to_ip",
        "samples_accepted",
        "samples_consumed",
        "snapshot_count",
        "decision_count",
        "final_pred",
        "final_mem_nsr",
        "final_mem_chf",
        "final_mem_arr",
        "final_mem_aff",
        "snn_error",
        "feeder_error",
    ]:
        if key in board:
            lines.append(f"| {key} | {board[key]} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_replay_summary(
    case_name: str,
    transcript_path: Path,
    comparison_path: Path,
    summary_path: Path,
    pass_match: bool,
    internal_pass: bool,
    board: dict[str, int],
) -> None:
    system_summary_path = RESULTS / "microblaze_full_replay_summary.json"
    if not system_summary_path.exists():
        return
    data = json.loads(system_summary_path.read_text(encoding="utf-8"))
    data["last_full_record_replay"] = {
        "case_name": case_name,
        "transcript": str(transcript_path),
        "comparison": str(comparison_path),
        "summary": str(summary_path),
        "board_internal_pass": internal_pass,
        "expected_vs_board_pass": pass_match,
        "samples_received": board.get("samples_received"),
        "samples_sent_to_ip": board.get("samples_sent_to_ip"),
        "samples_accepted": board.get("samples_accepted"),
        "samples_consumed": board.get("samples_consumed"),
        "snapshot_count": board.get("snapshot_count"),
        "decision_count": board.get("decision_count"),
        "final_pred": board.get("final_pred"),
        "final_mem": {
            "NSR": board.get("final_mem_nsr"),
            "CHF": board.get("final_mem_chf"),
            "ARR": board.get("final_mem_arr"),
            "AFF": board.get("final_mem_aff"),
        },
        "snn_error": board.get("snn_error"),
        "feeder_error": board.get("feeder_error"),
    }
    system_summary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a signed 12-bit .mem full record to the MicroBlaze UART replay app.")
    parser.add_argument("--mem", type=Path, required=True, help="signed 12-bit .mem file, one sample per line")
    parser.add_argument("--uart", help="UART COM port, for example COM8")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--case-name", default=None)
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--expected-result", type=Path, default=None)
    parser.add_argument("--program", action="store_true", help="program bitstream and download ELF before waiting for READY")
    parser.add_argument("--bit", type=Path, default=DEFAULT_BIT)
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--ready-timeout", type=float, default=60.0)
    parser.add_argument("--done-timeout", type=float, default=900.0)
    parser.add_argument("--flow-chunk-samples", type=int, default=DEFAULT_FLOW_CHUNK_SAMPLES)
    parser.add_argument("--ack-timeout", type=float, default=30.0)
    parser.add_argument("--progress-samples", type=int, default=100000)
    parser.add_argument("--max-samples", type=int, default=None, help="debug only; truncates input before sending")
    parser.add_argument("--dry-run", action="store_true", help="parse input and expected result without opening UART")
    args = parser.parse_args()

    mem_path = args.mem.resolve()
    if not mem_path.exists():
        raise FileNotFoundError(mem_path)
    case_name = args.case_name or mem_path.stem
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    COMPARISONS.mkdir(parents=True, exist_ok=True)
    transcript_path = TRANSCRIPTS / f"{case_name}_uart_full_replay.txt"
    comparison_path = COMPARISONS / f"{case_name}_expected_vs_board.csv"
    summary_path = COMPARISONS / f"{case_name}_summary.md"
    expected_template_path = COMPARISONS / f"{case_name}_expected_result_template.json"
    expected_snapshot_path = COMPARISONS / f"{case_name}_expected_result.json"

    expected = load_expected_json(args.expected_result.resolve()) if args.expected_result else find_expected_from_repo(mem_path, args.case_id)
    if expected is None:
        write_expected_template(expected_template_path, mem_path, case_name)
    else:
        expected_snapshot_path.write_text(json.dumps(expected, indent=2), encoding="utf-8")

    payload, sample_count = load_mem_payload(mem_path, args.max_samples)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "mem": str(mem_path),
                    "case_name": case_name,
                    "samples": sample_count,
                    "payload_bytes": len(payload),
                    "expected": expected,
                    "expected_template": str(expected_template_path) if expected is None else None,
                },
                indent=2,
            )
        )
        return 0 if expected is not None else 2

    if not args.uart:
        raise SystemExit("--uart is required unless --dry-run is used")

    serial = import_serial()
    ser = serial.Serial(args.uart, args.baud, timeout=0.1, write_timeout=10)
    monitor = SerialMonitor(ser)
    monitor.start()
    try:
        if args.program:
            rc = program_board(args.bit.resolve(), args.elf.resolve())
            if rc != 0:
                raise RuntimeError(f"XSDB program/download failed with exit code {rc}")
        if not monitor.wait_for("SNN_ECG_FULL_REPLAY_READY", args.ready_timeout):
            transcript_path.write_text(monitor.text(), encoding="utf-8")
            raise TimeoutError(f"board READY marker not seen within {args.ready_timeout}s; transcript saved to {transcript_path}")
        ready_text = monitor.text()
        match = re.search(r"SNN_ECG_FULL_REPLAY_READY total_samples=(\d+)", ready_text)
        board_total = int(match.group(1)) if match else None
        if board_total is not None and sample_count != board_total:
            transcript_path.write_text(ready_text, encoding="utf-8")
            raise RuntimeError(f"sample count mismatch: mem has {sample_count}, board expects {board_total}")
        print(f"board_ready total_samples={board_total}")
        send_payload(ser, monitor, payload, args.flow_chunk_samples, args.progress_samples, args.ack_timeout)
        if monitor.wait_for_any(
            ["SNN_ECG_FULL_REPLAY_BOARD_PASS", "SNN_ECG_FULL_REPLAY_BOARD_FAIL"],
            args.done_timeout,
        ) is None:
            transcript_path.write_text(monitor.text(), encoding="utf-8")
            raise TimeoutError(f"board PASS/FAIL marker not seen within {args.done_timeout}s; transcript saved to {transcript_path}")
    finally:
        time.sleep(0.5)
        monitor.stop()
        ser.close()

    transcript = monitor.text()
    transcript_path.write_text(transcript, encoding="utf-8")
    board = parse_board_values(transcript)
    internal_pass = "SNN_ECG_FULL_REPLAY_BOARD_PASS" in transcript
    rows, pass_match = compare(expected, board, internal_pass)
    write_csv(comparison_path, rows)
    write_summary(summary_path, case_name, mem_path, expected, board, transcript_path, comparison_path, pass_match, internal_pass)
    update_replay_summary(case_name, transcript_path, comparison_path, summary_path, pass_match, internal_pass, board)
    print(
        json.dumps(
            {
                "case_name": case_name,
                "transcript": str(transcript_path),
                "comparison": str(comparison_path),
                "summary": str(summary_path),
                "expected": expected,
                "board": board,
                "board_internal_pass": internal_pass,
                "expected_vs_board_pass": pass_match,
            },
            indent=2,
        )
    )
    return 0 if pass_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
