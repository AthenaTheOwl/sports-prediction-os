# STATUS — sports-prediction-os

Last updated: 2026-06-05

## Where the repo is

| Layer | State |
|---|---|
| Foundation (spec 0001) | Shipped — registry + Understat fetcher + CLI + 3 gates |
| Ops ledger (spec 0003) | Shipped — RunManifest + canonical id + date-bucketed ledger |
| Value layer (spec 0002, future) | Not started — socceraction VAEP/xT integration is next |
| Streamlit demo (spec 0004, future) | Not started — depends on the value layer |
| Weekly eval loop (spec 0005, future) | Not started — depends on the value layer |

## What just landed

- `src/sports_os/ops/run_manifest.py` — typed RunManifest record,
  content-hashed id, date-bucketed ledger layout.
- `ops/runs/` ledger directory (gitignored entries; the `.gitkeep`
  keeps the directory in tree).
- `specs/0003-ops-ledger/` with the 4-file pattern matching specs/0001.

## What runs today

```bash
uv run sports-os registry          # dump the source registry
uv run sports-os ingest understat --match-id 12345 --offline  # use the bundled fixture
uv run sports-os analyze           # placeholder; lands in spec 0002
uv run pytest                      # 22 tests, all green offline
```

## Next moves (per the portfolio backlog synthesis)

- spec 0002: socceraction VAEP/xT wrapper consuming Understat shots
- spec 0004: Streamlit demo (per-match value timeline)
- spec 0005: weekly eval loop (hold out most recent matchday, score
  the top value-adding actions against actual goals/assists/key passes)
