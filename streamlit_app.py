"""Streamlit surface for sports-prediction-os.

Reads the committed sample match artifact (data/sample/match-26618.json)
directly — paths are relative to this file, no network, no secrets. Mirrors
the `sports-os show` verb: a ranked shot table by xG, per-team summary, and
a one-line headline finding, with one interactive control (xG threshold).

Below that committed view, an interactive section drives the real engine:
the user edits a match (or pastes their own shots) and we call
`sports_os.analysis.load_report`, the same value layer the `show` verb uses,
recomputing the ranked report, per-team xG rollups, and the headline finding.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
SAMPLE_MATCH = HERE / "data" / "sample" / "match-26618.json"

GOAL_RESULTS = {"Goal"}

st.set_page_config(page_title="sports-prediction-os", layout="centered")


def load_match() -> dict:
    return json.loads(SAMPLE_MATCH.read_text(encoding="utf-8"))


st.title("sports-prediction-os")
st.caption(
    "offline read of a committed sample match: shots ranked by xG, "
    "per-team summary, and the headline finding. not a betting product."
)

if not SAMPLE_MATCH.exists():
    st.warning(
        "no sample match artifact found at data/sample/match-26618.json. "
        "commit the sample match and reload."
    )
    st.stop()

match = load_match()
shots = pd.DataFrame(match.get("shots", []))

if shots.empty:
    st.warning("the sample match artifact has no shots. nothing to rank.")
    st.stop()

shots["is_goal"] = shots["result"].isin(GOAL_RESULTS)

h_team = match["h_team"]
a_team = match["a_team"]
scoreline = f"{h_team} {match['h_goals']}-{match['a_goals']} {a_team}"
total_xg = round(float(shots["xG"].sum()), 2)
total_goals = int(shots["is_goal"].sum())

st.subheader(scoreline)
st.caption(f"{match.get('league', '')} {match.get('season', '')} - {match.get('datetime', '')}")

c1, c2, c3 = st.columns(3)
c1.metric("shots", len(shots))
c2.metric("total xG", f"{total_xg:.2f}")
c3.metric("goals", total_goals)

# Headline finding: which side most out-scored its own xG.
team_rows = []
for team in (h_team, a_team):
    sub = shots[shots["team"] == team]
    team_xg = round(float(sub["xG"].sum()), 2)
    team_goals = int(sub["is_goal"].sum())
    team_rows.append(
        {
            "team": team,
            "shots": int(len(sub)),
            "xG": team_xg,
            "goals": team_goals,
            "G-xG": round(team_goals - team_xg, 2),
        }
    )
team_df = pd.DataFrame(team_rows)

leader = max(team_rows, key=lambda r: r["G-xG"])
gap = leader["G-xG"]
if abs(gap) < 0.05:
    headline = (
        f"both sides finished close to their xG "
        f"({total_xg:.2f} total xG across {len(shots)} shots)."
    )
elif gap > 0:
    headline = (
        f"{leader['team']} scored {leader['goals']} from {leader['xG']:.2f} xG "
        f"(+{gap:.2f}) - the scoreline ran ahead of the chances created."
    )
else:
    headline = (
        f"{leader['team']} led the xG count yet the finishing lagged "
        f"({leader['goals']} goals from {leader['xG']:.2f} xG)."
    )
st.info(headline)

st.markdown("### team summary")
st.dataframe(team_df, hide_index=True, use_container_width=True)

st.markdown("### shots ranked by xG")
threshold = st.slider(
    "minimum xG to show",
    min_value=0.0,
    max_value=float(round(shots["xG"].max(), 2)),
    value=0.0,
    step=0.05,
    help="filter the ranked shot list by expected-goal value.",
)

ranked = (
    shots[shots["xG"] >= threshold]
    .sort_values("xG", ascending=False)
    .loc[:, ["minute", "player", "team", "xG", "result", "situation", "body_part"]]
    .reset_index(drop=True)
)
st.dataframe(ranked, hide_index=True, use_container_width=True)
st.caption(f"{len(ranked)} of {len(shots)} shots at or above {threshold:.2f} xG.")

# ---------------------------------------------------------------------------
# Run the real analysis engine live. Everything above reads the committed
# artifact straight off disk. Below, the user edits a match (or pastes their
# own shots) and we call sports_os.analysis.load_report — the SAME function
# the `sports-os show` verb and the table above ultimately model. It builds the
# ranked MatchReport, the per-team xG rollups, and the headline() finding. Edit
# the shots, watch the scoreline, the G-xG, and the finding recompute.
# ---------------------------------------------------------------------------
st.divider()
st.subheader("analyze your own match")
st.caption(
    "drive the actual engine — `sports_os.analysis.load_report` — on a match you "
    "edit. change a shot's xG or result, add a shot, flip the score, and the "
    "ranked report + the one-line finding recompute live. it's the real value "
    "layer, not the lookup above."
)

try:
    import sys
    import tempfile

    sys.path.insert(0, str(HERE / "src"))
    from sports_os.analysis import load_report

    default_doc = {
        "match_id": match.get("match_id", ""),
        "league": match.get("league", ""),
        "season": match.get("season", ""),
        "datetime": match.get("datetime", ""),
        "h_team": h_team,
        "a_team": a_team,
        "h_goals": match.get("h_goals", 0),
        "a_goals": match.get("a_goals", 0),
        "shots": match.get("shots", []),
    }

    st.caption(
        "a shot needs at least `team`, `xG`, and `result`. set `result` to "
        '`"Goal"` to count it as a goal. teams must be `h_team` / `a_team` above.'
    )
    raw = st.text_area(
        "match json (edit me)",
        value=json.dumps(default_doc, indent=2),
        height=320,
        help="this exact text is parsed and fed to the real load_report engine.",
    )

    run = st.button("run load_report", type="primary")
    if run:
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as exc:
            st.error(f"that isn't valid json: {exc}")
        else:
            # load_report takes a path, so we hand the engine a real temp file.
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tmp:
                json.dump(doc, tmp)
                tmp_path = tmp.name
            try:
                report = load_report(tmp_path)
            except (KeyError, ValueError, TypeError) as exc:
                st.error(
                    f"the engine rejected this match ({type(exc).__name__}: {exc}). "
                    "check that h_team / a_team and every shot's fields are present."
                )
            else:
                st.markdown(f"#### {report.scoreline}")
                st.caption(
                    f"{report.league} {report.season} - {report.datetime} - "
                    f"{len(report.shots)} shots, {report.total_xG:.2f} total xG"
                )

                t1, t2, t3 = st.columns(3)
                t1.metric("shots", len(report.shots))
                t2.metric("total xG", f"{report.total_xG:.2f}")
                t3.metric(
                    "goals", sum(t.goals for t in report.teams)
                )

                live_team_df = pd.DataFrame(
                    [
                        {
                            "team": t.team,
                            "shots": t.shots,
                            "xG": round(t.xG, 2),
                            "goals": t.goals,
                            "G-xG": round(t.xG_diff, 2),
                        }
                        for t in report.teams
                    ]
                )
                st.markdown("##### team summary (recomputed)")
                st.dataframe(live_team_df, hide_index=True, use_container_width=True)

                st.markdown("##### top shots by xG (recomputed)")
                top_df = pd.DataFrame(
                    [
                        {
                            "minute": s.minute,
                            "player": s.player,
                            "team": s.team,
                            "xG": s.xG,
                            "result": s.result,
                            "goal": s.is_goal,
                        }
                        for s in report.top_shots(10)
                    ]
                )
                st.dataframe(top_df, hide_index=True, use_container_width=True)

                st.success(f"**finding:** {report.headline()}")
                st.caption(
                    "this finding is `report.headline()` straight off the engine — "
                    "edit a shot above and re-run to watch which side's finishing "
                    "ran ahead of (or behind) its xG change."
                )
    else:
        st.caption("edit the json above, then press **run load_report** to recompute.")
except Exception as exc:  # pragma: no cover - defensive for cloud import differences
    st.info(
        f"interactive analysis needs the package importable ({exc}). "
        "the committed read above still renders."
    )
