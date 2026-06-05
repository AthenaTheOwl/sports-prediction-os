# Spec 0001 — Foundation

## R-FND-001 — repo scaffold
Repo lives at `e:/claude_code/random-apps/sports-prediction-os`. MIT
license; copyright Vignesh Gopalakrishnan. NOTICE file credits
socceraction + StatsBomb + Understat per their licenses.

## R-FND-002 — source registry as YAML
`config/sources.yaml` is the single source of truth for providers +
leagues + seasons. `src/sports_os/registry.py` parses it into typed
Pydantic models. Adding a provider = (a) registry entry, (b) matching
fetcher under `src/sports_os/sources/`.

## R-FND-003 — Understat fetcher
`src/sports_os/sources/understat.py` fetches one match's shot stream
from Understat. Caches JSON on disk. Offline mode reads cache only.

## R-FND-004 — CLI
`uv run sports-os --help` shows `registry`, `ingest`, `analyze`. Each
subcommand delegates to one function so the Streamlit UI can share
primitives.

## R-FND-005 — gates
Three gates run in CI + locally: `voice_lint.py` (banlist + structural
anti-patterns mirrored from athena-site), `validate_sensitive_disclosures.py`
(mirrored from mcp-security-lab), `spec_check.py` (every R-FND-* / R-*-*
referenced in spec is implemented + tested).

## R-FND-006 — fixtures
`tests/fixtures/understat/match-12345.json` ships a real fetched-then-
sanitized fixture so the test suite runs offline. The fixture file path
mirrors `data/cache/understat/matches/<id>.json` so a test can point the
cache at fixtures and skip the network entirely.

## R-FND-007 — portfolio integration (deferred to follow-up PR on athena-site)
Door N° 19, status `active`. `ops/portfolio-manifest.yml` entry +
`doors.json` card live in athena-site, not here.
