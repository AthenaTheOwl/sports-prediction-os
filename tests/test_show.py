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
