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


def test_partial_shot_feed_is_not_summarized_as_a_complete_match(tmp_path):
    with pytest.raises(ValueError, match="disagrees with scoreline"):
        load_report(_write(tmp_path, lambda d: d["shots"].pop(0)))


def test_cli_reports_invalid_artifact_without_a_traceback(monkeypatch, capsys):
    from sports_os import cli

    def invalid():
        raise ValueError("shot xG must be finite")

    monkeypatch.setattr(cli, "load_report", invalid)
    assert cli.main(["show"]) == 1
    assert "match artifact invalid: shot xG must be finite" in capsys.readouterr().err
