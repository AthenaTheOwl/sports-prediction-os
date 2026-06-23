"""Streamlit surface for sports-prediction-os.

Reads the committed sample match artifact (data/sample/match-26618.json)
directly — paths are relative to this file, no network, no secrets. Mirrors
the `sports-os show` verb: a ranked shot table by xG, per-team summary, and
a one-line headline finding, with one interactive control (xG threshold).
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
