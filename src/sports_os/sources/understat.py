"""Understat fetcher.

Understat embeds match + shot data as JSON in `<script>` tags on each page.
We extract by regex, then JSON-decode. No auth required. Network is
optional in tests via on-disk fixtures under `tests/fixtures/understat/`.

Respect: `crawl-delay: 5` (we use the registry's rate_limit_per_sec).

API surface:
    fetch_match_shots(match_id, *, cache_dir=DEFAULT_CACHE) -> list[Shot]
    fetch_league_matches(league, season, *, cache_dir=...) -> list[Match]

Shape returned is normalized to Pydantic models in models.py so consumers
don't need to know Understat's encoding.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field


DEFAULT_CACHE = Path(__file__).resolve().parents[3] / "data" / "cache" / "understat"
USER_AGENT = "sports-prediction-os/0.1 (+https://github.com/AthenaTheOwl/sports-prediction-os)"

# Understat embeds payloads as JSON.parse('escaped string'); the outer
# script tag also names the variable.
_PAYLOAD_RE = re.compile(
    r"var\s+(?P<name>\w+)\s*=\s*JSON\.parse\('(?P<payload>(?:[^'\\]|\\.)*)'\)"
)


class Shot(BaseModel):
    """Single shot record from an Understat match page."""

    id: str
    minute: int = Field(ge=0)
    player: str
    team: str
    x: float
    y: float
    xG: float = Field(ge=0, le=1)
    result: str  # Goal, SavedShot, MissedShots, BlockedShot, ShotOnPost, OwnGoal
    situation: str | None = None
    body_part: str | None = None


class Match(BaseModel):
    """Single match summary from an Understat league page."""

    id: str
    isResult: bool
    h_team: str
    a_team: str
    h_goals: int | None = None
    a_goals: int | None = None
    datetime: str


class FetchError(RuntimeError):
    """Raised when the fetch fails AND no cached fallback is available."""


def _cache_path(cache_dir: Path, kind: str, identifier: str) -> Path:
    return cache_dir / kind / f"{identifier}.json"


def _decode_payload(raw: str) -> Any:
    # Understat double-escapes; one decode layer is enough for JSON.parse('...').
    return json.loads(raw.encode("latin-1").decode("unicode_escape"))


def _extract_payload(html: str, variable_name: str) -> Any | None:
    for match in _PAYLOAD_RE.finditer(html):
        if match.group("name") == variable_name:
            return _decode_payload(match.group("payload"))
    return None


def fetch_match_shots(
    match_id: str,
    *,
    cache_dir: Path = DEFAULT_CACHE,
    use_network: bool = True,
) -> list[Shot]:
    """Fetch shot data for one match. Cache-on-disk on success."""
    cache_path = _cache_path(cache_dir, "matches", match_id)
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        return [Shot.model_validate(row) for row in cached]

    if not use_network:
        raise FetchError(f"no cached data for match_id={match_id} and use_network=False")

    url = f"https://understat.com/match/{match_id}"
    try:
        with httpx.Client(timeout=20.0, headers={"User-Agent": USER_AGENT}) as c:
            r = c.get(url)
            r.raise_for_status()
            html = r.text
    except httpx.HTTPError as exc:
        raise FetchError(f"fetch failed for match_id={match_id}: {exc}") from exc

    payload = _extract_payload(html, "shotsData")
    if payload is None:
        raise FetchError(f"shotsData not found on match page {match_id}")

    rows: list[dict] = []
    for side in ("h", "a"):
        for entry in payload.get(side, []):
            rows.append(
                {
                    "id": str(entry.get("id", "")),
                    "minute": int(entry.get("minute", 0)),
                    "player": entry.get("player", ""),
                    "team": entry.get(f"{side}_team", entry.get("team", "")),
                    "x": float(entry.get("X", entry.get("x", 0))),
                    "y": float(entry.get("Y", entry.get("y", 0))),
                    "xG": float(entry.get("xG", 0)),
                    "result": entry.get("result", ""),
                    "situation": entry.get("situation"),
                    "body_part": entry.get("shotType"),
                }
            )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    return [Shot.model_validate(row) for row in rows]
