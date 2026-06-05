"""Tests for the source registry. Covers R-FND-002."""

from __future__ import annotations

from pathlib import Path

import pytest

from sports_os.registry import Provider, Registry, load_registry


REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry()


def test_registry_loads_and_validates(registry: Registry) -> None:
    assert registry.version >= 1
    assert len(registry.providers) >= 2
    assert len(registry.leagues) >= 5


def test_understat_provider_is_active(registry: Registry) -> None:
    p = registry.provider("understat")
    assert isinstance(p, Provider)
    assert p.status == "active"
    assert p.rate_limit_per_sec > 0


def test_every_provider_supports_known_leagues(registry: Registry) -> None:
    league_ids = {league.id for league in registry.leagues}
    for p in registry.providers:
        for lid in p.leagues_supported:
            assert lid in league_ids, f"{p.id} declares unknown league {lid}"


def test_unknown_provider_raises(registry: Registry) -> None:
    with pytest.raises(KeyError):
        registry.provider("does-not-exist")
