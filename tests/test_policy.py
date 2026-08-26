from __future__ import annotations

from northstar.contracts import (
    Evidence,
    Finding,
    FindingCategory,
    GateStatus,
    PolicyConfig,
    Severity,
)
from northstar.policy import evaluate_gate


def _finding(
    *,
    finding_id: str,
    category: FindingCategory,
    severity: Severity,
    confidence: float = 0.9,
) -> Finding:
    return Finding(
        id=finding_id,
        agent="test",
        category=category,
        severity=severity,
        title="Policy test finding",
        evidence=[Evidence(source_id="TEST-SOURCE", statement="Synthetic policy evidence.")],
        recommendation="Send the decision to the configured owner.",
        confidence=confidence,
    )


def test_gate_allows_low_severity_finding() -> None:
    decision = evaluate_gate(
        [
            _finding(
                finding_id="TEST-LOW",
                category=FindingCategory.CAPACITY,
                severity=Severity.LOW,
            )
        ],
        PolicyConfig(),
    )

    assert decision.status is GateStatus.ALLOW
    assert not decision.blocking_finding_ids
    assert not decision.review_finding_ids


def test_gate_routes_high_severity_to_human_review() -> None:
    decision = evaluate_gate(
        [
            _finding(
                finding_id="TEST-HIGH",
                category=FindingCategory.DEPENDENCY,
                severity=Severity.HIGH,
            )
        ],
        PolicyConfig(),
    )

    assert decision.status is GateStatus.HUMAN_REVIEW
    assert decision.review_finding_ids == ["TEST-HIGH"]


def test_gate_blocks_critical_privacy_finding() -> None:
    decision = evaluate_gate(
        [
            _finding(
                finding_id="TEST-PRIVACY",
                category=FindingCategory.PRIVACY,
                severity=Severity.CRITICAL,
            )
        ],
        PolicyConfig(),
    )

    assert decision.status is GateStatus.BLOCK
    assert decision.blocking_finding_ids == ["TEST-PRIVACY"]


def test_gate_does_not_escalate_below_minimum_confidence() -> None:
    decision = evaluate_gate(
        [
            _finding(
                finding_id="TEST-UNCERTAIN",
                category=FindingCategory.PRIVACY,
                severity=Severity.CRITICAL,
                confidence=0.2,
            )
        ],
        PolicyConfig(minimum_confidence=0.65),
    )

    assert decision.status is GateStatus.ALLOW


def test_breaking_api_can_require_review_below_severity_threshold() -> None:
    decision = evaluate_gate(
        [
            _finding(
                finding_id="TEST-API",
                category=FindingCategory.BREAKING_API,
                severity=Severity.MEDIUM,
            )
        ],
        PolicyConfig(review_at_or_above=Severity.CRITICAL),
    )

    assert decision.status is GateStatus.HUMAN_REVIEW
    assert decision.review_finding_ids == ["TEST-API"]
