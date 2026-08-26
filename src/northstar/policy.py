"""Deterministic policy gates applied before recommendations are surfaced."""

from northstar.contracts import (
    Finding,
    FindingCategory,
    GateDecision,
    GateStatus,
    PolicyConfig,
)


def evaluate_gate(findings: list[Finding], policy: PolicyConfig) -> GateDecision:
    blocking: list[str] = []
    review: list[str] = []
    reasons: list[str] = []
    for finding in findings:
        if finding.confidence < policy.minimum_confidence:
            continue
        if (
            finding.category in policy.blocked_categories
            and finding.severity.score >= policy.block_at_or_above.score
        ):
            blocking.append(finding.id)
        elif finding.severity.score >= policy.review_at_or_above.score:
            review.append(finding.id)
        elif policy.require_human_for_breaking_api and finding.category is FindingCategory.BREAKING_API:
            review.append(finding.id)

    if blocking:
        reasons.append("One or more high-confidence prohibited risks reached the blocking threshold.")
        status = GateStatus.BLOCK
    elif review:
        reasons.append("Consequential findings require an accountable human decision before execution.")
        status = GateStatus.HUMAN_REVIEW
    else:
        reasons.append("No configured blocking or mandatory-review threshold was reached.")
        status = GateStatus.ALLOW
    return GateDecision(
        status=status,
        reasons=reasons,
        blocking_finding_ids=sorted(blocking),
        review_finding_ids=sorted(set(review)),
    )
