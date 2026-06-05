#!/usr/bin/env python3
"""Voice lint for public-facing copy.

This follows the editorial pattern used in the sibling fiction repos: hard
FAIL rules for phrases and structures that should not ship, plus WARN rules
for AI-cadence candidates that require close read. WARN exits non-zero by
default here because this repo is small enough that every hit should be fixed
or explicitly allowlisted.

Per-line allowlist: append `voice_lint:allow <label>` on the same line.
Multiple labels: `voice_lint:allow label1 label2`. `all` suppresses all rules.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


class Rule(NamedTuple):
    severity: str
    label: str
    pattern: re.Pattern[str]


def phrase_rule(severity: str, label: str, phrase: str) -> Rule:
    return Rule(severity, label, re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE))


BANNED_FAIL = [
    "leverage",
    "leverages",
    "leveraging",
    "demonstrates",
    "demonstrate",
    "production-grade",
    "comprehensive",
    "portfolio-grade",
    "synergy",
    "enables",
    "enabling",
    "best-in-class",
    "state-of-the-art",
    "seamlessly",
    "cutting-edge",
    "robust solution",
    "industry-leading",
    "world-class",
    "next-generation",
    "transformative",
    "game-changing",
    "revolutionary",
    "significant",
    "substantial",
    "innovative",
    "utilize",
    "delve",
    "tapestry",
    "testament to",
    "myriad",
    "in the realm of",
    "it is worth noting",
    "it is important to note",
    "it goes without saying",
    "in conclusion",
    "in summary",
    "at the end of the day",
    "shed light",
    "pivotal",
    "embark",
    "facilitate",
    "showcase",
    "crucial role",
]

BANNED_WARN = [
    "clearly",
    "obviously",
    "basically",
    "actually",
    "literally",
    "really",
    "very",
    "quite",
    "somewhat",
    "rather",
    "seemingly",
    "deeply",
    "utterly",
    "completely",
    "absolutely",
    "moreover",
    "furthermore",
    "a sense of",
    "something about",
    "in practice",
]

NEGATION = (
    r"(?:isn['\u2019]t|aren['\u2019]t|wasn['\u2019]t|weren['\u2019]t|"
    r"is\s+not|are\s+not|was\s+not|were\s+not)"
)
RIGHT_COPULA = (
    r"(?:(?:it|they|that|this|there|here)\s+(?:is|are|was|were)"
    r"|(?:it|that|this|there|here)['\u2019]s"
    r"|(?:they|we|you)['\u2019]re)"
)

STRUCTURAL = [
    Rule(
        "FAIL",
        "antithetical-period",
        re.compile(
            rf"\b{NEGATION}\b[^.!?\n]{{1,80}}[.!?]\s*{RIGHT_COPULA}\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "FAIL",
        "antithetical-dash",
        re.compile(
            rf"\b{NEGATION}\b[^.!?\n]{{1,80}}(?:[\u2014\u2013]|&mdash;|&ndash;|;\s|--)\s*"
            rf"[^.!?\n]{{1,80}}(?:\b(?:is|are|was|were)\b|{RIGHT_COPULA})",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "FAIL",
        "the-point-is",
        re.compile(r"\bthe\s+point\s+(?:is|isn['\u2019]t|is\s+not)\b", re.IGNORECASE),
    ),
    Rule(
        "FAIL",
        "not-because-because",
        re.compile(
            r"\bnot\s+because\s+[^.!?\n]{1,100}[.!?]\s+because\s+", re.IGNORECASE
        ),
    ),
    Rule(
        "FAIL",
        "not-as-as",
        re.compile(r"\bnot\s+as\s+[^.!?\n]{1,100}[.!?]\s+as\s+", re.IGNORECASE),
    ),
    Rule(
        "FAIL",
        "not-just-but",
        re.compile(
            r"\bnot\s+(?:just|only|merely|simply)\b[^.!?\n]{1,80}\bbut\b", re.IGNORECASE
        ),
    ),
    Rule(
        "FAIL", "more-than-just", re.compile(r"\bmore\s+than\s+just\b", re.IGNORECASE)
    ),
    Rule(
        "WARN",
        "its-about",
        re.compile(r"\b(?:it['\u2019]s|it\s+is)\s+about\b", re.IGNORECASE),
    ),
    Rule("WARN", "this-is-why", re.compile(r"\bthis\s+is\s+why\b", re.IGNORECASE)),
    Rule(
        "WARN",
        "question-is",
        re.compile(
            r"\b(?:the\s+)?(?:question|lesson|key|core|move)\s+(?:is|isn['\u2019]t|is\s+not)\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "WARN",
        "empty-adverbial-opener",
        re.compile(
            r"^\s*(?:importantly|notably|ultimately|fundamentally|essentially|in practice),?\b",
            re.IGNORECASE,
        ),
    ),
]

ALLOWLIST_RE = re.compile(r"voice_lint:allow\s+([A-Za-z0-9\-_ ]+)")

TARGETS = [
    # public-facing copy and spec-ledger docs in this repo. Adjust if
    # additional content paths land later (e.g. site/, docs/, examples/).
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "specs/**/*.md",
    "docs/**/*.md",
]

SKIP_DIRS = {"node_modules", "dist", ".git", "_legacy", ".venv", "data"}


def iter_files(root: Path, targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in targets:
        for path in root.glob(pattern):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                files.append(path)
    return sorted(set(files))


def line_allowlist(line: str) -> set[str]:
    match = ALLOWLIST_RE.search(line)
    if not match:
        return set()
    return {label.strip() for label in match.group(1).split() if label.strip()}


def rules() -> list[Rule]:
    out = [phrase_rule("FAIL", f"banned-{phrase}", phrase) for phrase in BANNED_FAIL]
    out.extend(phrase_rule("WARN", f"weak-{phrase}", phrase) for phrase in BANNED_WARN)
    out.extend(STRUCTURAL)
    return out


def scan(
    path: Path, active_rules: list[Rule], filter_label: str | None = None
) -> list[tuple[str, int, str, str]]:
    offenses: list[tuple[str, int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return offenses

    for line_no, line in enumerate(text.splitlines(), start=1):
        allowed = line_allowlist(line)
        if "all" in allowed:
            continue
        for severity, label, pattern in active_rules:
            if filter_label and filter_label != label:
                continue
            if label in allowed:
                continue
            if pattern.search(line):
                offenses.append((severity, line_no, label, line.strip()))
    return offenses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voice_lint", description="voice-tell lint")
    parser.add_argument("--root", type=Path, default=ROOT, help="repo root to scan")
    parser.add_argument("--label", default=None, help="filter output to one label")
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        default=None,
        help="override TARGETS glob; repeatable",
    )
    parser.add_argument(
        "--warn-only", action="store_true", help="print findings but exit 0"
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    targets = args.targets if args.targets else TARGETS
    files = iter_files(root, targets)
    total = 0
    fail_total = 0
    warn_total = 0

    for file_path in files:
        for severity, line_no, label, line_text in scan(
            file_path, rules(), filter_label=args.label
        ):
            rel = file_path.relative_to(root).as_posix()
            snippet = line_text if len(line_text) <= 200 else line_text[:200] + "..."
            print(f"{rel}:{line_no}: {severity}: {label} -> {snippet}")
            total += 1
            if severity == "FAIL":
                fail_total += 1
            else:
                warn_total += 1

    suffix = f" (filtered by label={args.label!r})" if args.label else ""
    if total:
        print(
            "\nvoice-lint: "
            f"{fail_total} FAIL, {warn_total} WARN across "
            f"{len(files)} file(s) scanned{suffix}.",
            file=sys.stderr,
        )
        return 0 if args.warn_only else 1
    print(f"voice-lint: clean. {len(files)} file(s) scanned{suffix}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
