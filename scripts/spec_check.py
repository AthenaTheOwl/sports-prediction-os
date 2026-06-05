#!/usr/bin/env python3
"""Verify every requirement ID in specs/ is referenced in source or tests.

Walks specs/*/requirements.md, extracts every `R-<PREFIX>-NNN` token, then
greps the repo (excluding specs/ + .git/ + build artifacts) for each one.
A missing reference fails the gate.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs"
ID_RE = re.compile(r"\bR-[A-Z]{2,8}-\d{3}\b")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "specs", "data"}
SEARCH_GLOBS = ("**/*.py", "**/*.md", "**/*.yaml", "**/*.yml", "**/*.toml")


def extract_ids() -> set[str]:
    ids: set[str] = set()
    if not SPECS.exists():
        return ids
    for p in SPECS.rglob("requirements.md"):
        ids.update(ID_RE.findall(p.read_text(encoding="utf-8")))
    return ids


def reference_text() -> str:
    parts: list[str] = []
    for pattern in SEARCH_GLOBS:
        for p in ROOT.glob(pattern):
            if any(d in p.parts for d in SKIP_DIRS):
                continue
            try:
                parts.append(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
    return "\n".join(parts)


def main() -> int:
    ids = extract_ids()
    if not ids:
        print("spec_check: no requirement IDs found in specs/")
        return 0
    haystack = reference_text()
    missing = sorted(rid for rid in ids if rid not in haystack)
    if missing:
        print(
            f"spec_check: {len(missing)} requirement ID(s) NOT referenced outside specs/:",
            file=sys.stderr,
        )
        for rid in missing:
            print(f"  - {rid}", file=sys.stderr)
        return 1
    print(f"spec_check: all {len(ids)} requirement ID(s) referenced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
