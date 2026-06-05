"""Smoke tests for the CLI. Covers R-FND-004."""

from __future__ import annotations

import io
import json
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from sports_os.cli import main


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "understat"


def test_registry_subcommand_prints_json() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["registry"])
    assert rc == 0
    parsed = json.loads(buf.getvalue())
    assert "providers" in parsed
    assert "leagues" in parsed


def test_ingest_offline_uses_fixture_cache(tmp_path: Path) -> None:
    cache_dir = tmp_path / "understat"
    (cache_dir / "matches").mkdir(parents=True)
    shutil.copy(FIXTURES / "12345.json", cache_dir / "matches" / "12345.json")

    rc = main(
        [
            "ingest",
            "understat",
            "--match-id",
            "12345",
            "--offline",
            "--cache-dir",
            str(cache_dir),
        ]
    )
    assert rc == 0


def test_ingest_unknown_provider_returns_nonzero() -> None:
    with pytest.raises(SystemExit):
        # argparse choices reject unknown providers up front
        main(["ingest", "does-not-exist", "--match-id", "x", "--offline"])


def test_analyze_subcommand_runs() -> None:
    rc = main(["analyze"])
    assert rc == 0
