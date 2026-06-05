"""Foundation smoke tests.

Each test references a requirement ID from specs/0001-foundation/ so the
spec_check gate sees the ID outside specs/.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_R_FND_001_repo_scaffold_files_exist() -> None:
    """R-FND-001: license + readme + notice + pyproject all present."""
    for f in ("LICENSE", "README.md", "NOTICE", "AGENTS.md", "pyproject.toml"):
        assert (ROOT / f).exists(), f"missing scaffold file: {f}"


def test_R_FND_005_gate_scripts_exist() -> None:
    """R-FND-005: three gates ship as scripts."""
    for g in (
        "voice_lint.py",
        "validate_sensitive_disclosures.py",
        "spec_check.py",
    ):
        assert (ROOT / "scripts" / g).exists(), f"missing gate: {g}"


def test_R_FND_007_portfolio_door_is_documented() -> None:
    """R-FND-007: README claims door N° 19; portfolio integration tracked."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "N° 19" in readme, "README must declare door N° 19"
    assert "Portfolio integration" in (
        ROOT / "specs" / "0001-foundation" / "requirements.md"
    ).read_text(encoding="utf-8") or "portfolio integration" in (
        ROOT / "specs" / "0001-foundation" / "requirements.md"
    ).read_text(encoding="utf-8")
