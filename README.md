# sports-prediction-os

Arsenal drew Liverpool 2-2 and the box score calls it even. The shots don't.
Liverpool built 2.13 expected goals and walked away with two; Arsenal built 1.49
and also got two. Same scoreline, different luck. sports-prediction-os is a soccer
analytics surface that reads the gap between what a team should have scored and
what the keeper let in — and tells you which side the scoreboard flattered.

## What it does

Most public soccer projects predict the winner. That's a crowded, boring corner —
the result of a match is the least information-dense thing about it. The interesting
signal lives one layer down, in possession value and shot quality: who created the
better chances, who converted above or below them, which actions actually moved the
ball toward a goal.

So this reads matches, not outcomes. v0 ships an xG analysis off a committed sample
match: rank every shot by expected goals, roll it up per team, and stamp a one-line
verdict on who the scoreline ran ahead of. The data layer fetches Understat event
data for the big-six European leagues (with an offline fixture fallback so the demo
never touches the network), and the value layer leans on
[socceraction](https://github.com/ML-KULeuven/socceraction) (MIT, KU Leuven) for
VAEP and xT off SPADL action streams — battle-tested primitives, wrapped, not
reinvented. There's a weekly eval loop in the plan: hold out the most recent
matchday, recompute on the prior four weeks, and check whether the highest-value
actions on Saturday matched the goals and assists that actually happened. A loop,
not a one-shot demo.

It is not a betting product. No live feed, no money in the loop — just an honest
analytical surface backed by public data.

## Try it

```bash
git clone https://github.com/AthenaTheOwl/sports-prediction-os
cd sports-prediction-os
uv sync
uv run sports-os show        # ranked read of the committed sample match
```

`show` reads the committed sample match (`data/sample/match-26618.json`), ranks its
shots by xG, rolls them up per team, and prints the headline finding — offline, no
network, no secrets:

```
Arsenal 2-2 Liverpool  EPL 2024-25 - 2025-04-12 16:30:00
12 shots - 3.62 total xG

                team summary
+------------------------------------------+
| team      | shots |   xG | goals |  G-xG |
|-----------+-------+------+-------+-------|
| Arsenal   |     7 | 1.49 |     2 | +0.51 |
| Liverpool |     5 | 2.13 |     2 | -0.13 |
+------------------------------------------+
                     top shots by xG
+--------------------------------------------------------+
| # | min | player        | team      |   xG | result    |
|---+-----+---------------+-----------+------+-----------|
| 1 |  45 | Mohamed Salah | Liverpool | 0.76 | GOAL      |
| 2 |  90 | Darwin Nunez  | Liverpool | 0.55 | SavedShot |
| 3 |  78 | Kai Havertz   | Arsenal   | 0.48 | GOAL      |
| 4 |  33 | Luis Diaz     | Liverpool | 0.41 | GOAL      |
| 5 |  52 | Gabriel Jesus | Arsenal   | 0.33 | SavedShot |
+--------------------------------------------------------+

finding: Arsenal scored 2 from 1.49 xG (+0.51) - the scoreline ran ahead of the
chances created.
```

Salah's 0.76-xG strike was the best chance on the pitch, and Liverpool still didn't
win. That's the whole pitch for looking past the result.

## Live demo

`sports-os show` and the Streamlit app read the same committed sample match —
offline, no network, no secrets. The browser version renders the scoreline, three
metrics (shots / total xG / goals), a per-team summary, an xG-threshold slider over
the ranked shot list, and the same headline callout.

```bash
uv run sports-os show                       # CLI: ranked table + finding
pip install -r requirements.txt
streamlit run streamlit_app.py              # browser: same read, interactive
```

Deploy on Streamlit Community Cloud: repo `AthenaTheOwl/sports-prediction-os`,
branch `main`, main file `streamlit_app.py`.

<!-- live-url: (paste the Streamlit Cloud URL here once deployed) -->

## How it connects

- [supplier-risk-rag-agent](https://github.com/AthenaTheOwl/supplier-risk-rag-agent)
  — same Streamlit-on-Community-Cloud shape and BYOK deploy pattern; this repo
  reuses that playbook.
- [promotion-vs-pip](https://github.com/AthenaTheOwl/promotion-vs-pip) — the other
  playful surface in the portfolio, same eval-discipline spine pointed at a
  different question.

## Run it in full

```bash
uv sync
uv run sports-os --help
uv run sports-os show        # ranked read of the committed sample match
```

## Layout

```
src/sports_os/        cli, analysis, sources (understat fetcher), registry, ops
data/sample/          the committed sample match show + streamlit both read
specs/  ops/          spec 0001/0003, STATUS.md, and the run ledger
streamlit_app.py      the interactive surface over the same read
```

## Status

v0.1 partial — the ingest + analyze CLI and the Understat fetcher (with offline
fixture fallback) run today; the socceraction/StatsBomb integration, the deployed
Streamlit demo, and the first weekly eval run are the next passes. See
[ops/STATUS.md](ops/STATUS.md).

## License

MIT (code). Derived data inherits the StatsBomb terms cascade (NC-SA), documented
per dataset. See [LICENSE](LICENSE).

Portfolio: door N° 21 in the AthenaTheOwl portfolio.
