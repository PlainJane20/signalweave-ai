from __future__ import annotations

from northstar import DecisionOrchestrator
from northstar.contracts import GateStatus
from northstar.providers import AnalysisProvider, OfflineProvider, ProviderError


class FailingProvider(AnalysisProvider):
    mode = "failing-test-provider"

    def assess(self, *, system_prompt, scenario, fallback):
        raise ProviderError("synthetic provider outage")


def _metric(report, name: str) -> float:
    return next(item.value for item in report.metrics if item.name == name)


def test_full_offline_orchestration_is_evidence_linked_and_gated(
    baseline_scenario,
) -> None:
    report = DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)

    assert report.scenario_id == baseline_scenario.id
    assert report.report_id.startswith("RPT-")
    assert len(report.assessments) == 6
    assert all(finding.evidence for item in report.assessments for finding in item.findings)
    assert report.gate.status is GateStatus.HUMAN_REVIEW
    assert report.options
    assert report.recommended_option_ids
    assert "accountable" in report.human_accountability_note.lower()


def test_same_inputs_produce_stable_report_identity(baseline_scenario) -> None:
    orchestrator = DecisionOrchestrator(provider=OfflineProvider())

    first = orchestrator.run(baseline_scenario)
    second = orchestrator.run(baseline_scenario)

    assert first.report_id == second.report_id
    assert first.model_dump(exclude={"generated_at"}) == second.model_dump(
        exclude={"generated_at"}
    )


def test_provider_outage_degrades_to_explicit_offline_assessment(
    baseline_scenario,
) -> None:
    report = DecisionOrchestrator(provider=FailingProvider()).run(baseline_scenario)

    assert len(report.assessments) == 6
    assert all(item.analysis_mode == "offline" for item in report.assessments)
    assert all("fallback used" in item.summary for item in report.assessments)


def test_capacity_shock_changes_portfolio_metric(baseline_scenario) -> None:
    orchestrator = DecisionOrchestrator(provider=OfflineProvider())
    baseline = orchestrator.run(baseline_scenario)
    shocked_teams = [
        team.model_copy(update={"quarterly_capacity_points": 60})
        if team.id == "TEAM-PLATFORM"
        else team
        for team in baseline_scenario.teams
    ]
    shocked_scenario = baseline_scenario.model_copy(update={"teams": shocked_teams})
    shocked = orchestrator.run(shocked_scenario)

    assert _metric(shocked, "Capacity utilization") > _metric(
        baseline, "Capacity utilization"
    )
    assert _metric(shocked, "High and critical findings") >= _metric(
        baseline, "High and critical findings"
    )


def test_critical_phi_control_gap_blocks_report(baseline_scenario) -> None:
    unsafe = baseline_scenario.model_copy(
        update={
            "services": [
                baseline_scenario.services[0].model_copy(
                    update={"contains_phi": True, "encryption_at_rest": False}
                )
            ]
        }
    )

    report = DecisionOrchestrator(provider=OfflineProvider()).run(unsafe)

    assert report.gate.status is GateStatus.BLOCK
    assert report.gate.blocking_finding_ids
