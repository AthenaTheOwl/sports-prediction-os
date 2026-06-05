# Spec 0001 — Acceptance

```bash
cd e:/claude_code/random-apps/sports-prediction-os
uv sync                                              # install deps
uv run pytest                                        # all green
uv run python -m sports_os.cli registry              # prints valid JSON
uv run python -m sports_os.cli ingest understat \
    --match-id 12345 --offline                       # reads fixture
uv run python scripts/voice_lint.py                  # clean
uv run python scripts/validate_sensitive_disclosures.py  # clean
uv run python scripts/spec_check.py                  # every R-FND-* satisfied
```

On the v0 ship:
- `git log` shows 1-2 commits totaling the scaffold
- GitHub repo `AthenaTheOwl/sports-prediction-os` exists, public, MIT
- README's status checklist shows v0 boxes ticked
- v1 work (socceraction + Streamlit + per-week eval loop) tracked in
  spec 0002 + 0003 (not yet authored)
