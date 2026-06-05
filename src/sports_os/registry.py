"""Source registry loader.

Parses `config/sources.yaml` into Pydantic models. The runner consults
this — fetchers must declare a `provider_id` that resolves cleanly here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import datetime as _dt

import yaml
from pydantic import BaseModel, Field, field_validator


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "config" / "sources.yaml"


class Provider(BaseModel):
    id: str
    name: str
    kind: Literal["free-web", "github-static", "auth-api"]
    base_url: str
    rate_limit_per_sec: float = Field(gt=0)
    cache_ttl_days: int = Field(ge=0)
    license: str
    status: Literal["active", "paused", "retired"]
    leagues_supported: list[str] = Field(default_factory=list)
    notes: str | None = None


class League(BaseModel):
    id: str
    name: str
    season_start_month: int = Field(ge=1, le=12)
    seasons_in_scope: list[str]
    priority: int = Field(ge=1)


class Registry(BaseModel):
    version: int
    last_curated: str
    providers: list[Provider]
    leagues: list[League]

    @field_validator("last_curated", mode="before")
    @classmethod
    def _coerce_date(cls, v: object) -> str:
        if isinstance(v, _dt.date):
            return v.isoformat()
        return str(v)

    def provider(self, provider_id: str) -> Provider:
        for p in self.providers:
            if p.id == provider_id:
                return p
        raise KeyError(f"unknown provider id: {provider_id}")

    def league(self, league_id: str) -> League:
        for league in self.leagues:
            if league.id == league_id:
                return league
        raise KeyError(f"unknown league id: {league_id}")


def load_registry(path: Path | str = DEFAULT_REGISTRY) -> Registry:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Registry.model_validate(data)
