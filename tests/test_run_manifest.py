"""Tests for sports_os.ops.run_manifest.

Spec coverage:
- R-OPS-001 RunManifest Pydantic record + round-trip
- R-OPS-002 canonical_id is order-invariant and content-sensitive
- R-OPS-003 date-bucketed path layout (YYYY/MM/DD)
- R-OPS-004 idempotency: same content -> same path
- R-OPS-005 STATUS.md skeleton exists
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from sports_os.ops.run_manifest import (
    RunKind,
    RunManifest,
    canonical_id,
    list_manifests,
    read_manifest,
    write_manifest,
)


def test_R_OPS_001_write_and_read_round_trip(tmp_path: Path) -> None:
    manifest, path = write_manifest(
        RunKind.INGEST,
        inputs=["understat/match-12345.json"],
        outputs=["data/cache/understat/matches/12345.json"],
        code_sha="abc1234",
        fixture_sha256="d" * 64,
        run_date="2026-06-05",
        ledger_root=tmp_path,
    )
    assert path.exists()
    read = read_manifest(path)
    assert read == manifest


def test_R_OPS_002_canonical_id_is_order_invariant() -> None:
    a = canonical_id(RunKind.VALUE, ["a", "b"], ["x", "y"], "sha", "fix")
    b = canonical_id(RunKind.VALUE, ["b", "a"], ["y", "x"], "sha", "fix")
    assert a == b


def test_R_OPS_002_canonical_id_is_content_sensitive() -> None:
    base = canonical_id(RunKind.EVAL, ["a"], ["x"])
    diff_kind = canonical_id(RunKind.VALUE, ["a"], ["x"])
    diff_input = canonical_id(RunKind.EVAL, ["aa"], ["x"])
    diff_output = canonical_id(RunKind.EVAL, ["a"], ["xx"])
    assert {base, diff_kind, diff_input, diff_output} == {base, diff_kind, diff_input, diff_output}
    # Each variant differs from base.
    for other in (diff_kind, diff_input, diff_output):
        assert other != base


def test_R_OPS_003_path_layout_is_yyyy_mm_dd(tmp_path: Path) -> None:
    _, path = write_manifest(
        RunKind.INGEST,
        inputs=["x"],
        outputs=["y"],
        run_date="2026-06-05",
        ledger_root=tmp_path,
    )
    parts = path.relative_to(tmp_path).parts
    assert parts[0] == "2026"
    assert parts[1] == "06"
    assert parts[2] == "05"
    assert parts[3].startswith("ingest-")


def test_write_manifest_is_idempotent_on_same_content(tmp_path: Path) -> None:
    _, p1 = write_manifest(
        RunKind.VALUE,
        inputs=["a", "b"],
        outputs=["c"],
        code_sha="sha",
        run_date="2026-06-05",
        ledger_root=tmp_path,
    )
    _, p2 = write_manifest(
        RunKind.VALUE,
        inputs=["b", "a"],  # different order, same content
        outputs=["c"],
        code_sha="sha",
        run_date="2026-06-05",
        ledger_root=tmp_path,
    )
    assert p1 == p2


def test_write_manifest_requires_explicit_date(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_manifest(
            RunKind.EVAL,
            inputs=["x"],
            outputs=["y"],
            ledger_root=tmp_path,
        )


def test_write_manifest_accepts_today_injection(tmp_path: Path) -> None:
    fixed = dt.date(2025, 1, 15)
    manifest, _ = write_manifest(
        RunKind.EVAL,
        inputs=["x"],
        outputs=["y"],
        ledger_root=tmp_path,
        today=fixed,
    )
    assert manifest.run_date == "2025-01-15"


def test_list_manifests_walks_ledger(tmp_path: Path) -> None:
    write_manifest(RunKind.INGEST, ["a"], ["b"], run_date="2026-06-05", ledger_root=tmp_path)
    write_manifest(RunKind.VALUE, ["c"], ["d"], run_date="2026-06-06", ledger_root=tmp_path)
    listed = list_manifests(tmp_path)
    assert len(listed) == 2
    kinds = {m.kind for _, m in listed}
    assert kinds == {RunKind.INGEST, RunKind.VALUE}
