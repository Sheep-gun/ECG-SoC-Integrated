from pathlib import Path
import csv
import importlib.util
import json
import re
import sys

import numpy as np


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def csv_write(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def sv64(v):
    v = int(v)
    return f"-64'sd{abs(v)}" if v < 0 else f"64'sd{v}"


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_c24_spike_fold.py <workspace> <contest_root>")
    ws = Path(sys.argv[1])
    root = Path(sys.argv[2])
    out = ws / "results" / "c24_rtl_equivalence"
    out.mkdir(parents=True, exist_ok=True)

    fast = load_module("fast_readout_curated", root / "afe_model_s_eval" / "tune_afe_model_s_global_snn_readout_fast.py")
    cur = load_module("curated_readout", root / "afe_model_s_eval" / "tune_xmodelmatch_curated_v2_global.py")

    qrs_tag = "e5w8t16l0r280a1b1c2000tc100_c24"
    profile = [p for p in cur.profiles() if p["name"] == "compact"][0]
    count_scale = 10.0
    base_scale = 25000.0
    l2 = 1000.0
    boosts = {0: 1.1, 1: 1.8, 2: 1.8, 3: 1.0}
    q = 100000000
    classes = fast.CLASSES

    def val(row, key):
        x = row.get(key, "")
        return float(x) if x not in ("", None) else 0.0

    data = {s: cur.load_split(s, qrs_tag) for s in ["train", "val", "test"]}
    xtr_raw, names = fast.build_X(data["train"]["rows"], {**profile, "count_scale": count_scale})
    mean = xtr_raw.mean(axis=0)
    std = xtr_raw.std(axis=0)
    std[std < 1e-6] = 1.0
    coef = fast.fit_ridge(
        fast.add_base_features((xtr_raw - mean) / std, data["train"]["base"], base_scale),
        data["train"]["y"],
        l2,
        boosts,
    )
    all_names = names + [f"base_{c}" for c in classes]

    fold_w = []
    for j, name in enumerate(all_names):
        if name.startswith("base_"):
            w = coef[j] / base_scale
        else:
            w = coef[j] / std[j]
            if name.startswith("event_"):
                w /= count_scale
        fold_w.append(np.rint(w * q).astype(np.int64))
    fold_w = np.array(fold_w, dtype=np.int64)

    fold_b_float = coef[-1].copy()
    for j in range(len(names)):
        fold_b_float -= (mean[j] / std[j]) * coef[j]
    fold_b = np.rint(fold_b_float * q).astype(np.int64)
    fw = {name: fold_w[i] for i, name in enumerate(all_names)}
    base_w = fold_w[-4:, :]

    raw_bias = np.array([-5213, -22414, -7298, 32767], dtype=np.int64)
    raw = {
        "pnn_match": [-100, 418, -746, 427],
        "pnn_mis": [-955, 650, -643, 948],
        "dscr_flip": [650, -531, 0, 0],
        "dscr_slope": [-21, 9, 0, 0],
        "ram_count": [0, 0, -987, 577],
        "ram_code": [0, 0, -23, -92],
        "rdm_valid": [-514, 703, -1059, 871],
        "rdm_code": [-16, -12, 18, 10],
        "ect_pair": [976, 1663, 328, -2967],
        "qrs_width": [-2700, -2500, 2600, 700],
        "qrs_complex": [-400, -2100, -200, 2500],
        "qrs_energy": [-500, 2900, -1300, -2700],
        "sec": [1903, 802, -424, -2281],
        "arr_high": [0, 0, 40000, 0],
        "rbbb_delay": [-100000, 0, 100000, 0],
        "rbbb_late": [-150000, 0, 150000, 0],
        "eerg": [0, 0, 25000, 0],
        "zero": [0, 0, 0, 0],
    }
    rdm_ge = np.array(
        [
            [-2616, -2595, 5000, 211],
            [458, -730, 876, -603],
            [2094, 683, -2054, -723],
            [-467, 773, -356, 51],
            [-53, -116, -183, 351],
            [1765, -533, -1500, 268],
            [1287, -390, -909, 12],
            [-733, 135, 453, 144],
            [-637, 343, -205, 499],
            [-665, 354, -709, 1021],
            [-1000, 192, 243, 566],
            [-992, 564, -358, 787],
            [-1484, 904, 189, 391],
            [-1536, 267, 940, 329],
            [-2372, -1037, 3099, 310],
        ],
        dtype=np.int64,
    )

    def bt(vec):
        return np.array(vec, dtype=np.int64) @ base_w

    init_mem = fold_b + bt(raw_bias)
    event = {
        "PNN_MATCH": fw["event_pnn_match_count"] + bt(raw["pnn_match"]),
        "PNN_MIS": fw["event_pnn_mismatch_count"] + bt(raw["pnn_mis"]),
        "DSCR_FLIP": fw["event_dscr_flip_count"] + bt(raw["dscr_flip"]),
        "DSCR_SLOPE": fw["event_dscr_slope_count"] + bt(raw["dscr_slope"]),
        "RAM_COUNT": fw["event_ram_code_count"] + bt(raw["ram_count"]),
        "RAM_CODE": fw["event_ram_code_sum"] + bt(raw["ram_code"]),
        "RDM_VALID": fw["event_rdm_valid_count"] + bt(raw["rdm_valid"]),
        "RDM_CODE": fw["event_rdm_code_sum"] + bt(raw["rdm_code"]),
        "ECT_PAIR": fw["event_ectopic_pair_count"] + bt(raw["ect_pair"]),
        "PRE_QRS": fw["event_pre_qrs_bump_count"],
        "QRS_MAF": fw["event_qrs_maf_count"],
        "QRS_WIDTH": fw["event_qrs_width_abn_count"] + bt(raw["qrs_width"]),
        "QRS_COMPLEX": bt(raw["qrs_complex"]),
        "QRS_ENERGY": fw["event_qrs_energy_abn_count"] + bt(raw["qrs_energy"]),
        "SECOND": bt(raw["sec"]),
        "RBBB_LIKE": fw["event_rbbb_delay_like_count"],
        "RBBB_SEGMENT": fw["event_rbbb_delay_segment_count"],
        "RBBB_APPLIED": fw["event_rbbb_delay_applied_count"] + bt(raw["rbbb_delay"]),
        "RBBB_LATE_APPLIED": bt(raw["rbbb_late"]),
        "EERG_GATE": fw["event_eerg_gate_count"],
        "EERG_APPLIED": fw["event_eerg_applied_count"] + bt(raw["eerg"]),
        "ARR_HIGH_IRR": bt(raw["arr_high"]),
        "ETMC": bt(raw["zero"]),
        "RCD": bt(raw["zero"]),
        "RCD2": bt(raw["zero"]),
        "IPB_PERSIST": bt(raw["zero"]),
        "IPB_EPISODIC": bt(raw["zero"]),
        "IPB_BURST": bt(raw["zero"]),
    }
    rdm_level = np.array([bt(rdm_ge[i]) for i in range(15)], dtype=np.int64)

    continuous = {
        "event_pnn_match_count",
        "event_pnn_mismatch_count",
        "event_dscr_flip_count",
        "event_dscr_slope_count",
        "event_ram_code_sum",
        "event_ram_code_count",
        "event_rdm_valid_count",
        "event_rdm_code_sum",
        "event_ectopic_pair_count",
        "event_pre_qrs_bump_count",
        "event_qrs_maf_count",
        "event_qrs_width_abn_count",
        "event_qrs_energy_abn_count",
        "event_rbbb_delay_like_count",
        "event_rbbb_delay_segment_count",
        "event_rbbb_delay_applied_count",
        "event_eerg_gate_count",
        "event_eerg_applied_count",
        "base_NSR",
        "base_CHF",
        "base_ARR",
        "base_AFF",
    }
    binary_names = [n for n in all_names if n not in continuous]

    def ge_pct(n, d, th):
        return d != 0 and n * 100 >= th * d

    def le_pct(n, d, th):
        return d == 0 or n * 100 <= th * d

    def ge_avg(s, d, th):
        return d != 0 and s >= th * d

    def le_avg(s, d, th):
        return d == 0 or s <= th * d

    def add_binary(mem, row):
        beat = int(val(row, "beat_count"))
        pnn_match = int(val(row, "pnn_match_count"))
        pnn_mis = int(val(row, "pnn_mismatch_count"))
        pnn_den = pnn_match + pnn_mis
        rdm_n = int(val(row, "rdm_valid_count"))
        rdm_sum = int(val(row, "rdm_code_sum"))
        dscr_flip = int(val(row, "dscr_flip_count"))
        dscr_slope = int(val(row, "dscr_slope_count"))
        ram_sum = int(val(row, "ram_code_sum"))
        ram_n = int(val(row, "ram_code_count"))
        qrs_valid = int(val(row, "qrs_maf_valid_count"))
        rbbb_valid = int(val(row, "rbbb_delay_valid_count"))
        ecp = int(val(row, "ectopic_pair_count"))
        pre = int(val(row, "pre_qrs_bump_count"))
        qrs = int(val(row, "qrs_maf_count"))
        qrs_width = int(val(row, "qrs_width_abn_count"))
        qrs_energy = int(val(row, "qrs_energy_abn_count"))
        rbbb_like = int(val(row, "rbbb_delay_like_count"))
        rbbb_wide = int(val(row, "rbbb_delay_wide_count"))
        rbbb_term = int(val(row, "rbbb_delay_terminal_count"))
        conds = []
        for th in profile["pnn_ge"]:
            conds.append((f"pnn_mis_ge_{th:g}", ge_pct(pnn_mis, pnn_den, th)))
        for th in profile["pnn_le"]:
            conds.append((f"pnn_mis_le_{th:g}", le_pct(pnn_mis, pnn_den, th)))
        for th in profile["rdm_ge"]:
            conds.append((f"rdm_avg_ge_{th:g}", ge_avg(rdm_sum, rdm_n, th)))
        for th in profile["rdm_le"]:
            conds.append((f"rdm_avg_le_{th:g}", le_avg(rdm_sum, rdm_n, th)))
        for key, num in [
            ("rdm_ge20", int(val(row, "rdm_ge20_count"))),
            ("rdm_ge50", int(val(row, "rdm_ge50_count"))),
            ("rdm_ge80", int(val(row, "rdm_ge80_count"))),
            ("rdm_ge100", int(val(row, "rdm_ge100_count"))),
        ]:
            for th in profile["rate_ge"]:
                conds.append((f"{key}_ge_{th:g}", ge_pct(num, rdm_n, th)))
        for th in profile["dscr_ge"]:
            conds.append((f"dscr_ge_{th:g}", ge_pct(dscr_flip, dscr_slope, th)))
        for th in profile["dscr_le"]:
            conds.append((f"dscr_le_{th:g}", le_pct(dscr_flip, dscr_slope, th)))
        for th in profile["ram_ge"]:
            conds.append((f"ram_ge_{th:g}", ge_avg(ram_sum, ram_n, th)))
        for th in profile["ram_le"]:
            conds.append((f"ram_le_{th:g}", le_avg(ram_sum, ram_n, th)))
        for th in profile["ecp_ge"]:
            conds.append((f"ecp_ge_{th:g}", ge_pct(ecp, beat, th)))
        for th in profile["pre_ge"]:
            conds.append((f"pre_ge_{th:g}", ge_pct(pre, beat, th)))
        for th in profile["qrs_ge"]:
            conds.append((f"qrs_ge_{th:g}", ge_pct(qrs, qrs_valid, th)))
        for th in profile["qrs_width_ge"]:
            conds.append((f"qrs_width_ge_{th:g}", ge_pct(qrs_width, qrs_valid, th)))
        for th in profile["qrs_energy_ge"]:
            conds.append((f"qrs_energy_ge_{th:g}", ge_pct(qrs_energy, qrs_valid, th)))
        for th in profile["rbbb_ge"]:
            conds.append((f"rbbb_ge_{th:g}", ge_pct(rbbb_like, beat, th)))
        for th in profile["rbbb_ge"]:
            conds.append((f"rbbb_wide_ge_{th:g}", ge_pct(rbbb_wide, rbbb_valid, th)))
        for th in profile["rbbb_ge"]:
            conds.append((f"rbbb_terminal_ge_{th:g}", ge_pct(rbbb_term, rbbb_valid, th)))
        conds += [
            ("gate_regular_rbbb_rescue", le_pct(pnn_mis, pnn_den, 15) and ge_pct(rbbb_like, beat, 2)),
            ("gate_regular_qrs_arr_rescue", le_pct(pnn_mis, pnn_den, 15) and (ge_pct(qrs_width, qrs_valid, 2) or ge_pct(qrs_energy, qrs_valid, 35))),
            ("gate_episodic_ectopic_arr", ge_pct(ecp, beat, 3) and le_pct(pnn_mis, pnn_den, 35) and le_avg(rdm_sum, rdm_n, 8)),
            ("gate_eerg_like", rbbb_like == 0 and pre >= 1 and (int(val(row, "eerg_early_count")) >= 10 or int(val(row, "eerg_ecp_count")) >= 3) and le_pct(int(val(row, "eerg_pnn_mismatch_count")), int(val(row, "eerg_pnn_decision_count")), 15) and le_avg(int(val(row, "eerg_rdm_code_sum")), int(val(row, "eerg_rdm_valid_count")), 5)),
            ("gate_aff_persistent_irreg", ge_pct(pnn_mis, pnn_den, 25) and ge_avg(rdm_sum, rdm_n, 7) and ge_pct(ecp, beat, 5)),
            ("gate_arr_mid_irreg", ge_pct(pnn_mis, pnn_den, 5) and le_pct(pnn_mis, pnn_den, 30) and ge_avg(rdm_sum, rdm_n, 2) and le_avg(rdm_sum, rdm_n, 9)),
            ("gate_chf_low_dscr_low_irreg", le_pct(dscr_flip, dscr_slope, 3) and le_pct(pnn_mis, pnn_den, 20)),
            ("gate_nsr_high_dscr_low_irreg", ge_pct(dscr_flip, dscr_slope, 5) and le_pct(pnn_mis, pnn_den, 15) and le_avg(rdm_sum, rdm_n, 5)),
            ("gate_ram_high_regular", ge_avg(ram_sum, ram_n, 10) and le_pct(pnn_mis, pnn_den, 20)),
            ("gate_ram_low_irregular", le_avg(ram_sum, ram_n, 5) and ge_pct(pnn_mis, pnn_den, 15)),
        ]
        for name, cond in conds:
            if cond:
                mem = mem + fw[name]
        return mem

    def spike_mem(row):
        mem = init_mem.copy()
        mem += int(val(row, "pnn_match_count")) * event["PNN_MATCH"]
        mem += int(val(row, "pnn_mismatch_count")) * event["PNN_MIS"]
        mem += int(val(row, "dscr_flip_count")) * event["DSCR_FLIP"]
        mem += int(val(row, "dscr_slope_count")) * event["DSCR_SLOPE"]
        mem += int(val(row, "ram_code_count")) * event["RAM_COUNT"] + int(val(row, "ram_code_sum")) * event["RAM_CODE"]
        mem += int(val(row, "rdm_valid_count")) * event["RDM_VALID"] + int(val(row, "rdm_code_sum")) * event["RDM_CODE"]
        for i in range(15):
            mem += int(val(row, f"rdm_ge{(i + 1) * 10}_count")) * rdm_level[i]
        mem += int(val(row, "ectopic_pair_count")) * event["ECT_PAIR"]
        mem += int(val(row, "pre_qrs_bump_count")) * event["PRE_QRS"]
        mem += int(val(row, "qrs_maf_count")) * event["QRS_MAF"]
        mem += int(val(row, "qrs_width_abn_count")) * event["QRS_WIDTH"]
        mem += int(val(row, "qrs_complex_abn_count")) * event["QRS_COMPLEX"]
        mem += int(val(row, "qrs_energy_abn_count")) * event["QRS_ENERGY"]
        mem += 60 * event["SECOND"]
        mem += int(val(row, "rbbb_delay_like_count")) * event["RBBB_LIKE"]
        mem += int(val(row, "rbbb_delay_segment_count")) * event["RBBB_SEGMENT"]
        mem += int(val(row, "rbbb_delay_applied_count")) * event["RBBB_APPLIED"]
        mem += int(val(row, "eerg_gate_count")) * event["EERG_GATE"]
        mem += int(val(row, "eerg_applied_count")) * event["EERG_APPLIED"]
        pden = int(val(row, "pnn_match_count")) + int(val(row, "pnn_mismatch_count"))
        pmis = int(val(row, "pnn_mismatch_count"))
        rn = int(val(row, "rdm_valid_count"))
        rsum = int(val(row, "rdm_code_sum"))
        ramn = int(val(row, "ram_code_count"))
        rams = int(val(row, "ram_code_sum"))
        ecp = int(val(row, "ectopic_pair_count"))
        if pden and pmis * 100 >= 12 * pden and pmis * 100 <= 65 * pden and rn and rsum >= 5 * rn and rsum <= 12 * rn and ramn and rams >= 12 * ramn and ecp * 100 >= 4 * rn and ecp * 100 <= 35 * rn:
            mem += event["ARR_HIGH_IRR"]
        return add_binary(mem, row)

    def fixed_direct(split):
        rows = data[split]["rows"]
        xraw, _ = fast.build_X(rows, {**profile, "count_scale": count_scale})
        vals = []
        for i, row in enumerate(rows):
            v = []
            for j, name in enumerate(names):
                v.append(xraw[i, j] * count_scale if name.startswith("event_") else xraw[i, j])
            v.extend(data[split]["base"][i].tolist())
            vals.append(v)
        return np.array(vals, dtype=np.float64) @ fold_w + fold_b

    repro = {
        "qrs_tag": qrs_tag,
        "profile": "compact",
        "count_scale": count_scale,
        "base_scale": base_scale,
        "l2": l2,
        "boosts": boosts,
        "Q": q,
        "metrics": {},
    }
    fold_rows = []
    fixed_rows = []
    for split in ["train", "val", "test"]:
        rows = data[split]["rows"]
        xraw, _ = fast.build_X(rows, {**profile, "count_scale": count_scale})
        flt = fast.add_base_features((xraw - mean) / std, data[split]["base"], base_scale) @ coef[:-1] + coef[-1]
        float_pred = np.argmax(flt, axis=1)
        fixed = fixed_direct(split)
        fixed_pred = np.argmax(fixed, axis=1)
        spike = np.vstack([spike_mem(row) for row in rows])
        spike_pred = np.argmax(spike, axis=1)
        y = data[split]["y"]
        repro["metrics"][split] = {
            "segment_correct": int((float_pred == y).sum()),
            "segment_total": int(len(rows)),
            "segment_accuracy": float((float_pred == y).mean()),
            "class_correct": {classes[i]: int(((float_pred == i) & (y == i)).sum()) for i in range(4)},
            "float_vs_fixed_pred_mismatch": int((float_pred != fixed_pred).sum()),
            "fixed_vs_spike_pred_mismatch": int((fixed_pred != spike_pred).sum()),
        }
        for i, row in enumerate(rows):
            base = {
                "split": split,
                "case_id": row["case_id"],
                "label": row.get("label", ""),
                "expected_class": int(y[i]),
                "global_pred": int(float_pred[i]),
                "fixed_pred": int(fixed_pred[i]),
                "spike_folded_pred": int(spike_pred[i]),
            }
            fold_rows.append({**base, "global_vs_spike_mismatch": int(float_pred[i] != spike_pred[i])})
            fixed_rows.append({**base, "global_vs_fixed_mismatch": int(float_pred[i] != fixed_pred[i]), "fixed_vs_spike_mismatch": int(fixed_pred[i] != spike_pred[i])})

    (out / "c24_global_readout_reproduce.json").write_text(json.dumps(repro, indent=2), encoding="utf-8")
    csv_write(out / "c24_folded_weight_equivalence.csv", fold_rows)
    csv_write(out / "c24_fixed_point_equivalence.csv", fixed_rows)
    (out / "c24_folded_weights_for_rtl.json").write_text(
        json.dumps(
            {
                "Q": q,
                "folded_bias_before_base": {classes[i]: int(fold_b[i]) for i in range(4)},
                "c24_mem_init": {classes[i]: int(init_mem[i]) for i in range(4)},
                "base_weight_per_raw_score": {f"base_{classes[r]}": {classes[c]: int(base_w[r, c]) for c in range(4)} for r in range(4)},
                "continuous_event_weights": {name: {classes[i]: int(vec[i]) for i in range(4)} for name, vec in event.items()},
                "rdm_level_weights": {f"rdm_ge{(i + 1) * 10}": {classes[c]: int(rdm_level[i, c]) for c in range(4)} for i in range(15)},
                "binary_feature_weights": {name: {classes[i]: int(fw[name][i]) for i in range(4)} for name in binary_names},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    def const4(prefix, vec):
        return "\n".join(
            [
                f"    localparam signed [63:0] C24_W_{prefix}_NSR = {sv64(vec[0])};",
                f"    localparam signed [63:0] C24_W_{prefix}_CHF = {sv64(vec[1])};",
                f"    localparam signed [63:0] C24_W_{prefix}_ARR = {sv64(vec[2])};",
                f"    localparam signed [63:0] C24_W_{prefix}_AFF = {sv64(vec[3])};",
                "",
            ]
        )

    def san(name):
        return name.upper().replace("EVENT_", "").replace(".", "P").replace("-", "M")

    const_lines = [
        "    localparam ENABLE_C24_GLOBAL_READOUT = 1;",
        "",
        f"    localparam signed [63:0] C24_MEM_INIT_NSR = {sv64(init_mem[0])};",
        f"    localparam signed [63:0] C24_MEM_INIT_CHF = {sv64(init_mem[1])};",
        f"    localparam signed [63:0] C24_MEM_INIT_ARR = {sv64(init_mem[2])};",
        f"    localparam signed [63:0] C24_MEM_INIT_AFF = {sv64(init_mem[3])};",
        "",
    ]
    for name, vec in event.items():
        const_lines.append(const4(name, vec))
    for name in binary_names:
        const_lines.append(const4(san(name), fw[name]))
    localparams = "\n".join(const_lines)

    rdm_funcs = []
    for ci, cls in enumerate(["nsr", "chf", "arr", "aff"]):
        lines = [f"    function signed [63:0] c24_rdm_level_{cls};", "        input integer idx;", "        begin", "            case (idx)"]
        for i in range(15):
            lines.append(f"                {i}: c24_rdm_level_{cls} = {sv64(rdm_level[i, ci])};")
        lines += [f"                default: c24_rdm_level_{cls} = 64'sd0;", "            endcase", "        end", "    endfunction", ""]
        rdm_funcs.append("\n".join(lines))

    helpers = f"""    function [63:0] c24_u32_x100;
        input [31:0] value;
        begin
            c24_u32_x100 = ({{32'd0, value}} << 6) + ({{32'd0, value}} << 5) + ({{32'd0, value}} << 2);
        end
    endfunction

    function [63:0] c24_u32_mul_th;
        input [31:0] value;
        input [31:0] th;
        begin
            case (th)
                32'd1:  c24_u32_mul_th = {{32'd0, value}};
                32'd2:  c24_u32_mul_th = {{32'd0, value}} << 1;
                32'd3:  c24_u32_mul_th = ({{32'd0, value}} << 1) + {{32'd0, value}};
                32'd4:  c24_u32_mul_th = {{32'd0, value}} << 2;
                32'd5:  c24_u32_mul_th = ({{32'd0, value}} << 2) + {{32'd0, value}};
                32'd6:  c24_u32_mul_th = ({{32'd0, value}} << 2) + ({{32'd0, value}} << 1);
                32'd7:  c24_u32_mul_th = ({{32'd0, value}} << 2) + ({{32'd0, value}} << 1) + {{32'd0, value}};
                32'd8:  c24_u32_mul_th = {{32'd0, value}} << 3;
                32'd9:  c24_u32_mul_th = ({{32'd0, value}} << 3) + {{32'd0, value}};
                32'd10: c24_u32_mul_th = ({{32'd0, value}} << 3) + ({{32'd0, value}} << 1);
                32'd12: c24_u32_mul_th = ({{32'd0, value}} << 3) + ({{32'd0, value}} << 2);
                32'd14: c24_u32_mul_th = ({{32'd0, value}} << 3) + ({{32'd0, value}} << 2) + ({{32'd0, value}} << 1);
                32'd15: c24_u32_mul_th = ({{32'd0, value}} << 3) + ({{32'd0, value}} << 2) + ({{32'd0, value}} << 1) + {{32'd0, value}};
                32'd20: c24_u32_mul_th = ({{32'd0, value}} << 4) + ({{32'd0, value}} << 2);
                32'd25: c24_u32_mul_th = ({{32'd0, value}} << 4) + ({{32'd0, value}} << 3) + {{32'd0, value}};
                32'd30: c24_u32_mul_th = ({{32'd0, value}} << 4) + ({{32'd0, value}} << 3) + ({{32'd0, value}} << 2) + ({{32'd0, value}} << 1);
                32'd35: c24_u32_mul_th = ({{32'd0, value}} << 5) + ({{32'd0, value}} << 1) + {{32'd0, value}};
                32'd40: c24_u32_mul_th = ({{32'd0, value}} << 5) + ({{32'd0, value}} << 3);
                32'd45: c24_u32_mul_th = ({{32'd0, value}} << 5) + ({{32'd0, value}} << 3) + ({{32'd0, value}} << 2) + {{32'd0, value}};
                default: c24_u32_mul_th = 64'd0;
            endcase
        end
    endfunction

    function c24_ge_pct;
        input [31:0] num;
        input [31:0] den;
        input [31:0] th;
        begin
            c24_ge_pct = (den != 32'd0) && (c24_u32_x100(num) >= c24_u32_mul_th(den, th));
        end
    endfunction

    function c24_le_pct;
        input [31:0] num;
        input [31:0] den;
        input [31:0] th;
        begin
            c24_le_pct = (den == 32'd0) || (c24_u32_x100(num) <= c24_u32_mul_th(den, th));
        end
    endfunction

    function c24_ge_avg;
        input [31:0] sum;
        input [31:0] den;
        input [31:0] th;
        begin
            c24_ge_avg = (den != 32'd0) && ({{32'd0, sum}} >= c24_u32_mul_th(den, th));
        end
    endfunction

    function c24_le_avg;
        input [31:0] sum;
        input [31:0] den;
        input [31:0] th;
        begin
            c24_le_avg = (den == 32'd0) || ({{32'd0, sum}} <= c24_u32_mul_th(den, th));
        end
    endfunction

    function signed [SCORE_WIDTH-1:0] score_mul_u6;
        input signed [SCORE_WIDTH-1:0] weight;
        input [5:0] value;
        reg signed [SCORE_WIDTH-1:0] acc;
        begin
            acc = {{SCORE_WIDTH{{1'b0}}}};
            if (value[0]) acc = acc + weight;
            if (value[1]) acc = acc + (weight <<< 1);
            if (value[2]) acc = acc + (weight <<< 2);
            if (value[3]) acc = acc + (weight <<< 3);
            if (value[4]) acc = acc + (weight <<< 4);
            if (value[5]) acc = acc + (weight <<< 5);
            score_mul_u6 = acc;
        end
    endfunction

    function signed [63:0] c24_mul_u6;
        input signed [63:0] weight;
        input [5:0] value;
        reg signed [63:0] acc;
        begin
            acc = 64'sd0;
            if (value[0]) acc = acc + weight;
            if (value[1]) acc = acc + (weight <<< 1);
            if (value[2]) acc = acc + (weight <<< 2);
            if (value[3]) acc = acc + (weight <<< 3);
            if (value[4]) acc = acc + (weight <<< 4);
            if (value[5]) acc = acc + (weight <<< 5);
            c24_mul_u6 = acc;
        end
    endfunction

{''.join(rdm_funcs)}    task c24_add4;
        input signed [63:0] w_nsr;
        input signed [63:0] w_chf;
        input signed [63:0] w_arr;
        input signed [63:0] w_aff;
        begin
            c24_mem_nsr_next = c24_mem_nsr_next + w_nsr;
            c24_mem_chf_next = c24_mem_chf_next + w_chf;
            c24_mem_arr_next = c24_mem_arr_next + w_arr;
            c24_mem_aff_next = c24_mem_aff_next + w_aff;
        end
    endtask

"""

    def add4(prefix):
        return f"c24_add4(C24_W_{prefix}_NSR, C24_W_{prefix}_CHF, C24_W_{prefix}_ARR, C24_W_{prefix}_AFF);"

    def add4_expr(nsr, chf, arr, aff):
        return f"c24_add4({nsr}, {chf}, {arr}, {aff});"

    def vpct_ge(n, d, th):
        return f"c24_ge_pct({n}, {d}, 32'd{int(th)})"

    def vpct_le(n, d, th):
        return f"c24_le_pct({n}, {d}, 32'd{int(th)})"

    def vavg_ge(s, d, th):
        return f"c24_ge_avg({s}, {d}, 32'd{int(th)})"

    def vavg_le(s, d, th):
        return f"c24_le_avg({s}, {d}, 32'd{int(th)})"

    pden = "{15'd0, pnn_decision_seg_count}"
    pmis = "{16'd0, pnn_mis_seg_count_next}"
    rden = "{16'd0, rdm_valid_seg_count_next}"
    rsum = "{12'd0, rdm_code_seg_sum_next}"
    bden = "{16'd0, beat_seg_count_next}"
    dden = "{16'd0, dscr_slope_seg_count_next}"
    dflip = "{16'd0, dscr_flip_seg_count_next}"
    ramden = "{16'd0, ram_seg_count_next}"
    ramsum = "{10'd0, ram_code_seg_sum_next}"
    qden = "{16'd0, qrs_maf_valid_seg_count_next}"
    rbden = "{16'd0, rbbb_valid_seg_count_next}"
    conds = {}
    for th in profile["pnn_ge"]:
        conds[f"pnn_mis_ge_{th:g}"] = vpct_ge(pmis, pden, th)
    for th in profile["pnn_le"]:
        conds[f"pnn_mis_le_{th:g}"] = vpct_le(pmis, pden, th)
    for th in profile["rdm_ge"]:
        conds[f"rdm_avg_ge_{th:g}"] = vavg_ge(rsum, rden, th)
    for th in profile["rdm_le"]:
        conds[f"rdm_avg_le_{th:g}"] = vavg_le(rsum, rden, th)
    for key, num in [
        ("rdm_ge20", "{16'd0, rdm_ge20_seg_count_next}"),
        ("rdm_ge50", "{16'd0, rdm_ge50_seg_count_next}"),
        ("rdm_ge80", "{16'd0, rdm_ge80_seg_count_next}"),
        ("rdm_ge100", "{16'd0, rdm_ge100_seg_count_next}"),
    ]:
        for th in profile["rate_ge"]:
            conds[f"{key}_ge_{th:g}"] = vpct_ge(num, rden, th)
    for th in profile["dscr_ge"]:
        conds[f"dscr_ge_{th:g}"] = vpct_ge(dflip, dden, th)
    for th in profile["dscr_le"]:
        conds[f"dscr_le_{th:g}"] = vpct_le(dflip, dden, th)
    for th in profile["ram_ge"]:
        conds[f"ram_ge_{th:g}"] = vavg_ge(ramsum, ramden, th)
    for th in profile["ram_le"]:
        conds[f"ram_le_{th:g}"] = vavg_le(ramsum, ramden, th)
    for th in profile["ecp_ge"]:
        conds[f"ecp_ge_{th:g}"] = vpct_ge("{16'd0, ectopic_pair_seg_count_next}", bden, th)
    for th in profile["pre_ge"]:
        conds[f"pre_ge_{th:g}"] = vpct_ge("{16'd0, pre_qrs_bump_seg_count_next}", bden, th)
    for th in profile["qrs_ge"]:
        conds[f"qrs_ge_{th:g}"] = vpct_ge("{16'd0, qrs_maf_seg_count_next}", qden, th)
    for th in profile["qrs_width_ge"]:
        conds[f"qrs_width_ge_{th:g}"] = vpct_ge("{16'd0, qrs_width_abn_seg_count_next}", qden, th)
    for th in profile["qrs_energy_ge"]:
        conds[f"qrs_energy_ge_{th:g}"] = vpct_ge("{16'd0, qrs_energy_abn_seg_count_next}", qden, th)
    for th in profile["rbbb_ge"]:
        conds[f"rbbb_ge_{th:g}"] = vpct_ge("{16'd0, rbbb_like_seg_count_next}", bden, th)
        conds[f"rbbb_wide_ge_{th:g}"] = vpct_ge("{16'd0, rbbb_wide_seg_count_next}", rbden, th)
        conds[f"rbbb_terminal_ge_{th:g}"] = vpct_ge("{16'd0, rbbb_terminal_seg_count_next}", rbden, th)
    rbbb_like_expr = "{16'd0, rbbb_like_seg_count_next}"
    qrs_width_expr = "{16'd0, qrs_width_abn_seg_count_next}"
    qrs_energy_expr = "{16'd0, qrs_energy_abn_seg_count_next}"
    ect_pair_expr = "{16'd0, ectopic_pair_seg_count_next}"
    conds.update(
        {
            "gate_regular_rbbb_rescue": f"{vpct_le(pmis, pden, 15)} && {vpct_ge(rbbb_like_expr, bden, 2)}",
            "gate_regular_qrs_arr_rescue": f"{vpct_le(pmis, pden, 15)} && ({vpct_ge(qrs_width_expr, qden, 2)} || {vpct_ge(qrs_energy_expr, qden, 35)})",
            "gate_episodic_ectopic_arr": f"{vpct_ge(ect_pair_expr, bden, 3)} && {vpct_le(pmis, pden, 35)} && {vavg_le(rsum, rden, 8)}",
            "gate_eerg_like": f"(rbbb_like_seg_count_next == 16'd0) && (pre_qrs_bump_seg_count_next >= 16'd1) && ((ectopic_early_seg_count_next >= 16'd10) || (ectopic_pair_seg_count_next >= 16'd3)) && {vpct_le(pmis, pden, 15)} && {vavg_le(rsum, rden, 5)}",
            "gate_aff_persistent_irreg": f"{vpct_ge(pmis, pden, 25)} && {vavg_ge(rsum, rden, 7)} && {vpct_ge(ect_pair_expr, bden, 5)}",
            "gate_arr_mid_irreg": f"{vpct_ge(pmis, pden, 5)} && {vpct_le(pmis, pden, 30)} && {vavg_ge(rsum, rden, 2)} && {vavg_le(rsum, rden, 9)}",
            "gate_chf_low_dscr_low_irreg": f"{vpct_le(dflip, dden, 3)} && {vpct_le(pmis, pden, 20)}",
            "gate_nsr_high_dscr_low_irreg": f"{vpct_ge(dflip, dden, 5)} && {vpct_le(pmis, pden, 15)} && {vavg_le(rsum, rden, 5)}",
            "gate_ram_high_regular": f"{vavg_ge(ramsum, ramden, 10)} && {vpct_le(pmis, pden, 20)}",
            "gate_ram_low_irregular": f"{vavg_le(ramsum, ramden, 5)} && {vpct_ge(pmis, pden, 15)}",
        }
    )

    terminal = ["        if ((ENABLE_C24_GLOBAL_READOUT != 0) && segment_done) begin"]
    for name in binary_names:
        terminal.append(f"            if ({conds[name]})")
        terminal.append(f"                {add4(san(name))} // {name}")
    terminal.append("        end")
    terminal = "\n".join(terminal)

    wta = f"""        {terminal}

        if ((ENABLE_C24_GLOBAL_READOUT != 0) && segment_done) begin
            c24_best_score = c24_mem_nsr_next;
            c24_best_class = CLASS_NSR;
            if (c24_mem_chf_next > c24_best_score) begin c24_best_score = c24_mem_chf_next; c24_best_class = CLASS_CHF; end
            if (c24_mem_arr_next > c24_best_score) begin c24_best_score = c24_mem_arr_next; c24_best_class = CLASS_ARR; end
            if (c24_mem_aff_next > c24_best_score) begin c24_best_score = c24_mem_aff_next; c24_best_class = CLASS_AFF; end
            best_score = c24_best_score[SCORE_WIDTH-1:0];
            best_class = c24_best_class;
        end else begin
            best_score = score_nsr_next;
            best_class = CLASS_NSR;
            if (score_chf_next > best_score) begin best_score = score_chf_next; best_class = CLASS_CHF; end
            if (score_arr_next > best_score) begin best_score = score_arr_next; best_class = CLASS_ARR; end
            if (score_aff_next > best_score) begin best_score = score_aff_next; best_class = CLASS_AFF; end
        end
"""
    reg_block = """    reg signed [63:0] c24_mem_nsr;

    reg signed [63:0] c24_mem_chf;

    reg signed [63:0] c24_mem_arr;

    reg signed [63:0] c24_mem_aff;

    reg signed [63:0] c24_mem_nsr_next;

    reg signed [63:0] c24_mem_chf_next;

    reg signed [63:0] c24_mem_arr_next;

    reg signed [63:0] c24_mem_aff_next;

    reg signed [63:0] c24_best_score;

    reg [1:0] c24_best_class;

"""

    def patch(path):
        text = path.read_text(encoding="utf-8")
        if "C24_MEM_INIT_NSR" in text:
            raise RuntimeError(f"already patched: {path}")
        text = re.sub(r"    localparam ENABLE_C24_GLOBAL_READOUT = 1;\n\n    localparam signed \[63:0\] C24_BIAS_NSR = .*?C24_BIAS_AFF = .*?;\n\n", localparams + "\n", text, flags=re.S)
        text = re.sub(r"    reg signed \[63:0\] c24_score_nsr_acc;\n\n    reg signed \[63:0\] c24_score_chf_acc;\n\n    reg signed \[63:0\] c24_score_arr_acc;\n\n    reg signed \[63:0\] c24_score_aff_acc;\n\n    reg signed \[63:0\] c24_best_score;\n\n    reg \[1:0\] c24_best_class;\n\n", reg_block, text)
        text = re.sub(r"    function c24_ge_pct;\n.*?    function \[4:0\] scale_q4_from_ticks;", helpers + "    function [4:0] scale_q4_from_ticks;", text, flags=re.S)
        text = text.replace(
            "        c24_score_nsr_acc = C24_BIAS_NSR;\n\n        c24_score_chf_acc = C24_BIAS_CHF;\n\n        c24_score_arr_acc = C24_BIAS_ARR;\n\n        c24_score_aff_acc = C24_BIAS_AFF;\n\n        c24_best_score = 64'sd0;\n\n        c24_best_class = CLASS_NSR;\n\n",
            "        c24_mem_nsr_next = c24_mem_nsr;\n\n        c24_mem_chf_next = c24_mem_chf;\n\n        c24_mem_arr_next = c24_mem_arr;\n\n        c24_mem_aff_next = c24_mem_aff;\n\n        c24_best_score = 64'sd0;\n\n        c24_best_class = CLASS_NSR;\n\n",
        )
        replacements = [
            ("        if (pnn_match_spike) begin\n\n            local_nsr_next = local_nsr_next + W_PNN_MATCH_NSR;", f"        if (pnn_match_spike) begin\n\n            {add4('PNN_MATCH')}\n\n            local_nsr_next = local_nsr_next + W_PNN_MATCH_NSR;"),
            ("        if (pnn_mismatch_spike) begin\n\n            local_nsr_next = local_nsr_next + W_PNN_MIS_NSR;", f"        if (pnn_mismatch_spike) begin\n\n            {add4('PNN_MIS')}\n\n            local_nsr_next = local_nsr_next + W_PNN_MIS_NSR;"),
            ("        if (dscr_valid_slope_spike) begin\n\n            local_nsr_next = local_nsr_next + W_DSCR_SLOPE_NSR;", f"        if (dscr_valid_slope_spike) begin\n\n            {add4('DSCR_SLOPE')}\n\n            local_nsr_next = local_nsr_next + W_DSCR_SLOPE_NSR;"),
            ("        if (dscr_sign_flip_spike) begin\n\n            local_nsr_next = local_nsr_next + W_DSCR_FLIP_NSR;", f"        if (dscr_sign_flip_spike) begin\n\n            {add4('DSCR_FLIP')}\n\n            local_nsr_next = local_nsr_next + W_DSCR_FLIP_NSR;"),
            ("        if (ram_amp_spike) begin\n\n            local_arr_next = local_arr_next + W_RAM_COUNT_ARR + (W_RAM_SUM_ARR * $signed({26'd0, ram_amp_code}));", "        if (ram_amp_spike) begin\n\n            " + add4_expr("C24_W_RAM_COUNT_NSR + c24_mul_u6(C24_W_RAM_CODE_NSR, ram_amp_code)", "C24_W_RAM_COUNT_CHF + c24_mul_u6(C24_W_RAM_CODE_CHF, ram_amp_code)", "C24_W_RAM_COUNT_ARR + c24_mul_u6(C24_W_RAM_CODE_ARR, ram_amp_code)", "C24_W_RAM_COUNT_AFF + c24_mul_u6(C24_W_RAM_CODE_AFF, ram_amp_code)") + "\n\n            local_arr_next = local_arr_next + W_RAM_COUNT_ARR + score_mul_u6(W_RAM_SUM_ARR, ram_amp_code);"),
            ("                    local_aff_next = local_aff_next + w_rdm_ge_aff(i);\n\n                end", "                    local_aff_next = local_aff_next + w_rdm_ge_aff(i);\n\n                    c24_add4(c24_rdm_level_nsr(i), c24_rdm_level_chf(i), c24_rdm_level_arr(i), c24_rdm_level_aff(i));\n\n                end"),
            ("            local_nsr_next = local_nsr_next + W_RDM_VALID_NSR + (W_RDM_CODE_NSR * $signed({27'd0, rdm_code_calc}));", "            " + add4_expr("C24_W_RDM_VALID_NSR + c24_mul_u6(C24_W_RDM_CODE_NSR, {1'b0, rdm_code_calc})", "C24_W_RDM_VALID_CHF + c24_mul_u6(C24_W_RDM_CODE_CHF, {1'b0, rdm_code_calc})", "C24_W_RDM_VALID_ARR + c24_mul_u6(C24_W_RDM_CODE_ARR, {1'b0, rdm_code_calc})", "C24_W_RDM_VALID_AFF + c24_mul_u6(C24_W_RDM_CODE_AFF, {1'b0, rdm_code_calc})") + "\n\n            local_nsr_next = local_nsr_next + W_RDM_VALID_NSR + score_mul_u6(W_RDM_CODE_NSR, {1'b0, rdm_code_calc});"),
            ("        if (ectopic_pair_spike) begin\n\n            local_nsr_next = local_nsr_next + W_ECT_PAIR_NSR;", f"        if (ectopic_pair_spike) begin\n\n            {add4('ECT_PAIR')}\n\n            local_nsr_next = local_nsr_next + W_ECT_PAIR_NSR;"),
            ("        if (qrs_width_abn_spike) begin\n\n            local_nsr_next = local_nsr_next + W_QRS_WIDTH_COUNT_NSR;", f"        if (qrs_width_abn_spike || qrs_complex_abn_spike || qrs_energy_abn_spike) begin\n\n            {add4('QRS_MAF')}\n\n        end\n\n        if (qrs_width_abn_spike) begin\n\n            {add4('QRS_WIDTH')}\n\n            local_nsr_next = local_nsr_next + W_QRS_WIDTH_COUNT_NSR;"),
            ("        if (qrs_complex_abn_spike) begin\n\n            local_nsr_next = local_nsr_next + W_QRS_COMPLEX_COUNT_NSR;", f"        if (qrs_complex_abn_spike) begin\n\n            {add4('QRS_COMPLEX')}\n\n            local_nsr_next = local_nsr_next + W_QRS_COMPLEX_COUNT_NSR;"),
            ("        if (qrs_energy_abn_spike) begin\n\n            local_nsr_next = local_nsr_next + W_QRS_ENERGY_COUNT_NSR;", f"        if (qrs_energy_abn_spike) begin\n\n            {add4('QRS_ENERGY')}\n\n            local_nsr_next = local_nsr_next + W_QRS_ENERGY_COUNT_NSR;"),
            ("        if (etmc_spike) begin\n\n            local_nsr_next = local_nsr_next + W_ETMC_NSR;", f"        if (etmc_spike) begin\n\n            {add4('ETMC')}\n\n            local_nsr_next = local_nsr_next + W_ETMC_NSR;"),
            ("        if (rcd_segment_spike) begin\n\n            local_nsr_next = local_nsr_next + W_RCD_NSR;", f"        if (rcd_segment_spike) begin\n\n            {add4('RCD')}\n\n            local_nsr_next = local_nsr_next + W_RCD_NSR;"),
            ("        if (rcd2_segment_spike) begin\n\n            local_nsr_next = local_nsr_next + W_RCD2_NSR;", f"        if (rcd2_segment_spike) begin\n\n            {add4('RCD2')}\n\n            local_nsr_next = local_nsr_next + W_RCD2_NSR;"),
            ("        if (ipb_persistent_irreg_spike) begin\n\n            local_nsr_next = local_nsr_next + W_IPB_PERSIST_NSR;", f"        if (ipb_persistent_irreg_spike) begin\n\n            {add4('IPB_PERSIST')}\n\n            local_nsr_next = local_nsr_next + W_IPB_PERSIST_NSR;"),
            ("        if (ipb_episodic_irreg_spike) begin\n\n            local_nsr_next = local_nsr_next + W_IPB_EPISODIC_NSR;", f"        if (ipb_episodic_irreg_spike) begin\n\n            {add4('IPB_EPISODIC')}\n\n            local_nsr_next = local_nsr_next + W_IPB_EPISODIC_NSR;"),
            ("        if (ipb_burst_irreg_spike) begin\n\n            local_nsr_next = local_nsr_next + W_IPB_BURST_NSR;", f"        if (ipb_burst_irreg_spike) begin\n\n            {add4('IPB_BURST')}\n\n            local_nsr_next = local_nsr_next + W_IPB_BURST_NSR;"),
            ("        if (rhythm_tick && (ms_count == 10'd999)) begin\n\n            local_nsr_next = local_nsr_next + W_SEC_NSR;", f"        if (rhythm_tick && (ms_count == 10'd999)) begin\n\n            {add4('SECOND')}\n\n            local_nsr_next = local_nsr_next + W_SEC_NSR;"),
        ]
        for old, new in replacements:
            if old not in text:
                raise RuntimeError(f"pattern not found in {path}: {old[:90]}")
            text = text.replace(old, new, 1)
        text = text.replace(
            "local_aff_next = local_aff_next + W_RAM_COUNT_AFF + (W_RAM_SUM_AFF * $signed({26'd0, ram_amp_code}));",
            "local_aff_next = local_aff_next + W_RAM_COUNT_AFF + score_mul_u6(W_RAM_SUM_AFF, ram_amp_code);",
        )
        text = text.replace(
            "local_chf_next = local_chf_next + W_RDM_VALID_CHF + (W_RDM_CODE_CHF * $signed({27'd0, rdm_code_calc}));",
            "local_chf_next = local_chf_next + W_RDM_VALID_CHF + score_mul_u6(W_RDM_CODE_CHF, {1'b0, rdm_code_calc});",
        )
        text = text.replace(
            "local_arr_next = local_arr_next + W_RDM_VALID_ARR + (W_RDM_CODE_ARR * $signed({27'd0, rdm_code_calc}));",
            "local_arr_next = local_arr_next + W_RDM_VALID_ARR + score_mul_u6(W_RDM_CODE_ARR, {1'b0, rdm_code_calc});",
        )
        text = text.replace(
            "local_aff_next = local_aff_next + W_RDM_VALID_AFF + (W_RDM_CODE_AFF * $signed({27'd0, rdm_code_calc}));",
            "local_aff_next = local_aff_next + W_RDM_VALID_AFF + score_mul_u6(W_RDM_CODE_AFF, {1'b0, rdm_code_calc});",
        )
        text = text.replace(
            "        if (pnn_match_spike) begin",
            f"""        if (pre_qrs_bump_spike) begin

            {add4('PRE_QRS')}

        end

        if (rbbb_qrs_like_beat_spike) begin

            {add4('RBBB_LIKE')}

        end

        if (rbbb_qrs_delay_segment_spike) begin

            {add4('RBBB_SEGMENT')}

        end

        if (pnn_match_spike) begin""",
            1,
        )
        text = text.replace(
            "            if (arr_high_irregular_spike)\n\n                score_arr_next = score_arr_next + scale_score_q4(W_ARR_HIGH_IRR_TO_ARR, window_scale_q4);",
            f"            if (arr_high_irregular_spike) begin\n\n                score_arr_next = score_arr_next + scale_score_q4(W_ARR_HIGH_IRR_TO_ARR, window_scale_q4);\n\n                {add4('ARR_HIGH_IRR')}\n\n            end",
        )
        text = text.replace("                    rbbb_lateslope_applied = 1'b1;\n\n                end", f"                    rbbb_lateslope_applied = 1'b1;\n\n                    {add4('RBBB_LATE_APPLIED')}\n\n                end", 1)
        text = text.replace("                    rbbb_lateslope_applied = 1'b1;\n\n                end", f"                    rbbb_lateslope_applied = 1'b1;\n\n                    {add4('RBBB_LATE_APPLIED')}\n\n                end", 1)
        text = text.replace("                    rbbb_qrs_delay_applied = 1'b1;\n\n                end", f"                    rbbb_qrs_delay_applied = 1'b1;\n\n                    {add4('RBBB_APPLIED')}\n\n                end", 1)
        text = text.replace("                    rbbb_qrs_delay_applied = 1'b1;\n\n                end", f"                    rbbb_qrs_delay_applied = 1'b1;\n\n                    {add4('RBBB_APPLIED')}\n\n                end", 1)
        text = text.replace(
            "        if (segment_done && eerg_gate_next) begin\n\n            score_arr_next = score_arr_next + W_EERG_ARR_BOOST_S;\n\n            eerg_applied = 1'b1;\n\n        end",
            f"        if (segment_done && eerg_gate_next) begin\n\n            score_arr_next = score_arr_next + W_EERG_ARR_BOOST_S;\n\n            eerg_applied = 1'b1;\n\n            {add4('EERG_GATE')}\n\n            {add4('EERG_APPLIED')}\n\n        end",
        )
        text = re.sub(r"        if \(\(ENABLE_C24_GLOBAL_READOUT != 0\) && segment_done\) begin\n            c24_score_nsr_acc = C24_BIAS_NSR;.*?        end\n\n    end\n\n\n\n    always @\(posedge clk\) begin", wta + "\n    end\n\n\n\n    always @(posedge clk) begin", text, flags=re.S)
        text = text.replace(
            "            score_aff <= BIAS_AFF;\n\n            pred_class <= CLASS_NSR;",
            "            score_aff <= BIAS_AFF;\n\n            c24_mem_nsr <= C24_MEM_INIT_NSR;\n\n            c24_mem_chf <= C24_MEM_INIT_CHF;\n\n            c24_mem_arr <= C24_MEM_INIT_ARR;\n\n            c24_mem_aff <= C24_MEM_INIT_AFF;\n\n            pred_class <= CLASS_NSR;",
            1,
        )
        text = text.replace(
            "            score_aff <= BIAS_AFF;\n\n            pred_class <= CLASS_NSR;",
            "            score_aff <= BIAS_AFF;\n\n            c24_mem_nsr <= C24_MEM_INIT_NSR;\n\n            c24_mem_chf <= C24_MEM_INIT_CHF;\n\n            c24_mem_arr <= C24_MEM_INIT_ARR;\n\n            c24_mem_aff <= C24_MEM_INIT_AFF;\n\n            pred_class <= CLASS_NSR;",
            1,
        )
        text = text.replace(
            "            score_aff <= score_aff_next;\n\n\n\n            if (finalize_window) begin",
            "            score_aff <= score_aff_next;\n\n            c24_mem_nsr <= c24_mem_nsr_next;\n\n            c24_mem_chf <= c24_mem_chf_next;\n\n            c24_mem_arr <= c24_mem_arr_next;\n\n            c24_mem_aff <= c24_mem_aff_next;\n\n\n\n            if (finalize_window) begin",
        )
        if "c24_add_feature" in text or "c24_score_nsr_acc" in text or "c24_weight_{cls_name}" in text:
            raise RuntimeError(f"vector C24 leftover in {path}")
        path.write_text(text, encoding="utf-8", newline="")

    for rel in ["SNN_ECG.srcs/sources_1/new/class_score_neurons.v", "rtl/core/class_score_neurons.v"]:
        patch(ws / rel)

    print(json.dumps({"metrics": repro["metrics"], "init_mem": [int(x) for x in init_mem], "binary_feature_count": len(binary_names), "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
