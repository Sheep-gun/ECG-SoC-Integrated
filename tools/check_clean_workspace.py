#!/usr/bin/env python3
"""Check that the curated workspace contains only canonical project structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOP = {
    "analysis", "datasets", "design", "docs", "figures", "models",
    "project_registry", "reports", "tables", "tools", "verification", "vivado",
}
ALLOWED_XPR = {
    "vivado/microblaze/SNN_ECG_MB_FULL_REPLAY.xpr",
    "vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr",
}
FORBIDDEN_DIR_NAMES = {
    ".Xil", "__pycache__", ".pytest_cache", ".mypy_cache", "ip_user_files",
}
FORBIDDEN_PATH_PARTS = {"private_submission", "submission_private"}
HOME_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\\/\s]+[\\/]", re.I),
    re.compile(r"/home/[^/\s]+/"),
)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".py", ".tcl",
    ".v", ".sv", ".vh", ".xdc", ".xml", ".prj", ".f", ".sh", ".ps1", ".m",
    ".log", ".rpt", ".do", ".jou", ".str",
}


def public_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        rel = path.relative_to(ROOT)
        if ".git" in rel.parts or "tmp" in rel.parts:
            continue
        files.append(path)
    return files


def main() -> int:
    errors: list[str] = []
    for name in sorted(REQUIRED_TOP):
        if not (ROOT / name).is_dir():
            errors.append(f"missing top-level directory: {name}")

    xprs = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.xpr")}
    if xprs != ALLOWED_XPR:
        errors.append(f"Vivado projects must be exactly {sorted(ALLOWED_XPR)}; found {sorted(xprs)}")

    nested_git = [p for p in ROOT.rglob(".git") if p != ROOT / ".git"]
    if nested_git:
        errors.extend(f"nested repository boundary: {p.relative_to(ROOT)}" for p in nested_git)

    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if p.is_dir() and p.name in FORBIDDEN_DIR_NAMES:
            errors.append(f"generated/cache directory retained: {rel}")
        if any(part in FORBIDDEN_PATH_PARTS for part in rel.parts):
            errors.append(f"private submission path retained: {rel}")

    checker_sources = {
        Path(__file__).resolve(),
        (ROOT / "tools" / "redact_local_paths.py").resolve(),
    }
    for p in public_text_files():
        if p.resolve() in checker_sources:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"tracked text is not UTF-8: {p.relative_to(ROOT)}")
            continue
        for pattern in HOME_PATTERNS:
            if pattern.search(text):
                errors.append(f"personal absolute path in public text: {p.relative_to(ROOT)}")
                break

    if errors:
        print("CLEAN_WORKSPACE: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CLEAN_WORKSPACE: PASS")
    print("- canonical top-level layout present")
    print("- exactly two Vivado projects present")
    print("- no nested Git boundary, private submission path, or personal absolute path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
