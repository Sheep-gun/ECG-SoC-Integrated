from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
DATASET = REPO / "fullrec_afe_30min_annotation_valid_balanced"
SOURCE_MANIFEST = DATASET / "annotation_valid_balanced_30min_manifest.csv"
RESULTS = REPO / "results" / "final_membrane_v2_snn"

RUN_ID = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in os.environ.get("RECORDWISE_RUN_ID", "").strip())
BASE_REPORTS = REPO / "reports" / "strict_recordwise"
REPORTS = BASE_REPORTS if not RUN_ID else REPO / "reports" / f"strict_recordwise_{RUN_ID}"
CONFIGS = REPO / "configs" / ("recordwise" if not RUN_ID else f"recordwise_{RUN_ID}")
GENERATED = REPO / "generated"

CLASSES = ["NSR", "CHF", "ARR", "AFF"]
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}
SPLITS = ["train", "val", "test"]
CLASS_DB_DEFAULT = {"NSR": "nsrdb", "CHF": "chfdb", "ARR": "mitdb", "AFF": "afdb"}

TEXT_ENCODING = "utf-8"


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
    with path.open("w", newline="", encoding=TEXT_ENCODING) as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding=TEXT_ENCODING)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding=TEXT_ENCODING))


def md_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def stable_bucket(text: str, seed: str | int) -> int:
    digest = hashlib.sha256(f"{seed}:{text}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def git_hash() -> str:
    candidates = [
        REPO / ".git" / "unused",
        Path(r"C:\Users\YangGeon\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"),
        Path(r"C:\Users\YangGeon\AppData\Local\GitHubDesktop\app-3.6.2\resources\app\git\cmd\git.exe"),
        Path("git"),
    ]
    for git in candidates:
        try:
            proc = subprocess.run(
                [str(git), "rev-parse", "HEAD"],
                cwd=REPO,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            return proc.stdout.strip()
        except Exception:
            continue
    return "unknown"


def source_db_for(row: dict[str, str]) -> str:
    raw = (row.get("source_db") or "").strip()
    if raw:
        return raw
    return CLASS_DB_DEFAULT.get(row.get("class_label", ""), "unknown")


def make_source_record_id(class_label: str, source_db: str, record_id: str) -> str:
    return f"{class_label}_{source_db}_{record_id}"


def norm_rel(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip()


def manifest_path() -> Path:
    path = REPORTS / "recordwise_manifest.csv"
    if path.exists():
        return path
    return BASE_REPORTS / "recordwise_manifest.csv"


def split_csv_path() -> Path:
    return REPORTS / "strict_recordwise_split.csv"


def split_json_path(seed: int | str = 2026) -> Path:
    return CONFIGS / f"strict_recordwise_split_seed{seed}.json"


def load_recordwise_manifest(path: Path | None = None) -> list[dict[str, str]]:
    return read_csv(path or manifest_path())


def load_strict_split(path: Path | None = None) -> list[dict[str, str]]:
    return read_csv(path or split_csv_path())


def class_counts(rows: list[dict[str, str]], split_col: str | None = None) -> dict[str, Counter[str]]:
    out: dict[str, Counter[str]] = {cls: Counter() for cls in CLASSES}
    for row in rows:
        cls = row["class_label"]
        key = row[split_col] if split_col else "all"
        out[cls][key] += 1
    return out


def load_module(path: Path, name: str) -> Any:
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_snapshot_module() -> Any:
    return load_module(REPO / "scripts" / "snapshot_c24_v2_search.py", "strict_snapshot_c24_v2_search")


def load_final_module() -> Any:
    return load_module(REPO / "scripts" / "search_final_membrane_v2_snn.py", "strict_final_membrane_v2_snn")


def metric_from_pairs(true_ids: list[int], pred_ids: list[int]) -> dict[str, Any]:
    cm = [[0 for _ in CLASSES] for _ in CLASSES]
    for truth, pred in zip(true_ids, pred_ids):
        cm[int(truth)][int(pred)] += 1
    total = sum(sum(row) for row in cm)
    correct = sum(cm[i][i] for i in range(4))
    per_class: dict[str, dict[str, float | int]] = {}
    for idx, cls in enumerate(CLASSES):
        tp = cm[idx][idx]
        fp = sum(cm[r][idx] for r in range(4) if r != idx)
        fn = sum(cm[idx][c] for c in range(4) if c != idx)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cls] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(cm[idx])}
    recalls = [float(per_class[cls]["recall"]) for cls in CLASSES]
    return {
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "macro_f1": sum(float(per_class[cls]["f1"]) for cls in CLASSES) / 4.0 if total else 0.0,
        "balanced_accuracy": sum(recalls) / 4.0 if recalls else 0.0,
        "min_recall": min(recalls) if recalls else 0.0,
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def confusion_rows(metric: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cm = metric["confusion_matrix"]
    for ridx, cls in enumerate(CLASSES):
        row: dict[str, Any] = {"true_label": cls}
        for pidx, pred_cls in enumerate(CLASSES):
            row[pred_cls] = cm[ridx][pidx]
        rows.append(row)
    return rows


def load_all_window_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for original_split in SPLITS:
        path = RESULTS / f"window_dump_{original_split}.csv"
        for row in read_csv(path):
            item: dict[str, Any] = dict(row)
            item["original_window_split"] = original_split
            item["original_case_id"] = row.get("case_id", "")
            rows.append(item)
    return rows


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def enrich_snapshot_features(row: dict[str, Any]) -> dict[str, Any]:
    pnn_match = to_int(row.get("pnn_match_count"))
    pnn_mismatch = to_int(row.get("pnn_mismatch_count"))
    pnn_total = pnn_match + pnn_mismatch
    row["pnn_mismatch_rate_pct"] = 100.0 * pnn_mismatch / pnn_total if pnn_total else 0.0

    rdm_count = to_int(row.get("rdm_valid_count"))
    ram_count = to_int(row.get("ram_code_count"))
    row["rdm_avg"] = to_int(row.get("rdm_code_sum")) / rdm_count if rdm_count else to_int(row.get("rdm_avg_code_q8")) / 256.0
    row["ram_avg"] = to_int(row.get("ram_code_sum")) / ram_count if ram_count else to_int(row.get("ram_avg_code_q8")) / 256.0

    if row.get("qrs_maf_rate_bp") not in (None, ""):
        row["qrs_maf_rate_pct"] = to_int(row.get("qrs_maf_rate_bp")) / 100.0
    else:
        valid = to_int(row.get("qrs_maf_valid_count"))
        row["qrs_maf_rate_pct"] = 100.0 * to_int(row.get("qrs_maf_count")) / valid if valid else 0.0
    return row


def strict_rows_from_split(split_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_chunk = {norm_rel(row["chunk_file"]): row for row in split_rows}
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for row in load_all_window_rows():
        key = norm_rel(row["chunk_file"])
        meta = by_chunk.get(key)
        if meta is None:
            missing.append(key)
            continue
        item = dict(row)
        item["case_id"] = meta["strict_case_id"]
        item["split"] = meta["split"]
        item["strict_split"] = meta["split"]
        item["source_record_id"] = meta["source_record_id"]
        item["physical_record_id"] = meta.get("physical_record_id", "")
        item["source_database"] = meta["source_database"]
        item["mem_path"] = meta["mem_path"]
        item["original_case_id"] = row.get("case_id", "")
        rows.append(enrich_snapshot_features(item))
    if missing:
        raise RuntimeError(f"{len(missing)} window rows missing from strict split; first={missing[0]}")
    return rows


def record_lists_from_split(split_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    out = {split: sorted({row["source_record_id"] for row in split_rows if row["split"] == split}) for split in SPLITS}
    return out


def write_log(script_name: str, argv: list[str], outputs: list[Path], extra: dict[str, Any] | None = None) -> None:
    payload = {
        "script": script_name,
        "argv": argv,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_hash(),
        "cwd": str(REPO),
        "outputs": [str(path.relative_to(REPO)) if path.is_absolute() else str(path) for path in outputs],
        "extra": extra or {},
    }
    path = REPORTS / "logs" / f"{script_name}.json"
    write_json(path, payload)
