from __future__ import annotations

import json

from northstar.cli import main
from northstar.contracts import DecisionReport


def test_cli_writes_valid_decision_report(tmp_path, baseline_scenario) -> None:
    scenario_path = tmp_path / "scenario.json"
    report_path = tmp_path / "report.json"
    scenario_path.write_text(
        baseline_scenario.model_dump_json(indent=2), encoding="utf-8"
    )

    exit_code = main(
        [
            "--scenario",
            str(scenario_path),
            "--provider",
            "offline",
            "--output",
            str(report_path),
        ]
    )

    assert exit_code == 0
    report = DecisionReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    assert report.scenario_id == baseline_scenario.id


def test_cli_returns_safe_error_for_invalid_scenario(tmp_path, capsys) -> None:
    scenario_path = tmp_path / "invalid.json"
    scenario_path.write_text('{"not":"a scenario"}', encoding="utf-8")

    exit_code = main(["--scenario", str(scenario_path)])

    assert exit_code == 2
    assert "northstar:" in capsys.readouterr().err
