from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports" / "award_readiness"
FIGURES = REPORTS / "figures"
RESULTS = REPO / "results" / "final_membrane_v2_snn"
DATASET = REPO / "fullrec_afe_30min_annotation_valid_balanced"
MANIFEST = DATASET / "annotation_valid_balanced_30min_manifest.csv"

CLASSES = ["NSR", "CHF", "ARR", "AFF"]
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}
SPLITS = ["train", "val", "test"]


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_snn_module() -> Any:
    return load_module(REPO / "scripts" / "search_final_membrane_v2_snn.py", "award_snn_mod")


def load_arr_module() -> Any:
    return load_module(REPO / "scripts" / "search_final_membrane_v2_arr_focus.py", "award_arr_mod")


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
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def md_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def argmax4(values: list[int]) -> int:
    best = 0
    for idx in range(1, 4):
        if values[idx] > values[best]:
            best = idx
    return best


def margin4(values: list[int]) -> int:
    order = sorted(range(4), key=lambda idx: values[idx], reverse=True)
    return values[order[0]] - values[order[1]]


def load_final_params() -> tuple[dict[str, Any], dict[str, Any]]:
    base = json.loads((RESULTS / "local_rules_seed41031_selected_train_val_locked.json").read_text(encoding="utf-8"))[
        "params"
    ]
    arr = json.loads((RESULTS / "arr_focus_final_test_summary.json").read_text(encoding="utf-8"))["post_params"]
    return base, arr


def split_chunks(splits: Iterable[str] | None = None) -> dict[str, list[Any]]:
    snn_mod = load_snn_module()
    return snn_mod.split_chunks(list(splits) if splits is not None else SPLITS)


def all_chunks() -> list[Any]:
    by_split = split_chunks(SPLITS)
    out: list[Any] = []
    for split in SPLITS:
        out.extend(by_split[split])
    return out


def infer_full_model(
    snn_mod: Any,
    arr_mod: Any,
    chunk: Any,
    base_params: dict[str, Any],
    arr_params: dict[str, Any],
) -> tuple[int, list[int], dict[str, int]]:
    pred, mem, flags = arr_mod.infer_one(snn_mod, chunk, base_params, arr_params)
    fs = chunk.feature_sum
    rescue = int(
        pred == 3
        and margin4(list(mem)) <= 12
        and chunk.pred_count[2] >= 3
        and fs["rdm_code_sum"] >= 512
        and fs["pnn_mismatch_count"] >= 800
        and fs["ectopic_pair_count"] >= 256
        and fs["abnormal_evidence_count"] >= 256
    )
    mem = list(mem)
    if rescue:
        mem[2] += 4
        mem[3] -= 16
        pred = argmax4(mem)
    return pred, mem, {"margin_evidence_rescue": rescue, **{k: int(v) for k, v in flags.items()}}


def infer_many(chunks: list[Any], mode: str = "full") -> tuple[dict[str, int], dict[str, dict[str, Any]]]:
    snn_mod = load_snn_module()
    arr_mod = load_arr_module()
    base_params, arr_params = load_final_params()
    pred: dict[str, int] = {}
    detail: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        if mode == "full":
            y, mem, flags = infer_full_model(snn_mod, arr_mod, chunk, base_params, arr_params)
        elif mode == "base_final":
            y, mem, flags = snn_mod.candidate_predict(chunk, base_params)
            mem = list(mem)
            flags = {f"base_{k}": int(v) for k, v in flags.items()}
        elif mode == "arr_focus_no_margin":
            y, mem, flags = arr_mod.infer_one(snn_mod, chunk, base_params, arr_params)
            mem = list(mem)
            flags = {k: int(v) for k, v in flags.items()}
        elif mode == "snapshot_majority":
            y, mem, flags = chunk.base_pred, list(chunk.pred_count), {}
        elif mode == "snapshot_mem_sum":
            y, mem, flags = argmax4(list(chunk.mem_sum)), list(chunk.mem_sum), {}
        elif mode == "feature_sum_zeroed":
            zeroed = replace(chunk, feature_sum={key: 0 for key in chunk.feature_sum})
            y, mem, flags = infer_full_model(snn_mod, arr_mod, zeroed, base_params, arr_params)
        else:
            raise ValueError(f"unknown inference mode: {mode}")
        key = chunk_key(chunk)
        pred[key] = int(y)
        detail[key] = {"mem": list(mem), "flags": {k: int(v) for k, v in flags.items()}}
    return pred, detail


def metrics(chunks: list[Any], pred: dict[str, int]) -> dict[str, Any]:
    cm = [[0 for _ in CLASSES] for _ in CLASSES]
    for chunk in chunks:
        cm[chunk.class_id][pred[chunk_key(chunk)]] += 1
    total = sum(sum(row) for row in cm)
    correct = sum(cm[idx][idx] for idx in range(4))
    per_class: dict[str, dict[str, float | int]] = {}
    for idx, cls in enumerate(CLASSES):
        tp = cm[idx][idx]
        fp = sum(cm[row][idx] for row in range(4) if row != idx)
        fn = sum(cm[idx][col] for col in range(4) if col != idx)
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


def prediction_rows(chunks: list[Any], pred: dict[str, int], detail: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chunk in chunks:
        key = chunk_key(chunk)
        item = detail.get(key, {}) if detail else {}
        row: dict[str, Any] = {
            "case_id": chunk.case_id,
            "split": chunk.split,
            "class_label": chunk.class_label,
            "class_id": chunk.class_id,
            "record_id": chunk.record_id,
            "chunk_id": chunk.chunk_id,
            "chunk_file": chunk.chunk_file,
            "pred_label": CLASSES[pred[key]],
            "pred_class": pred[key],
            "correct": int(pred[key] == chunk.class_id),
        }
        if "mem" in item:
            for idx, cls in enumerate(CLASSES):
                row[f"final_mem_{cls}"] = item["mem"][idx]
        if "flags" in item:
            row.update(item["flags"])
        rows.append(row)
    return rows


def confusion_rows(metric: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cm = metric["confusion_matrix"]
    for ridx, cls in enumerate(CLASSES):
        row = {"true_label": cls}
        for pidx, pred_cls in enumerate(CLASSES):
            row[pred_cls] = cm[ridx][pidx]
        rows.append(row)
    return rows


def record_counts(chunks: list[Any]) -> dict[str, Counter[str]]:
    out: dict[str, Counter[str]] = {cls: Counter() for cls in CLASSES}
    for chunk in chunks:
        out[chunk.class_label][chunk.record_id] += 1
    return out


def chunk_key(chunk: Any) -> str:
    return f"{chunk.split}:{chunk.case_id}"
