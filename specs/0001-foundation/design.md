# Spec 0001 — Design

## Layered architecture

```
config/sources.yaml         (single source of truth)
        |
        v
src/sports_os/registry.py   (typed parse: Provider / League / Registry)
        |
        v
src/sports_os/sources/      (one module per provider)
   understat.py             (HTTP + cache + Shot/Match models)
   statsbomb_open.py        (v1; not in 0001 scope)
        |
        v
src/sports_os/cli.py        (thin CLI: registry / ingest / analyze)
        |
        v
app.py                      (Streamlit; reads from cache + value layer)
        |
        v
src/sports_os/value/        (socceraction wrappers; v1, not in 0001)
```

## Cache + offline mode

Every fetcher writes its raw responses to `data/cache/<provider>/...` so
the test suite (and the Streamlit demo's first run) can operate offline.
Cache TTL is per-provider from the registry. v0 uses simple
file-existence checks; v1 adds TTL-aware invalidation.

## Test discipline

- Every fetcher has a unit test that runs offline against the bundled
  fixture under `tests/fixtures/<provider>/`.
- The CLI test runs `python -m sports_os.cli registry` end-to-end and
  asserts the parsed output is JSON-shaped.
- No test hits the live network in CI.

## Gates flow

```
pre-commit (local) — voice_lint, validate_sensitive_disclosures
ci.yml             — pytest, voice_lint, validate_sensitive_disclosures,
                     spec_check
```

`spec_check.py` parses `specs/*/requirements.md`, extracts every
`R-*-NNN` ID, and grep-confirms each ID appears in either source code or
tests. Missing IDs fail CI.
