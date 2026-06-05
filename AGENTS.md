# AGENTS.md — sports-prediction-os

Operating contract for AI agents (Claude, Codex, Cursor) working in this
repo. The conventions match the rest of the AthenaTheOwl portfolio so an
agent that's already trained on procurement-negotiation-lab or
ai-field-brief recognizes the shape.

## What this repo is

A small, scoped lab for soccer event-data analysis. The goal isn't a
winner-prediction model — it's possession-value + next-event modeling
with the same eval-loop discipline the rest of the portfolio runs on.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `data-fetcher` | Pulls Understat / StatsBomb data; caches on disk; respects rate limits |
| `value-runner` | Computes VAEP / xT via socceraction wrappers |
| `surface-builder` | Streamlit UI; per-match value timeline + top-N actions |
| `eval-curator` | Holds out the most recent matchday; scores models against actuals |
| `weekly-runner` | Per-week run: ingest → value → eval → publish |

These roles exist in spec ledger; not all are implemented in v0.

## Gates (CI + local)

Before pushing, every contributor — human or agent — runs:

```bash
uv run pytest
python scripts/voice_lint.py
python scripts/validate_sensitive_disclosures.py
python scripts/spec_check.py
```

A PR that fails any gate is not merged. The gates are mirrored from
mcp-security-lab (sensitive-disclosures) and the portfolio voice spec —
see headers in each script for the canonical source.

## Source registry

`config/sources.yaml` is the single source of truth for which leagues,
seasons, and providers are in scope. Adding a new league = editing the
registry + writing one matching fetcher under `src/sports_os/sources/`.

## Voice constraints

- No marketing words. <!-- voice_lint:allow all --> The banned set lives
  in `scripts/voice_lint.py::BANNED_FAIL`. Read the script for the full
  list — repeating each term here would trip the linter.
- No antithetical reversals as a structural device.
  <!-- voice_lint:allow antithetical-dash --> The "X isn't Y — Z is the W"
  shape is the AI tell. One per surface, when the contrast does real work.
- Plain assertions. The math + the data are the moat; the voice is the
  scaffolding.

## Out of scope

- Real-time data feeds. Public datasets only; refresh on cron, not push.
- Betting markets. No odds ingestion, no value-bet detection, no money in
  the loop.
- Other sports (tennis / esports). The research brief says they're
  credible extensions but Soccer first; scope discipline.
- A "general analytics platform". This is a focused lab.
