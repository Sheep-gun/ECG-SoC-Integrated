#!/usr/bin/env python3
"""Replace personal absolute paths in retained public text artifacts."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {
    ".md", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".py", ".tcl",
    ".v", ".sv", ".vh", ".xdc", ".xml", ".prj", ".f", ".sh", ".ps1", ".m",
    ".log", ".rpt", ".do", ".jou", ".str",
}

REPLACEMENTS = (
    (re.compile(r"C:[/\\]Users[/\\]YangGeon[/\\]SNN ECG Classifier[/\\]ECG-SoC-Integrated", re.I), "<REPOSITORY_ROOT>"),
    (re.compile(r"C:[/\\]Users[/\\]YangGeon[/\\]SNN ECG Classifier", re.I), "<WORKSPACE_ROOT>"),
    (re.compile(r"/home/soohwan/ECG-SoC"), "<XMODEL_REPOSITORY_ROOT>"),
    (re.compile(r"/home/soohwan/xmodel_2025\.12_x86_64"), "<XMODEL_INSTALL_ROOT>"),
    (re.compile(r"[A-Za-z]:[/\\]Users[/\\][^/\\\s]+", re.I), "<LOCAL_HOME>"),
    (re.compile(r"/home/[^/\s]+"), "<LOCAL_HOME>"),
)


def main() -> int:
    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        rel = path.relative_to(ROOT)
        if (
            ".git" in rel.parts
            or "tmp" in rel.parts
            or rel.as_posix() in {"tools/redact_local_paths.py", "tools/check_clean_workspace.py"}
        ):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        redacted = original
        for pattern, replacement in REPLACEMENTS:
            redacted = pattern.sub(replacement, redacted)
        if redacted != original:
            path.write_text(redacted, encoding="utf-8", newline="")
            changed += 1
            print(rel.as_posix())
    print(f"redacted_files={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
