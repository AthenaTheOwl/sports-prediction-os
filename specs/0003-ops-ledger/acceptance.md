# Spec 0003 — Acceptance

```bash
cd e:/claude_code/random-apps/sports-prediction-os
uv run pytest tests/test_run_manifest.py -v
uv run python -c "
from datetime import date
from sports_os.ops import write_manifest, RunKind
m, p = write_manifest(
    RunKind.INGEST,
    inputs=['understat/match-12345.json'],
    outputs=['data/cache/understat/matches/12345.json'],
    code_sha='HEAD',
    fixture_sha256='d'*64,
    today=date(2026, 6, 5),
)
print(f'wrote {p}')
print(f'id: {m.id}')
"
ls ops/runs/2026/06/05/
```

Acceptance:
- `tests/test_run_manifest.py` 9/9 pass
- the smoke run writes one file under `ops/runs/2026/06/05/ingest-<id>.json`
- the file's `id` field matches the file basename suffix
- running the same smoke twice writes to the same path (idempotent)
- `ops/STATUS.md` exists and names the current state of the repo
