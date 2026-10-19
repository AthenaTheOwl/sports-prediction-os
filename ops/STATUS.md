# STATUS — sports-prediction-os

Last updated: 2026-10-19

## Current state

| Layer | State |
|---|---|
| Foundation (spec 0001) | Shipped — registry + Understat fetcher + CLI + 3 gates |
| Ops ledger (spec 0003) | Shipped — RunManifest + canonical id + date-bucketed ledger |
| Value layer (spec 0002, future) | Not started — socceraction VAEP/xT integration is next |
| Streamlit demo (spec 0004) | Shipped locally — `streamlit_app.py` runs offline; not yet deployed to Streamlit Cloud |
| Weekly eval loop (spec 0005, future) | Not started — depends on the value layer |

## What just landed

- `src/sports_os/analysis.py` — `load_report` rejects nonfinite or
  out-of-range xG, shots for a team outside the match, and invalid or
  mismatched scorelines; the headline finding no longer misnames the xG
  leader when no side beats its xG. See
  `docs/match-integrity-and-evaluation.md`.
- `src/sports_os/ops/run_manifest.py` — typed RunManifest record,
  content-hashed id, date-bucketed ledger layout.
- `ops/runs/` ledger directory (gitignored entries; the `.gitkeep`
  keeps the directory in tree).
- `specs/0003-ops-ledger/` with the 4-file pattern matching specs/0001.

## What runs today

```bash
uv run sports-os show              # ranked shot table + headline finding (offline, sample match)
uv run sports-os registry          # dump the source registry
uv run sports-os ingest understat --match-id 12345 --offline  # use the bundled fixture
uv run sports-os analyze           # placeholder; lands in spec 0002
uv run pytest                      # 61 tests, all green offline
```

## Known limits

- socceraction VAEP/xT integration has not started.
- Streamlit Cloud deployment is still pending; the README live URL remains a placeholder.
- Weekly eval is still blocked on the value layer.

## Next feature queue

- spec 0002: socceraction VAEP/xT wrapper consuming Understat shots
- spec 0004: deploy Streamlit app to Streamlit Cloud (ships locally; live URL placeholder in README pending)
- spec 0005: weekly eval loop (hold out most recent matchday, score
  the top value-adding actions against actual goals/assists/key passes)
