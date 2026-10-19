import json

import pytest

from sports_os.analysis import SAMPLE_MATCH, load_report


def _write(tmp_path, change):
    data = json.loads(SAMPLE_MATCH.read_text(encoding="utf-8"))
    change(data)
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1, True, None, 10 ** 400])
def test_invalid_xg_cannot_contaminate_team_totals(tmp_path, value):
    with pytest.raises(ValueError, match="xG"):
        load_report(_write(tmp_path, lambda d: d["shots"][0].update(xG=value)))


def test_unknown_team_is_rejected_instead_of_disappearing_from_rollup(tmp_path):
    with pytest.raises(ValueError, match="team"):
        load_report(_write(tmp_path, lambda d: d["shots"][0].update(team="Another club")))


@pytest.mark.parametrize("value", [-1, 1.5, True, float("nan"), 10 ** 400])
def test_scoreline_requires_nonnegative_integer_goals(tmp_path, value):
    with pytest.raises(ValueError, match="h_goals"):
        load_report(_write(tmp_path, lambda d: d.update(h_goals=value)))


def test_missing_goal_shot_is_rejected(tmp_path):
    # Sample shot s01 is a Goal, so dropping it breaks the score check. A feed
    # missing only non-goal shots still loads; see docs/match-integrity-and-evaluation.md.
    with pytest.raises(ValueError, match="disagrees with scoreline"):
        load_report(_write(tmp_path, lambda d: d["shots"].pop(0)))


def test_top_level_must_be_an_object(tmp_path):
    path = tmp_path / "list.json"
    path.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(ValueError, match="match artifact must be an object"):
        load_report(path)


def test_home_and_away_must_be_distinct(tmp_path):
    with pytest.raises(ValueError, match="distinct"):
        load_report(_write(tmp_path, lambda d: d.update(a_team=d["h_team"])))


def test_shots_must_be_a_list(tmp_path):
    with pytest.raises(ValueError, match="shots must be a list"):
        load_report(_write(tmp_path, lambda d: d.update(shots={})))


def test_each_shot_must_be_an_object(tmp_path):
    with pytest.raises(ValueError, match="shot 0 must be an object"):
        load_report(_write(tmp_path, lambda d: d["shots"].__setitem__(0, [1])))


@pytest.mark.parametrize("value", [-1, 1.5, "x"])
def test_shot_minute_requires_nonnegative_integer(tmp_path, value):
    with pytest.raises(ValueError, match="shot 0 minute"):
        load_report(_write(tmp_path, lambda d: d["shots"][0].update(minute=value)))


def test_away_goals_require_nonnegative_integer(tmp_path):
    with pytest.raises(ValueError, match="a_goals"):
        load_report(_write(tmp_path, lambda d: d.update(a_goals=-1)))


def test_cli_reports_invalid_artifact_without_a_traceback(monkeypatch, capsys):
    from sports_os import cli

    def invalid():
        raise ValueError("shot xG must be finite")

    monkeypatch.setattr(cli, "load_report", invalid)
    assert cli.main(["show"]) == 1
    assert "match artifact invalid: shot xG must be finite" in capsys.readouterr().err
