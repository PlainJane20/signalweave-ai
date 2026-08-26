from __future__ import annotations

import pytest

from northstar.agents import (
    ArchitectureAgent,
    EconomicsAgent,
    ExecutionAgent,
    GovernanceAgent,
    PremortemAgent,
    StrategyAgent,
)
from northstar.contracts import FindingCategory
from northstar.providers import OfflineProvider


def _categories(agent, scenario) -> set[FindingCategory]:
    return {finding.category for finding in agent.run(scenario).findings}


def test_strategy_agent_finds_unaligned_work(baseline_scenario) -> None:
    assessment = StrategyAgent(OfflineProvider()).run(baseline_scenario)

    assert FindingCategory.STRATEGY in {item.category for item in assessment.findings}
    assert any("INIT-ORPHAN" in item.affected_initiative_ids for item in assessment.findings)
    assert all(item.evidence for item in assessment.findings)


def test_architecture_agent_finds_spof_and_breaking_api(baseline_scenario) -> None:
    categories = _categories(ArchitectureAgent(OfflineProvider()), baseline_scenario)

    assert FindingCategory.SPOF in categories
    assert FindingCategory.BREAKING_API in categories


def test_execution_agent_finds_capacity_ownership_and_sequence_risk(
    baseline_scenario,
) -> None:
    categories = _categories(ExecutionAgent(OfflineProvider()), baseline_scenario)

    assert {
        FindingCategory.CAPACITY,
        FindingCategory.OWNERSHIP,
        FindingCategory.DEPENDENCY,
    } <= categories


def test_governance_agent_blocks_unsafe_phi_controls(baseline_scenario) -> None:
    unsafe = baseline_scenario.model_copy(
        update={
            "services": [
                baseline_scenario.services[0].model_copy(
                    update={
                        "contains_phi": True,
                        "encryption_at_rest": False,
                        "audit_logging": False,
                    }
                )
            ]
        }
    )
    assessment = GovernanceAgent(OfflineProvider()).run(unsafe)

    assert {FindingCategory.PRIVACY, FindingCategory.COMPLIANCE} == {
        item.category for item in assessment.findings
    }
    assert all(item.requires_human_decision for item in assessment.findings)


def test_economics_agent_finds_negative_value(baseline_scenario) -> None:
    assessment = EconomicsAgent(OfflineProvider()).run(baseline_scenario)

    assert any(
        finding.category is FindingCategory.ECONOMICS
        and "INIT-ORPHAN" in finding.affected_initiative_ids
        for finding in assessment.findings
    )


def test_premortem_agent_emits_failure_chain_for_low_confidence_dependency(
    baseline_scenario,
) -> None:
    initiatives = [
        initiative.model_copy(update={"delivery_confidence": 0.45})
        if initiative.id == "INIT-MOBILE"
        else initiative
        for initiative in baseline_scenario.initiatives
    ]
    scenario = baseline_scenario.model_copy(update={"initiatives": initiatives})
    assessment = PremortemAgent(OfflineProvider()).run(scenario)

    assert any(
        finding.category is FindingCategory.PREMORTEM
        and "INIT-IDENTITY" in finding.affected_initiative_ids
        for finding in assessment.findings
    )


@pytest.mark.parametrize(
    "agent_type",
    [
        StrategyAgent,
        ArchitectureAgent,
        ExecutionAgent,
        GovernanceAgent,
        EconomicsAgent,
        PremortemAgent,
    ],
)
def test_every_agent_returns_a_valid_offline_assessment(agent_type, baseline_scenario) -> None:
    result = agent_type(OfflineProvider()).run(baseline_scenario)

    assert result.agent
    assert result.summary
    assert result.analysis_mode == "offline"
