"""Tests for the Understat fetcher. Covers R-FND-003 + R-FND-006."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import sports_os.sources.understat as understat
from sports_os.sources.understat import FetchError, Shot, fetch_match_shots


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "understat"


@pytest.fixture
def cache_with_fixture(tmp_path: Path) -> Path:
    """Stage the bundled fixture under a temp cache root.

    The fetcher's on-disk layout is `<cache_dir>/matches/<id>.json`, so the
    fixture file gets copied into that exact location to exercise the
    cache-hit path without touching the network.
    """
    cache_dir = tmp_path / "understat"
    matches_dir = cache_dir / "matches"
    matches_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "12345.json", matches_dir / "12345.json")
    return cache_dir


def test_offline_fetch_returns_shots(cache_with_fixture: Path) -> None:
    shots = fetch_match_shots("12345", cache_dir=cache_with_fixture, use_network=False)
    assert len(shots) == 3
    assert all(isinstance(s, Shot) for s in shots)
    assert sum(1 for s in shots if s.result == "Goal") == 2


def test_offline_missing_match_raises(tmp_path: Path) -> None:
    cache_dir = tmp_path / "understat"
    with pytest.raises(FetchError):
        fetch_match_shots("missing", cache_dir=cache_dir, use_network=False)


def test_shot_model_enforces_xg_bounds(cache_with_fixture: Path) -> None:
    shots = fetch_match_shots("12345", cache_dir=cache_with_fixture, use_network=False)
    for s in shots:
        assert 0.0 <= s.xG <= 1.0


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_network_parse_maps_understat_payload_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The cache-hit fixtures never exercise the HTML parse + field-normalization
    # block. Drive it directly: empty cache forces the network branch, and a
    # stubbed httpx.Client.get returns a raw Understat-style match page. This
    # pins the payload->Shot key mapping (xG<-xG, team<-{side}_team,
    # result<-result, body_part<-shotType) so swapping a source key breaks here.
    html = (FIXTURES / "match_page.html").read_text(encoding="utf-8")
    monkeypatch.setattr(
        understat.httpx.Client,
        "get",
        lambda self, url: _FakeResponse(html),
    )

    cache_dir = tmp_path / "understat"
    shots = fetch_match_shots("99999", cache_dir=cache_dir, use_network=True)

    assert len(shots) == 2
    by_player = {s.player: s for s in shots}

    saka = by_player["Bukayo Saka"]
    assert saka.team == "Arsenal"  # home side -> h_team
    assert saka.xG == 0.31
    assert saka.result == "Goal"
    assert saka.body_part == "RightFoot"  # <- shotType
    assert saka.minute == 12

    salah = by_player["Mohamed Salah"]
    assert salah.team == "Liverpool"  # away side -> a_team
    assert salah.xG == 0.18
    assert salah.result == "SavedShot"

    # Parsed shots get cached on success for the next cache-hit read.
    assert (cache_dir / "matches" / "99999.json").exists()
