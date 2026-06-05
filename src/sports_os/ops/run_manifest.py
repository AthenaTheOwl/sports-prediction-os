"""RunManifest: typed record of one ingest/value/eval run.

A manifest captures what went in, what came out, and the version of the
code + fixtures that produced it. Hashing inputs + outputs into the id
means the same run on the same data lands at the same path — runs are
deduplicated by content, and the ledger doubles as a replay index.

Layout
------

::

    ops/
      runs/
        2026/
          06/
            05/
              ingest-7a2b8f3e1d9c.json
              value-cf42ee...json
              eval-7a2b8f...json

Each file is a single ``RunManifest`` JSON object. Today (R-OPS-001) the
ledger is append-only; no eviction policy.

The ``RunKind`` enum is small on purpose: every run in the OS belongs to
one of three families. New families are added by extending the enum.
"""

from __future__ import annotations

import enum
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER_ROOT = REPO_ROOT / "ops" / "runs"


class RunKind(str, enum.Enum):
    INGEST = "ingest"
    VALUE = "value"
    EVAL = "eval"


class RunManifest(BaseModel):
    """One ingest/value/eval run, content-hashed for replay determinism."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=12, max_length=64)
    kind: RunKind
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    code_sha: str | None = None
    fixture_sha256: str | None = None
    run_date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO date the run was recorded; controls the path bucket.",
    )


def canonical_id(
    kind: RunKind,
    inputs: list[str],
    outputs: list[str],
    code_sha: str | None = None,
    fixture_sha256: str | None = None,
) -> str:
    """Compute the content hash that becomes ``manifest.id``.

    The hash covers (kind, sorted inputs, sorted outputs, code_sha,
    fixture_sha256) so reordering input/output lists doesn't change the
    id. Returns a 16-char hex prefix — short enough to keep file paths
    readable, long enough that the collision risk on a single-tenant
    repo is negligible.
    """
    payload = {
        "kind": kind.value,
        "inputs": sorted(inputs),
        "outputs": sorted(outputs),
        "code_sha": code_sha,
        "fixture_sha256": fixture_sha256,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def _date_path(ledger_root: Path, run_date: str) -> Path:
    yyyy, mm, dd = run_date.split("-")
    return ledger_root / yyyy / mm / dd


def write_manifest(
    kind: RunKind | str,
    inputs: list[str],
    outputs: list[str],
    *,
    code_sha: str | None = None,
    fixture_sha256: str | None = None,
    run_date: str | None = None,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    today: date | None = None,
) -> tuple[RunManifest, Path]:
    """Write a manifest + return (manifest, on-disk path).

    Idempotent — the same inputs + outputs + code_sha + fixture_sha256
    on the same date produce the same id and the same path. Re-writing
    just overwrites the file with the equivalent content.

    Parameters
    ----------
    kind:           ``RunKind`` or the matching string
    inputs/outputs: file paths or content references; order doesn't matter
    code_sha:       optional git sha of the code producing the run
    fixture_sha256: optional sha of the fixture corpus
    run_date:       ISO date; default ``today`` arg or system date
    ledger_root:    override the default ``ops/runs/`` location
    today:          inject a fixed date for tests
    """
    if isinstance(kind, str):
        kind = RunKind(kind)
    if run_date is None:
        if today is None:
            raise ValueError(
                "run_date must be provided (or today=) — sports-os does not "
                "consult the system clock implicitly"
            )
        run_date = today.isoformat()

    rid = canonical_id(kind, inputs, outputs, code_sha, fixture_sha256)
    manifest = RunManifest(
        id=rid,
        kind=kind,
        inputs=inputs,
        outputs=outputs,
        code_sha=code_sha,
        fixture_sha256=fixture_sha256,
        run_date=run_date,
    )

    bucket = _date_path(ledger_root, run_date)
    bucket.mkdir(parents=True, exist_ok=True)
    path = bucket / f"{kind.value}-{rid}.json"
    path.write_text(
        manifest.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )
    return manifest, path


def read_manifest(path: Path) -> RunManifest:
    return RunManifest.model_validate_json(path.read_text(encoding="utf-8"))


def list_manifests(
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
) -> list[tuple[Path, RunManifest]]:
    """Walk the ledger root and return every manifest path + parsed record."""
    out: list[tuple[Path, RunManifest]] = []
    if not ledger_root.is_dir():
        return out
    for path in sorted(ledger_root.rglob("*.json")):
        try:
            out.append((path, read_manifest(path)))
        except (OSError, ValueError):
            continue
    return out
