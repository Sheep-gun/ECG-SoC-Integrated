#!/usr/bin/env python3
"""Fail-closed integrity and claim-boundary checks for the integrated repository."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
GIT = os.environ.get(
    "GIT_EXECUTABLE",
    shutil.which("git")
    or r"C:\Users\YangGeon\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe",
)

SPECS = {
    "matlab_prevalidation": {
        "origin": "https://github.com/ferocious-kiwi/ECG-SoC-MATLAB-AFE-ADC-Prevalidation",
        "commit": "907f7e1f081a9d6a5703a32095d962143315a192",
        "owner": "서민우",
    },
    "afe_xmodel": {
        "origin": "https://github.com/Hwan-22/ECG-SoC",
        "commit": "4756a5086023547328ef44fd5fd87da3c250dc39",
        "owner": "이수환",
    },
    "digital_accelerator": {
        "origin": "https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier",
        "commit": "c6b80de19cdcad5b7e43fe7835588b629d847f75",
        "owner": "양건",
    },
}

REQUIRED = [
    "README.md", "LICENSE_OR_PROVENANCE.md", "INTEGRATION_AUDIT.md", ".gitignore",
    "source_of_truth/upstream_commits.yaml", "source_of_truth/global_metrics.yaml",
    "source_of_truth/claim_registry.csv", "source_of_truth/artifact_manifest.csv",
    "source_of_truth/ownership_matrix.csv", "source_of_truth/terminology.yaml",
    "source_of_truth/external_reference_registry.csv",
    "docs/RESEARCH_BACKGROUND_KR.md", "docs/PROBLEM_DEFINITION_KR.md",
    "docs/RESEARCH_OBJECTIVES_KR.md", "docs/CONTRIBUTIONS_AND_NOVELTY_KR.md",
    "docs/SYSTEM_OVERVIEW_KR.md", "docs/OWNERSHIP_AND_HANDOFF_KR.md",
    "docs/DATASET_AND_EVALUATION_KR.md", "docs/DATASET_DOMAIN_CONFOUNDING_KR.md",
    "docs/MIXED_SIGNAL_VERIFICATION_KR.md", "docs/DIGITAL_ARCHITECTURE_KR.md",
    "docs/HARDWARE_IMPLEMENTATION_KR.md", "docs/INTEGRATION_VERIFICATION_KR.md",
    "docs/LIMITATIONS_AND_CLAIM_BOUNDARY_KR.md", "docs/REPORT_EVIDENCE_MAP_KR.md",
    "docs/INTEGRATION_METHOD.md", "benchmarks/accelerator_benefit/README.md",
    "figures/FIGURE_INDEX.md", "figures/source/figure_data.json",
    "tools/import_upstream_repositories.py", "tools/build_global_metrics.py",
    "tools/check_integrated_repository.py", "tools/generate_integrated_figures.py",
    "tools/check_integrated_technical_report.py", "tools/fetch_physionet_datasets.py",
    "tools/verify_physionet_datasets.py", "datasets/README.md",
    "datasets/dataset_manifest.yaml", "datasets/DATASET_LICENSES.md",
    "datasets/SHA256SUMS_EXPECTED.txt", "docs/STREAMING_STATE_MEMORY_KR.md",
    "tables/streaming_state_inventory.csv",
    "figures/final/FIG-12_detailed_digital_architecture.svg",
    "integration_evidence/excluded_upstream_paths.csv",
    "integration_evidence/excluded_large_dataset_paths.csv",
    "reports/INTEGRATED_TECHNICAL_REPORT_KR.md",
    "reports/PUBLICATION_READINESS_PREFLIGHT.md", "reports/HISTORY_REWRITE_PLAN.md",
    "reports/HISTORY_REWRITE_RESULT.md", "reports/PUBLISH_REWRITTEN_HISTORY.md",
    "private_submission/.gitignore",
]


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run([GIT, "-C", str(repo), *args], text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {result.stderr.strip()}")
    return result.stdout.strip()


def normalize_origin(value: str) -> str:
    value = value.strip().replace("\\", "/")
    if value.endswith(".git"):
        value = value[:-4]
    return value.rstrip("/").lower()


def read_csv(rel: str):
    with (ROOT / rel).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def hash_path(path: Path) -> str:
    extended = "\\\\?\\" + str(path.resolve()) if os.name == "nt" else str(path)
    digest = hashlib.sha256()
    with open(extended, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture_state(component: str, repo: Path) -> dict:
    porcelain = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    tracked = git(repo, "status", "--porcelain=v1", "--untracked-files=no")
    return {
        "component": component,
        "repository_root": str(repo),
        "origin": git(repo, "remote", "get-url", "origin"),
        "active_branch": git(repo, "branch", "--show-current"),
        "active_head": git(repo, "rev-parse", "HEAD"),
        "fixed_imported_commit": SPECS[component]["commit"],
        "status_porcelain": porcelain.splitlines() if porcelain else [],
        "tracked_status": tracked.splitlines() if tracked else [],
        "untracked_paths": [line[3:] for line in porcelain.splitlines() if line.startswith("?? ")],
    }


def authored_text() -> str:
    paths = [ROOT / "README.md", ROOT / "LICENSE_OR_PROVENANCE.md", ROOT / "INTEGRATION_AUDIT.md", ROOT / "benchmarks" / "accelerator_benefit" / "README.md", ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_KR.md"]
    paths += sorted((ROOT / "docs").glob("*.md"))
    paths += sorted((ROOT / "datasets").glob("*.md"))
    paths += [ROOT / "figures" / "FIGURE_INDEX.md"]
    paths += sorted((ROOT / "tables").glob("*.csv"))
    return "\n".join(p.read_text(encoding="utf-8-sig", errors="replace") for p in paths if p.exists())


def main() -> int:
    checked: list[str] = []
    failures: list[str] = []
    unresolved: list[str] = []

    def check(name: str, condition: bool, detail: str = ""):
        checked.append(name)
        if not condition:
            failures.append(f"{name}: {detail or 'condition failed'}")

    check("independent .git exists", (ROOT / ".git").is_dir())
    active_branch = git(ROOT, "branch", "--show-current")
    check("integrated branch is approved", active_branch in {"main", "codex/award-level-integrated-report", "codex/deep-reader-centered-report"}, active_branch)
    for rel in REQUIRED:
        check(f"required path {rel}", (ROOT / rel).exists())
    check("14 non-benchmark figures", len(list((ROOT / "figures" / "final").glob("FIG-*.svg"))) == 14)
    check("verified tables present", len(list((ROOT / "tables").glob("*.csv"))) >= 4)
    check("public remote configured", normalize_origin(git(ROOT, "remote", "get-url", "origin")) == normalize_origin("https://github.com/Sheep-gun/ECG-SoC-Integrated.git"))

    before = json.loads((ROOT / "integration_evidence" / "upstream_status_before.json").read_text(encoding="utf-8-sig"))
    before_map = {x["component"]: x for x in before["repositories"]}
    after_rows = []
    for component, spec in SPECS.items():
        b = before_map.get(component)
        check(f"before state recorded: {component}", b is not None)
        if not b:
            continue
        repo = Path(b["repository_root"])
        check(f"upstream exists: {component}", (repo / ".git").exists())
        if not (repo / ".git").exists():
            continue
        origin = git(repo, "remote", "get-url", "origin")
        check(f"origin matches: {component}", normalize_origin(origin) == normalize_origin(spec["origin"]), origin)
        cat = subprocess.run([GIT, "-C", str(repo), "cat-file", "-e", f"{spec['commit']}^{{commit}}"])
        check(f"fixed commit exists: {component}", cat.returncode == 0, spec["commit"])
        if component == "digital_accelerator":
            check("digital fixed commit exact", spec["commit"] == "c6b80de19cdcad5b7e43fe7835588b629d847f75")
        state = capture_state(component, repo)
        after_rows.append(state)
        check(f"upstream branch unchanged: {component}", state["active_branch"] == b["active_branch"], f"before={b['active_branch']} after={state['active_branch']}")
        check(f"upstream HEAD unchanged: {component}", state["active_head"] == b["active_head"], f"before={b['active_head']} after={state['active_head']}")
        tracked_unchanged = state["tracked_status"] == b["tracked_status"]
        if component == "digital_accelerator" and b.get("dirty_tracked_exception"):
            # The user explicitly authorized the separate benchmark task to keep
            # editing this subtree while fixed commit c6b80de is archived. Any
            # tracked drift outside that subtree remains a hard failure.
            def changed_path(line: str) -> str:
                parts = line.split(maxsplit=1)
                return (parts[1] if len(parts) == 2 else "").split(" -> ")[-1]
            tracked_unchanged = all(
                changed_path(line).replace("\\", "/").startswith("benchmarks/accelerator_benefit/")
                for line in state["tracked_status"]
            )
        check(f"tracked status unchanged or authorized benchmark-only drift: {component}", tracked_unchanged, f"before={b['tracked_status']} after={state['tracked_status']}")
    after_payload = {"captured_at_utc": datetime.now(timezone.utc).isoformat(), "repositories": after_rows}
    # Timestamp is intentionally removed from the committed evidence to make reruns stable.
    after_payload["captured_at_utc"] = "FINAL_INTEGRITY_CHECK"
    (ROOT / "integration_evidence" / "upstream_status_after.json").write_text(json.dumps(after_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = read_csv("source_of_truth/artifact_manifest.csv")
    check("curated artifact manifest has 913 rows", len(manifest) == 913, str(len(manifest)))
    manifest_paths = set()
    component_counts = {key: 0 for key in SPECS}
    repo_by_component = {component: Path(before_map[component]["repository_root"]) for component in SPECS}
    upstream_blob_maps = {}
    for component, spec in SPECS.items():
        tree = git(repo_by_component[component], "-c", "core.quotepath=false", "ls-tree", "-r", spec["commit"])
        mapping = {}
        for line in tree.splitlines():
            metadata, path = line.split("\t", 1)
            mapping[path] = metadata.split()[2]
        upstream_blob_maps[component] = mapping
    local_index_blobs = {}
    for line in git(ROOT, "-c", "core.quotepath=false", "ls-files", "--stage", "components").splitlines():
        metadata, path = line.split("\t", 1)
        local_index_blobs[path] = metadata.split()[1]
    for row in manifest:
        rel = row["integrated_path"]
        manifest_paths.add(rel)
        component_counts[row["component"]] += 1
        path = ROOT / rel
        extended_name = "\\\\?\\" + str(path.resolve()) if os.name == "nt" else str(path)
        if not os.path.isfile(extended_name):
            failures.append(f"manifest file missing: {rel}")
            continue
        if hash_path(path) != row["sha256"]:
            failures.append(f"manifest hash mismatch: {rel}")
        if row["upstream_commit"] != SPECS[row["component"]]["commit"]:
            failures.append(f"manifest commit mismatch: {rel}")
        upstream_blob = upstream_blob_maps[row["component"]].get(row["upstream_path"], "")
        index_blob = local_index_blobs.get(rel, "")
        if upstream_blob != index_blob:
            failures.append(f"retained integrated Git blob differs from upstream Git object: {rel}")
    checked.append("all manifest files exist and SHA256-match")
    actual_paths = set()
    for component in SPECS:
        base = ROOT / "components" / component
        extended_base = Path("\\\\?\\" + str(base.resolve())) if os.name == "nt" else base
        for path in extended_base.rglob("*"):
            if path.is_file():
                rel = path.relative_to(extended_base).as_posix()
                actual_paths.add(f"components/{component}/{rel}")
    check("component trees exactly match manifest", actual_paths == manifest_paths, f"extra={len(actual_paths-manifest_paths)} missing={len(manifest_paths-actual_paths)}")
    check("curated component counts", component_counts == {"matlab_prevalidation": 136, "afe_xmodel": 520, "digital_accelerator": 257}, str(component_counts))
    nested_git = [p for p in (ROOT / "components").rglob(".git") if p.is_dir()]
    check("no upstream .git metadata copied", not nested_git, str(nested_git[:3]))
    check("digital benchmark tmp not imported", not (ROOT / "components" / "digital_accelerator" / "tmp").exists())
    check("digital benchmark obj not imported", not (ROOT / "components" / "digital_accelerator" / "obj").exists())
    check("incomplete accelerator benchmark not imported", not (ROOT / "components" / "digital_accelerator" / "benchmarks" / "accelerator_benefit").exists())
    prohibited_imports = [p for p in (ROOT / "components").rglob("*") if p.is_file() and (p.suffix.lower() == ".hwp" or "참가신청서" in p.name or "docs\\submission" in str(p))]
    check("application/private upstream files excluded", not prohibited_imports, str(prohibited_imports))
    excluded = read_csv("integration_evidence/excluded_upstream_paths.csv")
    large_excluded = read_csv("integration_evidence/excluded_large_dataset_paths.csv")
    check("intentional exclusion registry has 981 rows", len(excluded) == 981, str(len(excluded)))
    check("raw-dataset exclusion registry has 977 rows", len(large_excluded) == 977, str(len(large_excluded)))
    excluded_by_component = {component: set() for component in SPECS}
    for row in excluded:
        excluded_by_component[row["component"]].add(row["upstream_path"])
    manifest_by_component = {component: set() for component in SPECS}
    for row in manifest:
        manifest_by_component[row["component"]].add(row["upstream_path"])
    for component, spec in SPECS.items():
        upstream_all = set(upstream_blob_maps[component])
        accounted = manifest_by_component[component] | excluded_by_component[component]
        check(f"retained+excluded cover upstream tree: {component}", accounted == upstream_all, f"missing={len(upstream_all-accounted)} extra={len(accounted-upstream_all)}")
    raw_prefixes = [f"components/afe_xmodel/algorithm/person_data/{name}/1.0.0/" for name in ("nsrdb", "chfdb", "mitdb", "afdb")]
    tracked_paths = git(ROOT, "ls-files").splitlines()
    check("raw third-party datasets are not tracked", not any(path.startswith(tuple(raw_prefixes)) for path in tracked_paths))
    reachable_objects = git(ROOT, "rev-list", "--objects", "--all")
    check("raw dataset paths absent from reachable history", not any(prefix in reachable_objects for prefix in raw_prefixes))
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check("download paths ignored", all(term in ignore for term in ["_ecg_soc_physionet/", "datasets/downloads/", "datasets/raw/"]))
    provenance = (ROOT / "LICENSE_OR_PROVENANCE.md").read_text(encoding="utf-8")
    check("curated provenance wording", "curated technical snapshot" in provenance and "not a complete" in provenance)

    text = authored_text()
    check("no personal absolute paths in final-facing files", not re.search(r"(?i)[A-Z]:[\\/]Users[\\/]", text))
    tracked_private = git(ROOT, "ls-files", "private_submission").splitlines()
    check("private submission tracks only guard", tracked_private == ["private_submission/.gitignore"], str(tracked_private))

    gm = json.loads((ROOT / "source_of_truth" / "global_metrics.yaml").read_text(encoding="utf-8"))
    metrics = gm["metrics"]
    check("final chunk metric exact", metrics["final_test_chunk_accuracy"]["value"] == 80.56)
    check("board equivalence metric exact", metrics["board_final_pred_equivalence"]["value"] == "36/36" and metrics["board_final_mem_equivalence"]["value"] == "36/36")
    check("canonical cadence exact", metrics["canonical_sample_gap_cycles"]["value"] == 2)
    for name, item in metrics.items():
        path = ROOT / item["evidence_path"]
        check(f"metric evidence exists: {name}", path.exists(), item["evidence_path"])
    benchmark = gm["benchmark"]
    expected_benchmark_fields = ["cpu_kernel_latency_ms", "cpu_end_to_end_latency_ms", "rtl_processing_latency_ms", "rtl_throughput_samples_per_s", "realtime_headroom", "estimated_power_w", "measured_board_power_w", "estimated_energy_per_decision_j", "measured_energy_per_decision_j"]
    check("benchmark status pending", benchmark.get("status") == "PENDING_EXTERNAL_BENCHMARK_IMPORT")
    check("all benchmark values null not zero", all(benchmark.get(k) is None for k in expected_benchmark_fields), str({k: benchmark.get(k) for k in expected_benchmark_fields}))
    placeholder = (ROOT / "benchmarks" / "accelerator_benefit" / "README.md").read_text(encoding="utf-8")
    check("benchmark placeholder explicit", "PENDING_EXTERNAL_BENCHMARK_IMPORT" in placeholder and "No integrated latency, throughput, speedup, power, or energy conclusion" in placeholder)

    claims = read_csv("source_of_truth/claim_registry.csv")
    required_claim_columns = {"claim_id","category","proposed_claim_kr","proposed_claim_en","status","evidence_type","owner","upstream_repository","upstream_commit","evidence_path","scope","limitations","allowed_report_sections"}
    check("claim registry columns", set(claims[0]) == required_claim_columns)
    check("claim statuses controlled", {r["status"] for r in claims}.issubset({"SAFE","CAREFUL","FORBIDDEN","PENDING_EXTERNAL_WORK","UNVERIFIED"}))
    for row in claims:
        if row["status"] not in {"FORBIDDEN", "PENDING_EXTERNAL_WORK"}:
            check(f"claim evidence exists: {row['claim_id']}", (ROOT / row["evidence_path"]).exists(), row["evidence_path"])
    claim_map = {row["claim_id"]: row for row in claims}
    check("CLM-023 registered safe", claim_map.get("CLM-023", {}).get("status") == "SAFE")
    check("CLM-023 direct RTL evidence", "direct RTL" in claim_map.get("CLM-023", {}).get("evidence_type", ""))
    state_rows = read_csv("tables/streaming_state_inventory.csv")
    required_state_columns = {"state_id", "RTL_module", "RTL_signal_or_group", "state_category", "count", "width_bits", "estimated_total_bits", "reset_scope", "update_condition", "persistent_across_samples", "persistent_across_snapshots", "evidence_path", "notes"}
    check("streaming inventory columns", bool(state_rows) and set(state_rows[0]) == required_state_columns)
    check("streaming inventory substantive", len(state_rows) >= 20, str(len(state_rows)))
    check("unresolved widths explicit", any(row["width_bits"] == "UNRESOLVED_FROM_STATIC_AUDIT" for row in state_rows))
    check("avoided window arithmetic exact", metrics["avoided_full_raw_input_window_bits"]["value"] == 21600000 and metrics["avoided_full_raw_input_window_bytes"]["value"] == 2700000)

    owners = read_csv("source_of_truth/ownership_matrix.csv")
    owner_map = {row["contributor"]: row for row in owners}
    check("three canonical contributors", set(owner_map) == {"서민우","이수환","양건"}, str(set(owner_map)))
    check("MATLAB ownership correct", "MATLAB" in owner_map["서민우"]["canonical_role"])
    check("XMODEL ownership correct", "XMODEL" in owner_map["이수환"]["canonical_role"])
    check("digital/project lead ownership correct", "Project leader" in owner_map["양건"]["canonical_role"])

    conf = (ROOT / "docs" / "DATASET_DOMAIN_CONFOUNDING_KR.md").read_text(encoding="utf-8")
    required_conf = ["nsrdb", "chfdb", "mitdb", "afdb", "direct record leakage", "database-to-class confounding", "서로 다른 문제", "공통 1 kSPS signed 12-bit", "clinical disease generalization", "same-acquisition", "RTL correctness"]
    for phrase in required_conf:
        check(f"confounding disclosure: {phrase}", phrase in conf)
    bad_board_accuracy_lines = []
    for line in text.splitlines():
        if re.search(r"(?i)(classification accuracy|분류 정확도).{0,40}36/36", line):
            if not any(marker in line for marker in ["아니다", "아님", "≠", "not ", "금지"]):
                bad_board_accuracy_lines.append(line)
    check("board equivalence not called classification accuracy", not bad_board_accuracy_lines, str(bad_board_accuracy_lines))
    check("validation 100 is labeled selection-only", "Validation 100%는 final generalization claim이 아니다" in (ROOT / "README.md").read_text(encoding="utf-8"))
    check("clinical claim boundary present", "clinically validated diagnostic device가 아니다" in (ROOT / "README.md").read_text(encoding="utf-8"))
    check("physical claim boundary present", "fabricated silicon이 아니다" in (ROOT / "README.md").read_text(encoding="utf-8"))
    check("no positive clinical-validation claim", not re.search(r"본 (?:연구|설계|시스템).{0,60}(?:임상적으로 검증|clinical(?:ly)? validated)(?!.*(?:아니다|않|not))", text, re.I))
    check("no positive physical-silicon claim", not re.search(r"(?:physical AFE|ADC silicon|fabricated SoC).{0,40}(?:검증했다|검증하였다|validated)", text, re.I))
    contradictions = [m.group(0) for m in re.finditer(r"sample_gap_cycles\s*=\s*(\d+)", text) if m.group(1) != "2"]
    check("no canonical cadence contradiction", not contradictions, str(contradictions))

    refs = read_csv("source_of_truth/external_reference_registry.csv")
    check("external references registered", len(refs) >= 6 and all(r["URL_or_identifier"] for r in refs))
    check("external references authoritative", all(r["authoritative_status"] == "AUTHORITATIVE" for r in refs))
    unsupported_product_numbers = re.search(r"(?i)(Apple|Samsung|Fitbit|Garmin).{0,80}(sensitivity|specificity|민감도|특이도).{0,20}\d", text)
    check("no unsupported commercial-product figures", unsupported_product_numbers is None, str(unsupported_product_numbers.group(0) if unsupported_product_numbers else ""))
    check("wearable wording is product-specific", "특정 제품 문서의 사례" in (ROOT / "README.md").read_text(encoding="utf-8"))
    check("unsupported broad wearable wording absent", "대표 소비자 ECG" not in text and "representative consumer ECG functions" not in text.lower())
    dataset_manifest = json.loads((ROOT / "datasets" / "dataset_manifest.yaml").read_text(encoding="utf-8"))
    check("four fixed-version datasets", len(dataset_manifest["databases"]) == 4 and all(db["version"] == "1.0.0" for db in dataset_manifest["databases"]))
    check("dataset licenses explicit", all(db["license"] == "Open Data Commons Attribution License v1.0" for db in dataset_manifest["databases"]))
    check("dataset hashes populated", sum(1 for line in (ROOT / "datasets" / "SHA256SUMS_EXPECTED.txt").read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")) >= 1000)
    fig_index = (ROOT / "figures" / "FIGURE_INDEX.md").read_text(encoding="utf-8")
    manuscript = (ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_KR.md").read_text(encoding="utf-8")
    check("FIG-12 indexed", "FIG-12_detailed_digital_architecture.svg" in fig_index)
    check("FIG-12 referenced by manuscript", "FIG-12_detailed_digital_architecture.svg" in manuscript)
    check("manuscript raw-data policy", "raw waveform을 번들하지 않는다" in manuscript)
    for forbidden in ["54.01 ms", "33.3 MSPS", "33,300", "5.35 mJ", "0.099 W"]:
        check(f"benchmark value not promoted: {forbidden}", forbidden not in text)

    parent_index = git(PARENT, "ls-files", "--stage", "--", "ECG-SoC-Integrated")
    check("integrated repo absent from parent index", not parent_index, parent_index)
    parent_exclude = (PARENT / ".git" / "info" / "exclude").read_text(encoding="utf-8", errors="replace")
    check("parent local exclude installed", "/ECG-SoC-Integrated/" in parent_exclude)
    check("parent tracked gitignore untouched by integration", not any(line.endswith(".gitignore") for line in git(PARENT, "status", "--porcelain=v1", "--untracked-files=no").splitlines()))

    if benchmark["status"] == "PENDING_EXTERNAL_BENCHMARK_IMPORT":
        unresolved.append("Accelerator-benefit benchmark remains pending external import by design.")
    unresolved.append("Physical AFE/ADC/silicon and clinical validation are outside the completed scope.")
    unresolved.append("Database-class confounding requires future same-acquisition or cross-domain validation.")

    report = [
        "# Integrated repository check",
        "",
        f"## Result: {'PASS' if not failures else 'FAIL'}",
        "",
        f"- Rules checked: {len(checked)}",
        f"- Conflicts found: {len(failures)}",
        "- Benchmark placeholder: " + ("PASS (all fields null)" if benchmark.get("status") == "PENDING_EXTERNAL_BENCHMARK_IMPORT" and all(benchmark.get(k) is None for k in expected_benchmark_fields) else "FAIL"),
        "",
        "## Rules checked",
        "",
    ] + [f"- {'PASS' if not any(f.startswith(name + ':') for f in failures) else 'FAIL'} — {name}" for name in checked]
    report += ["", "## Conflicts found", ""] + ([f"- {f}" for f in failures] if failures else ["- None."])
    report += ["", "## Unresolved evidence / bounded scope", ""] + [f"- {u}" for u in unresolved]
    report += ["", "## Benchmark-placeholder verification", "", "- Status is `PENDING_EXTERNAL_BENCHMARK_IMPORT`.", "- Latency, throughput, speedup, power and energy fields are null, not zero.", "- No benchmark figure or integrated benchmark conclusion is present.", ""]
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "integrated_repository_check.md").write_text("\n".join(report), encoding="utf-8")
    print(f"{'PASS' if not failures else 'FAIL'}: {len(checked)} rules, {len(failures)} conflicts")
    if failures:
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
