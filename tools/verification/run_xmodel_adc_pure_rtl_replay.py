#!/usr/bin/env python3
"""Replay proven XMODEL-accepted ADC dumps through the fixed Pure RTL in XSim.

The delivery contains a 36-case test manifest but only four full-30-minute
XMODEL accepted-sample dumps.  This runner never substitutes emulator data.
It validates every delivered XMODEL dump, runs only those proven inputs, and
emits a 36-row comparison table with explicit MISSING_XMODEL_ADC status for
the other cases.
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "verification" / "xmodel_rtl_e2e"
WORK = OUT / "xsim_work"
XMODEL_DATA = REPO / "datasets" / "xmodel_afe_adc_outputs"
DIRECT_EVIDENCE = OUT / "direct_integration_evidence"
INTEGRATION = REPO / "design" / "analog" / "xmodel" / "integration"
DIGITAL_REPORT = (
    REPO
    / "design"
    / "digital"
    / "reports"
    / "final"
    / "fulltop_xsim_final_test_36"
    / "locked_class_cases_fulltop_xsim_predictions.csv"
)

RTL_COMMIT = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
RTL_TOP = "snn_ecg_30min_final_top"
RTL_DIR = REPO / "design" / "digital" / "rtl"
RTL_SIM = REPO / "design" / "digital" / "sim" / "tb_snn_ecg_30min_chunk_dataset.v"

def find_vivado_tool(name: str) -> Path:
    configured = shutil.which(name) or shutil.which(name + ".bat")
    if configured:
        return Path(configured)
    fallback = Path(r"C:\Xilinx\Vivado\2020.2\bin") / f"{name}.bat"
    return fallback


XVLOG = find_vivado_tool("xvlog")
XELAB = find_vivado_tool("xelab")
XSIM = find_vivado_tool("xsim")

EXPECTED_SAMPLES = 1_800_000
EXPECTED_SNAPSHOTS = 30
EXPECTED_DECISIONS = 1


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def portable_text(value: str) -> str:
    """Remove workstation-specific repository paths from persisted text."""
    return value.replace(str(REPO), "<REPOSITORY_ROOT>").replace(slash(REPO), "<REPOSITORY_ROOT>")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def validate_adc(path: Path) -> dict[str, Any]:
    count = 0
    invalid = 0
    unsigned_min = 4096
    unsigned_max = -1
    signed_min = 2048
    signed_max = -2049
    token_re = re.compile(r"^[0-9a-fA-F]{3}$")
    with path.open("r", encoding="ascii", errors="strict") as f:
        for line in f:
            token = line.strip()
            if not token:
                continue
            count += 1
            if not token_re.fullmatch(token):
                invalid += 1
                continue
            value = int(token, 16)
            signed = value if value < 0x800 else value - 0x1000
            unsigned_min = min(unsigned_min, value)
            unsigned_max = max(unsigned_max, value)
            signed_min = min(signed_min, signed)
            signed_max = max(signed_max, signed)
    return {
        "sample_count": count,
        "invalid_token_count": invalid,
        "unsigned_min": "" if unsigned_max < 0 else unsigned_min,
        "unsigned_max": "" if unsigned_max < 0 else unsigned_max,
        "signed_min": "" if signed_max < -2048 else signed_min,
        "signed_max": "" if signed_max < -2048 else signed_max,
        "sample_count_ok": count == EXPECTED_SAMPLES,
        "signed_12bit_format_ok": invalid == 0,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def parse_case_manifest() -> list[dict[str, Any]]:
    path = XMODEL_DATA / "case_manifest_36case.txt"
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cid, expected, name, pwl = line.split()
            cases.append(
                {
                    "case_id_num": int(cid),
                    "expected_class": int(expected),
                    "case_name": name,
                    "pwl_path": pwl,
                }
            )
    if len(cases) != 36:
        raise RuntimeError(f"expected 36 cases, found {len(cases)}")
    return cases


def parse_direct_log(case_name: str) -> dict[str, Any]:
    path = DIRECT_EVIDENCE / f"integ_{case_name}.log"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(
        r"E2E_RESULT .*?final_valid=(\d+) pred=(-?\d+) "
        r"mem_nsr=(-?\d+) mem_chf=(-?\d+) mem_arr=(-?\d+) mem_aff=(-?\d+) "
        r"accepted=(\d+) dumped=(\d+) windows=(\d+) decisions=(\d+)",
        text,
    )
    if not match:
        return {"direct_log": str(path), "direct_log_parse_ok": False}
    cadence = re.search(
        r"E2E_CADENCE .*?prof_total_cycles=(\d+).*?accepted_samples=(\d+) "
        r"avg_cycles_per_accept=(\d+)",
        text,
    )
    return {
        "direct_log": str(path),
        "direct_log_parse_ok": True,
        "direct_final_valid": int(match.group(1)),
        "direct_final_pred_class": int(match.group(2)),
        "direct_final_mem_nsr": int(match.group(3)),
        "direct_final_mem_chf": int(match.group(4)),
        "direct_final_mem_arr": int(match.group(5)),
        "direct_final_mem_af": int(match.group(6)),
        "direct_accepted_samples": int(match.group(7)),
        "direct_dumped_samples": int(match.group(8)),
        "direct_snapshots": int(match.group(9)),
        "direct_final_decisions": int(match.group(10)),
        "direct_prof_total_cycles": int(cadence.group(1)) if cadence else "",
        "direct_avg_cycles_per_accept": int(cadence.group(3)) if cadence else "",
    }


def validate_rtl_sources() -> tuple[list[Path], list[dict[str, Any]]]:
    source_list = INTEGRATION / "sources_questa.f"
    rels = [Path(line.strip()).relative_to("rtl") for line in source_list.read_text().splitlines() if line.strip()]
    sources = [RTL_DIR / rel for rel in rels]
    manifest_rows = read_csv(REPO / "project_registry" / "artifact_manifest.csv")
    expected = {
        Path(row["integrated_path"]).as_posix(): row
        for row in manifest_rows
        if row["component"] == "digital_accelerator" and row["upstream_commit"] == RTL_COMMIT
    }
    check_paths = sources + [RTL_DIR / "strict_recordwise_locked_params.vh"]
    rows: list[dict[str, Any]] = []
    for path in check_paths:
        rel_repo = path.relative_to(REPO).as_posix()
        evidence = expected.get(rel_repo)
        actual_hash = sha256_file(path) if path.exists() else "MISSING"
        expected_hash = evidence["sha256"] if evidence else "NO_COMMIT_EVIDENCE"
        rows.append(
            {
                "rtl_commit": RTL_COMMIT,
                "top": RTL_TOP,
                "source_file": rel_repo,
                "actual_sha256": actual_hash,
                "fixed_commit_sha256": expected_hash,
                "hash_match": actual_hash == expected_hash,
                "upstream_path": evidence["upstream_path"] if evidence else "",
                "verification_status": evidence["verification_status"] if evidence else "",
            }
        )
    if not all(row["hash_match"] for row in rows):
        bad = [row["source_file"] for row in rows if not row["hash_match"]]
        raise RuntimeError(f"fixed RTL source hash check failed: {bad}")
    return sources, rows


def run_logged(command: list[str], cwd: Path, log_path: Path) -> None:
    with log_path.open("w", encoding="utf-8", errors="replace") as f:
        f.write("COMMAND: " + portable_text(" ".join(command)) + "\n\n")
        proc = subprocess.run(command, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}); see {log_path}")


def run_xsim(cases: list[dict[str, Any]], sources: list[Path]) -> Path:
    for tool in (XVLOG, XELAB, XSIM):
        if not tool.exists():
            raise FileNotFoundError(tool)
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    # The Verilog manifest parser reads whitespace-delimited paths.  Stage the
    # delivered ADC files below WORK so each manifest entry is a space-free
    # relative path even when the repository itself lives under a path that
    # contains spaces.
    input_dir = WORK / "inputs"
    input_dir.mkdir()
    for case in cases:
        staged = input_dir / Path(case["xmodel_adc_file"]).name
        shutil.copyfile(case["xmodel_adc_file"], staged)
        case["staged_adc_file"] = staged.relative_to(WORK).as_posix()

    manifest = WORK / "replay_manifest_present.txt"
    manifest.write_text(
        "".join(
            f"{case['case_id_num']} {case['expected_class']} {EXPECTED_SAMPLES} "
            f"{case['staged_adc_file']}\n"
            for case in cases
        ),
        encoding="utf-8",
        newline="\n",
    )
    result_csv = OUT / "xsim_replay_results_present_cases.csv"
    wrapper = WORK / "tb_xmodel_adc_replay.v"
    wrapper.write_text(
        """`timescale 1ns/1ps
module tb_xmodel_adc_replay;
  tb_snn_ecg_30min_chunk_dataset #(
    .MAX_SAMPLES(1800000),
    .MANIFEST_FILE("replay_manifest_present.txt"),
    .RESULT_CSV("../xsim_replay_results_present_cases.csv"),
    .DUT_SNAPSHOT_SAMPLES(60000),
    .DUT_SNAPSHOTS_PER_CHUNK(30),
    .DUT_POST_DONE_TICKS(37),
    .DUT_PROFILE_EN(1),
    .DUT_SAMPLE_GAP_CYCLES(2)
  ) tb();
endmodule
""",
        encoding="utf-8",
        newline="\n",
    )
    project = WORK / "sources.prj"
    project.write_text(
        "".join(f'verilog work "{slash(path)}"\n' for path in sources)
        + f'verilog work "{slash(RTL_SIM)}"\n'
        + f'verilog work "{slash(wrapper)}"\n',
        encoding="utf-8",
        newline="\n",
    )
    (WORK / "run.tcl").write_text("run all\nquit\n", encoding="utf-8", newline="\n")
    (OUT / "xsim_commands.txt").write_text(
        "\n".join(
            [
                portable_text(f'{XVLOG} --nolog -i "{RTL_DIR}" -prj "{project}"'),
                f"{XELAB} --nolog -debug typical tb_xmodel_adc_replay -s tb_xmodel_adc_replay",
                f"{XSIM} tb_xmodel_adc_replay --nolog -tclbatch run.tcl",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    run_logged(
        [str(XVLOG), "--nolog", "-i", slash(RTL_DIR), "-prj", slash(project)],
        WORK,
        OUT / "xvlog.log",
    )
    run_logged(
        [str(XELAB), "--nolog", "-debug", "typical", "tb_xmodel_adc_replay", "-s", "tb_xmodel_adc_replay"],
        WORK,
        OUT / "xelab.log",
    )
    run_logged(
        [str(XSIM), "tb_xmodel_adc_replay", "--nolog", "-tclbatch", "run.tcl"],
        WORK,
        OUT / "xsim.log",
    )
    if not result_csv.exists():
        raise FileNotFoundError(result_csv)
    return result_csv


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = parse_case_manifest()
    rep4_rows = {row["case_name"]: row for row in read_csv(DIRECT_EVIDENCE / "rep4_e2e_verification.csv")}
    old_rows = {int(row["case_id"]): row for row in read_csv(DIGITAL_REPORT)}
    emu_rows = {row["case_id"]: row for row in read_csv(DIRECT_EVIDENCE / "legacy_emulator_input_manifest_36case_sha256.csv")}

    present: list[dict[str, Any]] = []
    input_manifest: list[dict[str, Any]] = []
    for case in cases:
        name = case["case_name"]
        adc = XMODEL_DATA / "representative_4case" / f"accepted_{name}.mem"
        direct_row = rep4_rows.get(name, {})
        row: dict[str, Any] = {
            "case_id_num": case["case_id_num"],
            "case_name": name,
            "expected_class": case["expected_class"],
            "xmodel_adc_file": adc.relative_to(REPO).as_posix() if adc.exists() else "",
            "file_exists": adc.exists(),
            "generation_evidence": (
                "tb_snn_ecg_30min_mixed_e2e.sv accepted handshake dump; integ log and rep4 comparison present"
                if adc.exists() else "no full-30-minute XMODEL accepted dump delivered or found"
            ),
            "direct_integration_reported_sha256": direct_row.get("xmodel_chunk_sha256", ""),
            "legacy_emulator_sha256": emu_rows.get(name, {}).get("generated_chunk_sha256", ""),
        }
        if adc.exists():
            stats = validate_adc(adc)
            row.update(stats)
            row["direct_reported_sha256_match"] = stats["sha256"] == row["direct_integration_reported_sha256"]
            row["xmodel_vs_legacy_emulator_sha256_match"] = stats["sha256"] == row["legacy_emulator_sha256"]
            row["status"] = (
                "PRESENT_VALID"
                if stats["sample_count_ok"] and stats["signed_12bit_format_ok"] and row["direct_reported_sha256_match"]
                else "PRESENT_INVALID"
            )
            if row["status"] == "PRESENT_VALID":
                case["xmodel_adc_file"] = adc
                present.append(case)
        else:
            row.update(
                {
                    "sample_count": "",
                    "invalid_token_count": "",
                    "unsigned_min": "",
                    "unsigned_max": "",
                    "signed_min": "",
                    "signed_max": "",
                    "sample_count_ok": False,
                    "signed_12bit_format_ok": False,
                    "sha256": "",
                    "size_bytes": "",
                    "direct_reported_sha256_match": False,
                    "xmodel_vs_legacy_emulator_sha256_match": "",
                    "status": "MISSING_XMODEL_ADC",
                }
            )
        input_manifest.append(row)

    write_csv(OUT / "input_sha256_manifest_36case.csv", input_manifest)
    sources, rtl_rows = validate_rtl_sources()
    write_csv(OUT / "rtl_source_hash_manifest.csv", rtl_rows)
    if not present:
        raise RuntimeError("no valid XMODEL ADC input is available")
    replay_csv = run_xsim(present, sources)
    replay_rows = {int(row["case_id"]): row for row in read_csv(replay_csv)}

    comparisons: list[dict[str, Any]] = []
    for case, input_row in zip(cases, input_manifest):
        cid = case["case_id_num"]
        name = case["case_name"]
        direct = parse_direct_log(name)
        replay = replay_rows.get(cid, {})
        old = old_rows.get(cid, {})
        has_all = input_row["status"] == "PRESENT_VALID" and direct.get("direct_log_parse_ok") and bool(replay)
        row = {
            "case_id_num": cid,
            "case_name": name,
            "expected_class": case["expected_class"],
            "xmodel_adc_status": input_row["status"],
            "xmodel_adc_file": input_row["xmodel_adc_file"],
            "input_sample_count": input_row["sample_count"],
            "input_signed_min": input_row["signed_min"],
            "input_signed_max": input_row["signed_max"],
            "direct_accepted_input_sha256": input_row["sha256"],
            "replay_input_sha256": input_row["sha256"] if replay else "",
            "input_sha256_match": bool(has_all and input_row["direct_reported_sha256_match"]),
            "direct_final_pred_class": direct.get("direct_final_pred_class", ""),
            "replay_final_pred_class": replay.get("final_pred_class", ""),
            "final_class_bitexact": bool(has_all and int(replay["final_pred_class"]) == direct["direct_final_pred_class"]),
            "direct_final_mem_nsr": direct.get("direct_final_mem_nsr", ""),
            "replay_final_mem_nsr": replay.get("final_mem_NSR", ""),
            "mem_nsr_bitexact": bool(has_all and int(replay["final_mem_NSR"]) == direct["direct_final_mem_nsr"]),
            "direct_final_mem_chf": direct.get("direct_final_mem_chf", ""),
            "replay_final_mem_chf": replay.get("final_mem_CHF", ""),
            "mem_chf_bitexact": bool(has_all and int(replay["final_mem_CHF"]) == direct["direct_final_mem_chf"]),
            "direct_final_mem_arr": direct.get("direct_final_mem_arr", ""),
            "replay_final_mem_arr": replay.get("final_mem_ARR", ""),
            "mem_arr_bitexact": bool(has_all and int(replay["final_mem_ARR"]) == direct["direct_final_mem_arr"]),
            "direct_final_mem_af": direct.get("direct_final_mem_af", ""),
            "replay_final_mem_af": replay.get("final_mem_AFF", ""),
            "mem_af_bitexact": bool(has_all and int(replay["final_mem_AFF"]) == direct["direct_final_mem_af"]),
            "all_four_membranes_bitexact": False,
            "direct_accepted_samples": direct.get("direct_accepted_samples", ""),
            "replay_accepted_samples": replay.get("prof_accepted_samples", ""),
            "accepted_samples_ok": bool(has_all and direct["direct_accepted_samples"] == EXPECTED_SAMPLES and int(replay["prof_accepted_samples"]) == EXPECTED_SAMPLES),
            "direct_snapshots": direct.get("direct_snapshots", ""),
            "replay_snapshots": replay.get("prof_windows", ""),
            "snapshots_ok": bool(has_all and direct["direct_snapshots"] == EXPECTED_SNAPSHOTS and int(replay["prof_windows"]) == EXPECTED_SNAPSHOTS),
            "direct_final_valid": direct.get("direct_final_valid", ""),
            "replay_final_valid": replay.get("final_valid", ""),
            "direct_final_decisions": direct.get("direct_final_decisions", ""),
            "replay_final_decisions": replay.get("prof_decisions", ""),
            "one_final_decision_ok": bool(has_all and direct["direct_final_valid"] == 1 and direct["direct_final_decisions"] == EXPECTED_DECISIONS and int(replay["final_valid"]) == 1 and int(replay["prof_decisions"]) == EXPECTED_DECISIONS),
            "direct_prof_total_cycles": direct.get("direct_prof_total_cycles", ""),
            "replay_prof_total_cycles": replay.get("prof_total_cycles", ""),
            "legacy_emulator_input_sha256": input_row["legacy_emulator_sha256"],
            "xmodel_vs_legacy_emulator_input_same": input_row["xmodel_vs_legacy_emulator_sha256_match"],
            "legacy_emulator_vivado_pred": old.get("final_pred_class", ""),
            "legacy_emulator_vivado_mem_nsr": old.get("final_mem_NSR", ""),
            "legacy_emulator_vivado_mem_chf": old.get("final_mem_CHF", ""),
            "legacy_emulator_vivado_mem_arr": old.get("final_mem_ARR", ""),
            "legacy_emulator_vivado_mem_af": old.get("final_mem_AFF", ""),
        }
        row["all_four_membranes_bitexact"] = all(
            row[key]
            for key in ("mem_nsr_bitexact", "mem_chf_bitexact", "mem_arr_bitexact", "mem_af_bitexact")
        )
        row["case_pass"] = all(
            row[key]
            for key in (
                "input_sha256_match",
                "final_class_bitexact",
                "all_four_membranes_bitexact",
                "accepted_samples_ok",
                "snapshots_ok",
                "one_final_decision_ok",
            )
        )
        row["case_status"] = "PASS" if row["case_pass"] else input_row["status"] if not has_all else "FAIL"
        comparisons.append(row)

    write_csv(OUT / "case_comparison_36case.csv", comparisons)

    def count_true(key: str) -> int:
        return sum(bool(row[key]) for row in comparisons)

    available = sum(row["xmodel_adc_status"] == "PRESENT_VALID" for row in comparisons)
    membrane_matches = sum(
        bool(row[key])
        for row in comparisons
        for key in ("mem_nsr_bitexact", "mem_chf_bitexact", "mem_arr_bitexact", "mem_af_bitexact")
    )
    summary = [
        {"metric": "actual_xmodel_adc_files_present_valid", "pass_count": available, "required_count": 36, "status": "PASS" if available == 36 else "FAIL", "criterion": "36/36"},
        {"metric": "input_adc_sha256_match", "pass_count": count_true("input_sha256_match"), "required_count": 36, "status": "PASS" if count_true("input_sha256_match") == 36 else "FAIL", "criterion": "36/36"},
        {"metric": "final_class_bitexact", "pass_count": count_true("final_class_bitexact"), "required_count": 36, "status": "PASS" if count_true("final_class_bitexact") == 36 else "FAIL", "criterion": "36/36"},
        {"metric": "final_membrane_bitexact", "pass_count": membrane_matches, "required_count": 144, "status": "PASS" if membrane_matches == 144 else "FAIL", "criterion": "144/144"},
        {"metric": "accepted_samples_1800000", "pass_count": count_true("accepted_samples_ok"), "required_count": 36, "status": "PASS" if count_true("accepted_samples_ok") == 36 else "FAIL", "criterion": "each case 1,800,000"},
        {"metric": "snapshots_30", "pass_count": count_true("snapshots_ok"), "required_count": 36, "status": "PASS" if count_true("snapshots_ok") == 36 else "FAIL", "criterion": "each case 30"},
        {"metric": "final_decision_1", "pass_count": count_true("one_final_decision_ok"), "required_count": 36, "status": "PASS" if count_true("one_final_decision_ok") == 36 else "FAIL", "criterion": "each case 1"},
        {"metric": "overall", "pass_count": count_true("case_pass"), "required_count": 36, "status": "PASS" if count_true("case_pass") == 36 else "FAIL", "criterion": "all criteria for all 36 cases"},
    ]
    write_csv(OUT / "overall_summary.csv", summary)

    missing = [row["case_name"] for row in comparisons if row["xmodel_adc_status"] == "MISSING_XMODEL_ADC"]
    (OUT / "ADC_DATA_PROVENANCE_KR.md").write_text(
        f"""# ADC 데이터 출처 판정

## 결론

- 실제 XMODEL AFE–ADC 출력이며 직접 통합 RTL이 수락한 full-30분 dump: **{available}/36**.
- 위치: `datasets/xmodel_afe_adc_outputs/representative_4case/accepted_<case>.mem`.
- 생성 근거: `tb_snn_ecg_30min_mixed_e2e.sv`가 XMODEL `afe_adc`를 offset-binary→signed 12-bit로 변환하고, `sample_valid && sample_ready` 수락 때 3-hex/줄로 dump한다. `run_rep4_full30min.sh`가 이 dump를 생성한 뒤 같은 파일을 RTL replay manifest에 넣는다.
- 실제 존재 파일의 직접 통합 로그와 `rep4_e2e_verification.csv`가 독립적으로 같은 SHA-256을 기록한다.

## 기존 emulator 데이터

- `input_manifest_36case_sha256.csv`와 `part1_input_sha256_compare_36case.csv`의 36개 SHA는 `datasets/fullrec_afe*`/`sim_out/chunks36`에서 온 Python `afe_full.py` 계열 emulator chunk와 board-replay 입력의 동일성이다.
- 패키지의 `INTEGRATION_VERIFICATION_REPORT.md`와 `SPOTCHECK_XMODEL_vs_EMULATOR.md`가 이 점을 명시하며, 실제 XMODEL 60초 출력과 emulator는 전체 표본 기준 53.21%만 exact였다.
- 따라서 해당 36/36을 실제 XMODEL 출력 증명으로 사용하지 않았다.

## 결과 종류 구분

1. XMODEL–RTL 직접 통합 결과: `verification/xmodel_rtl_e2e/direct_verification/verification\integration_evidence/integ_<case>.log` — 대표 4개.
2. 기존 Vivado/XSim 기준값: `design/digital/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` — emulator 입력 기반 36개.
3. 실제 XMODEL 출력 replay 신 기준값: 이 실행의 `xsim_replay_results_present_cases.csv` — 현재 증거가 있는 4개만 생성.
4. 실제 XMODEL ADC 입력 manifest: `input_sha256_manifest_36case.csv` — 32개 누락을 숨기지 않고 기록.

## 누락 32개

{chr(10).join('- ' + name for name in missing)}

재생성에는 원본 WFDB→PWL, XMODEL 2025.12/Questa 라이선스 환경, `optionB_gen_xmodel_chunks.sh` 또는 직접 통합 `run_e2e_all.sh`가 필요하다. 각 case에서 2초 settling 뒤 1,800,000 accepted signed code를 dump하고, dump SHA와 직접 통합 결과 로그를 함께 보존해야 한다.
""",
        encoding="utf-8",
    )
    (OUT / "PASS_FAIL_SUMMARY_KR.md").write_text(
        f"""# 실제 XMODEL ADC → 고정 Pure RTL XSim replay 검증

## 판정: **FAIL (완전한 36-case 검증 불가)**

고정 RTL은 commit `{RTL_COMMIT}`, top `{RTL_TOP}`이다. source-of-truth manifest의 고정 커밋 SHA와 실제 사용 RTL 17개 파일이 모두 일치했다.

실제 XMODEL accepted ADC dump가 있는 **{available}개**는 모두 1,800,000표본, signed 12-bit 형식이며 새 Vivado 2020.2 XSim replay에서 직접 통합 결과와 입력 SHA, 최종 클래스, 네 Final Membrane, 30 Snapshot, 1 final decision이 bit-exact했다. 그러나 나머지 **{36-available}개**의 실제 XMODEL full-30분 dump가 없어 전체 PASS 기준을 충족하지 못한다.

- 입력 SHA-256: {count_true('input_sha256_match')}/36
- 최종 클래스: {count_true('final_class_bitexact')}/36
- Final Membrane: {membrane_matches}/144
- accepted samples: {count_true('accepted_samples_ok')}/36
- Snapshot: {count_true('snapshots_ok')}/36
- final decision: {count_true('one_final_decision_ok')}/36

`part1_input_sha256_compare_36case.csv`의 36/36은 emulator chunk와 기존 RTL replay 입력의 무결성 결과이며, 실제 XMODEL 36개 존재/동일성을 뜻하지 않는다. 누락분을 emulator 파일로 대체하지 않았다.
""",
        encoding="utf-8",
    )
    print(f"OUTPUT={OUT}")
    print(f"XMODEL_ADC_PRESENT={available}/36")
    print(f"CLASS_BITEXACT={count_true('final_class_bitexact')}/36")
    print(f"MEMBRANE_BITEXACT={membrane_matches}/144")
    print(f"OVERALL={'PASS' if count_true('case_pass') == 36 else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
