from __future__ import annotations

import pytest
from pydantic import ValidationError

from northstar.contracts import Finding, ProgramScenario


def test_program_scenario_rejects_unknown_references(baseline_scenario: ProgramScenario) -> None:
    payload = baseline_scenario.model_dump()
    payload["initiatives"][0]["objective_ids"] = ["OBJ-DOES-NOT-EXIST"]

    with pytest.raises(ValidationError, match="unknown objective"):
        ProgramScenario.model_validate(payload)


def test_contracts_forbid_unknown_fields(baseline_scenario: ProgramScenario) -> None:
    payload = baseline_scenario.model_dump()
    payload["secret_override"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProgramScenario.model_validate(payload)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_finding_confidence_is_bounded(confidence: float) -> None:
    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "id": "TEST-1",
                "agent": "test",
                "category": "capacity",
                "severity": "medium",
                "title": "Capacity mismatch",
                "evidence": [{"source_id": "TEAM-1", "statement": "Demand exceeds capacity."}],
                "recommendation": "Rebalance work.",
                "confidence": confidence,
            }
        )


def test_finding_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "id": "TEST-1",
                "agent": "test",
                "category": "capacity",
                "severity": "medium",
                "title": "Capacity mismatch",
                "evidence": [],
                "recommendation": "Rebalance work.",
                "confidence": 0.8,
            }
        )
