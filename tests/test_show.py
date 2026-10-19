"""Tests for the `show` verb and the offline analysis layer."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from sports_os.analysis import SAMPLE_MATCH, load_report
from sports_os.cli import main


def test_sample_artifact_is_committed() -> None:
    assert SAMPLE_MATCH.exists(), "data/sample match artifact must be committed"


def test_load_report_ranks_shots_by_xg() -> None:
    report = load_report()
    top = report.top_shots(5)
    assert len(top) == 5
    xgs = [s.xG for s in top]
    assert xgs == sorted(xgs, reverse=True)
    # Highest-xG shot in the sample is the penalty.
    assert top[0].player == "Mohamed Salah"
    assert top[0].xG == 0.76


def test_team_lines_sum_shots_and_goals() -> None:
    report = load_report()
    assert {t.team for t in report.teams} == {"Arsenal", "Liverpool"}
    assert sum(t.shots for t in report.teams) == len(report.shots)
    assert sum(t.goals for t in report.teams) == report.h_goals + report.a_goals


def test_headline_is_nonempty_string() -> None:
    report = load_report()
    line = report.headline()
    assert isinstance(line, str) and line


def test_headline_pins_leader_branch_for_sample() -> None:
    # Golden lock on the branch selector in MatchReport.headline. The sample's
    # leader (Arsenal) overperformed its xG by +0.51, which must land on the
    # "scoreline ran ahead" text — not the "finished close" tie branch. Pinning
    # the literal here means a shifted `abs(gap) < 0.05` threshold breaks the
    # test instead of silently rerouting the finding.
    report = load_report()
    line = report.headline()
    assert line.startswith("Arsenal scored 2 from 1.49 xG (+0.51)")
    assert "the scoreline ran ahead of the chances created" in line
    assert "both sides finished close" not in line


def test_show_verb_runs_offline_and_prints_ranked_result() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["show"])
    out = buf.getvalue()
    assert rc == 0
    assert "team summary" in out
    assert "top shots by xG" in out
    assert "finding:" in out
    # The ranked headline shot should appear in the output.
    assert "Mohamed Salah" in out


def _report_from(tmp_path, home: list[tuple[float, bool]], away: list[tuple[float, bool]]):
    import json

    shots = [
        {"id": f"{side}{i}", "minute": i, "player": "p", "team": team, "xG": xg,
         "result": "Goal" if goal else "SavedShot"}
        for side, team, rows in (("h", "Home", home), ("a", "Away", away))
        for i, (xg, goal) in enumerate(rows)
    ]
    doc = {"h_team": "Home", "a_team": "Away",
           "h_goals": sum(g for _, g in home), "a_goals": sum(g for _, g in away),
           "shots": shots}
    path = tmp_path / "headline.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return load_report(path)


def test_headline_names_the_real_xg_leader_when_both_sides_fall_short(tmp_path) -> None:
    # Home 1 from 1.20 (-0.20) underperformed least, but Away created more xG.
    report = _report_from(tmp_path, [(0.6, True), (0.6, False)], [(0.75, False), (0.75, False)])
    assert report.headline() == (
        "Away led the xG count yet the finishing lagged (0 goals from 1.50 xG)."
    )


def test_headline_close_wording_requires_every_side_close(tmp_path) -> None:
    # Home 0 from 0.03 is close; Away 0 from 2.50 is not.
    report = _report_from(tmp_path, [(0.03, False)], [(1.0, False), (1.0, False), (0.5, False)])
    line = report.headline()
    assert "both sides finished close" not in line
    assert line == "Away led the xG count yet the finishing lagged (0 goals from 2.50 xG)."


def test_headline_names_the_side_that_fell_short_when_xg_leader_was_close(tmp_path) -> None:
    # Home 1 from 0.98 (+0.02) led the xG count and finished close; Away fell short.
    report = _report_from(tmp_path, [(0.49, True), (0.49, False)], [(0.6, False)])
    assert report.headline() == "Away finished below its xG (0 goals from 0.60 xG)."


def test_headline_both_close_when_every_side_is_within_threshold(tmp_path) -> None:
    report = _report_from(tmp_path, [(0.49, True), (0.49, False)], [(0.03, False)])
    assert report.headline() == (
        "Home 1-0 Away: both sides finished close to their xG (1.01 total xG across 3 shots)."
    )
