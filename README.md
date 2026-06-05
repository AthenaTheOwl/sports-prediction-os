# N° 21 · sports-prediction-os

An analytical OS for soccer that goes beyond match-result prediction. Built
around **possession value** and **next-event modeling** on public event
data, with a deployable Streamlit demo and a weekly iteration loop that
keeps the models honest against the prior week's actual matches.

Not a betting product. The goal is an interesting analytical surface
backed by real public data, with the same eval discipline the rest of the
portfolio runs on.

## What it covers (v0)

- **Data layer.** Understat fetcher for the big-six European leagues (EPL,
  La Liga, Serie A, Bundesliga, Ligue 1, RFPL) with cached on-disk JSON.
  StatsBomb open-data fetcher for verified-event matches. Schema in
  `schemas/`.
- **Value layer.** [socceraction](https://github.com/ML-KULeuven/socceraction)
  (MIT, KU Leuven) computes xT and VAEP off SPADL action streams. The
  primitives are stable and battle-tested; we wrap, we don't reinvent.
- **Surface layer.** Streamlit app that loads a match by `match_id` and
  renders the possession-value timeline plus the top-10 value-adding
  actions, with citations back to the source event.
- **Eval layer.** Per-week eval cases: hold out the most recent matchday,
  recompute on the prior 4 weeks, score whether the highest-value actions
  on Saturday match the goals + assists + key passes the bookmakers' data
  recorded. A loop, not a one-shot demo.

## What it deliberately is not

- A winner-prediction model. Commodity surface. Plenty of public projects
  already do it; the angle is uninteresting.
- A live betting feed. No real-time integration, no money in the loop.
- A general analytics platform for every sport. Soccer first — tennis +
  esports are credible extensions per the [research brief](docs/research-brief.md),
  but **scope discipline matters more than breadth**.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | matches socceraction + OpenSTARLab |
| Package mgr | `uv` | portfolio convention |
| Value | `socceraction` (MIT) | reference VAEP / xT implementation |
| Multi-provider unify | OpenSTARLab (Apache-2.0) [optional, v1+] | future-facing |
| UI | Streamlit | matches supplier-risk-rag-agent shape |
| Deploy | Streamlit Community Cloud (BYOK pattern) | free tier; reuses portfolio playbook |
| Data | Understat (free) + StatsBomb open (CC BY-NC-SA) | public; respects rate limits |
| License (code) | MIT | portfolio standard |
| License (derived data) | StatsBomb terms cascade (NC-SA) | documented per dataset |

## Quick start

```bash
git clone https://github.com/AthenaTheOwl/sports-prediction-os
cd sports-prediction-os
uv sync
uv run sports-os --help
uv run streamlit run app.py
```

See [docs/playbook.md](docs/playbook.md) for the weekly run.

## Status

v0 scaffold landing 2026-06-05. Tracker:

- [x] Repo scaffold + spec 0001 (foundation)
- [x] Understat fetcher with offline fixture fallback
- [x] CLI shape (`sports-os ingest`, `sports-os analyze`)
- [x] Voice / spec / sensitive-disclosures gates wired
- [ ] socceraction integration with sample StatsBomb match
- [ ] Streamlit demo deployed
- [ ] First weekly eval run committed

See [ops/STATUS.md](ops/STATUS.md) when it lands.
