"""Read-only analysis over a committed sample match artifact.

The v0 value layer is xG-based and offline: it loads the committed sample
match (``data/sample/match-26618.json``), ranks shots by xG, and rolls the
shots up per team and per player. No network, no socceraction dependency —
this is the readable slice that the ``show`` verb and the Streamlit app both
render. The socceraction VAEP/xT layer is a later pass; the shape here is
the contract those richer numbers will slot into.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_MATCH = REPO_ROOT / "data" / "sample" / "match-26618.json"

# Results that put the ball in the net (for actual-goal accounting).
_GOAL_RESULTS = {"Goal"}


@dataclass(frozen=True)
class Shot:
    id: str
    minute: int
    player: str
    team: str
    xG: float
    result: str
    situation: str | None
    body_part: str | None

    @property
    def is_goal(self) -> bool:
        return self.result in _GOAL_RESULTS


@dataclass(frozen=True)
class TeamLine:
    team: str
    shots: int
    xG: float
    goals: int

    @property
    def xG_diff(self) -> float:
        """Actual goals minus expected goals. Positive = overperformed."""
        return self.goals - self.xG


@dataclass(frozen=True)
class MatchReport:
    match_id: str
    league: str
    season: str
    h_team: str
    a_team: str
    h_goals: int
    a_goals: int
    datetime: str
    shots: list[Shot]
    teams: list[TeamLine]

    @property
    def scoreline(self) -> str:
        return f"{self.h_team} {self.h_goals}-{self.a_goals} {self.a_team}"

    @property
    def total_xG(self) -> float:
        return round(sum(s.xG for s in self.shots), 2)

    def top_shots(self, n: int = 5) -> list[Shot]:
        """Shots ranked by xG, highest first."""
        return sorted(self.shots, key=lambda s: s.xG, reverse=True)[:n]

    def headline(self) -> str:
        """One-line finding: which side most out-shot its own xG.

        We compare each team's actual goals against the xG it generated.
        The bigger the gap, the more the result leaned on finishing (or
        keeping) rather than chance creation.
        """
        if not self.teams:
            return "no shot data in artifact."
        leader = max(self.teams, key=lambda t: t.xG_diff)
        gap = leader.xG_diff
        if abs(gap) < 0.05:
            return (
                f"{self.scoreline}: both sides finished close to their xG "
                f"({self.total_xG:.2f} total xG across {len(self.shots)} shots)."
            )
        if gap > 0:
            return (
                f"{leader.team} scored {leader.goals} from {leader.xG:.2f} xG "
                f"(+{gap:.2f}) - the scoreline ran ahead of the chances created."
            )
        return (
            f"{leader.team} led the xG count yet the finishing lagged "
            f"({leader.goals} goals from {leader.xG:.2f} xG)."
        )


def load_report(path: Path | str = SAMPLE_MATCH) -> MatchReport:
    """Load the committed sample match into a ranked MatchReport. Offline."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    shots = [
        Shot(
            id=str(row.get("id", "")),
            minute=int(row.get("minute", 0)),
            player=str(row.get("player", "")),
            team=str(row.get("team", "")),
            xG=float(row.get("xG", 0.0)),
            result=str(row.get("result", "")),
            situation=row.get("situation"),
            body_part=row.get("body_part"),
        )
        for row in data.get("shots", [])
    ]

    teams: list[TeamLine] = []
    for team in (data["h_team"], data["a_team"]):
        team_shots = [s for s in shots if s.team == team]
        teams.append(
            TeamLine(
                team=team,
                shots=len(team_shots),
                xG=round(sum(s.xG for s in team_shots), 2),
                goals=sum(1 for s in team_shots if s.is_goal),
            )
        )

    return MatchReport(
        match_id=str(data.get("match_id", "")),
        league=str(data.get("league", "")),
        season=str(data.get("season", "")),
        h_team=str(data["h_team"]),
        a_team=str(data["a_team"]),
        h_goals=int(data.get("h_goals", 0)),
        a_goals=int(data.get("a_goals", 0)),
        datetime=str(data.get("datetime", "")),
        shots=shots,
        teams=teams,
    )
