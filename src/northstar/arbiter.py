"""Evidence-based decision option synthesis; no provider-specific code."""

from collections import defaultdict

from northstar.contracts import (
    DecisionOption,
    Finding,
    FindingCategory,
    PortfolioMetric,
    ProgramScenario,
)


def _risk_penalty(findings: list[Finding]) -> float:
    return min(0.6, sum(item.severity.score * item.confidence * 0.035 for item in findings))


def build_options(scenario: ProgramScenario, findings: list[Finding]) -> list[DecisionOption]:
    by_initiative: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        for initiative_id in finding.affected_initiative_ids:
            by_initiative[initiative_id].append(finding)

    options: list[DecisionOption] = []
    for initiative in scenario.initiatives:
        risks = by_initiative[initiative.id]
        penalty = _risk_penalty(risks)
        continue_confidence = max(0.05, initiative.delivery_confidence - penalty)
        has_high_risk = any(item.severity.score >= 3 for item in risks)
        negative_value = initiative.expected_annual_value_usd < initiative.annual_cost_usd
        unaligned = not initiative.objective_ids
        vendor_savings = (
            initiative.annual_cost_usd - initiative.alternative_vendor_cost_usd
            if initiative.alternative_vendor_cost_usd is not None else 0
        )
        preferred = (
            "stop" if negative_value and unaligned
            else "buy" if vendor_savings > initiative.annual_cost_usd * 0.3
            else "mitigate" if has_high_risk
            else "continue"
        )
        options.append(DecisionOption(
            id=f"OPT-CONT-{initiative.id}", action="continue", initiative_id=initiative.id,
            rationale="Continue the current plan while accepting all observed delivery and architecture risk.",
            estimated_cost_usd=initiative.annual_cost_usd,
            estimated_annual_value_usd=initiative.expected_annual_value_usd,
            launch_confidence=continue_confidence, risk_reduction_percent=0,
            recommended=preferred == "continue",
        ))
        if risks:
            mitigation_cost = round(initiative.annual_cost_usd * 1.15)
            options.append(DecisionOption(
                id=f"OPT-MIT-{initiative.id}", action="mitigate", initiative_id=initiative.id,
                rationale="Fund the evidence-linked remediations, rebaseline dependencies, and retain strategic scope.",
                estimated_cost_usd=mitigation_cost,
                estimated_annual_value_usd=initiative.expected_annual_value_usd,
                launch_confidence=min(0.95, initiative.delivery_confidence + 0.22),
                risk_reduction_percent=min(85, 30 + len(risks) * 12), recommended=preferred == "mitigate",
            ))
        if negative_value or unaligned:
            options.append(DecisionOption(
                id=f"OPT-STOP-{initiative.id}", action="stop", initiative_id=initiative.id,
                rationale="Stop low-value work and return constrained capacity to objective-aligned initiatives.",
                estimated_cost_usd=round(initiative.annual_cost_usd * 0.08),
                estimated_annual_value_usd=0, launch_confidence=1,
                risk_reduction_percent=95, recommended=preferred == "stop",
            ))
        if initiative.alternative_vendor_cost_usd is not None:
            options.append(DecisionOption(
                id=f"OPT-BUY-{initiative.id}", action="buy", initiative_id=initiative.id,
                rationale="Use the vendor alternative after security, integration, switching-cost, and control due diligence.",
                estimated_cost_usd=initiative.alternative_vendor_cost_usd,
                estimated_annual_value_usd=initiative.expected_annual_value_usd,
                launch_confidence=min(0.9, initiative.delivery_confidence + 0.15),
                risk_reduction_percent=35, recommended=preferred == "buy",
            ))
    return options


def build_metrics(scenario: ProgramScenario, findings: list[Finding], options: list[DecisionOption]) -> list[PortfolioMetric]:
    total_cost = sum(item.annual_cost_usd for item in scenario.initiatives)
    total_value = sum(item.expected_annual_value_usd for item in scenario.initiatives)
    total_demand = sum(item.required_capacity_points for item in scenario.initiatives)
    total_capacity = sum(item.quarterly_capacity_points for item in scenario.teams)
    recommended = [item for item in options if item.recommended]
    recommended_cost = sum(item.estimated_cost_usd for item in recommended)
    return [
        PortfolioMetric(name="Annual portfolio cost", value=total_cost, unit="USD", description="Modeled current annual run-rate."),
        PortfolioMetric(name="Annual portfolio value", value=total_value, unit="USD", description="Modeled value; not a financial forecast."),
        PortfolioMetric(name="Capacity utilization", value=round(total_demand / total_capacity * 100, 1) if total_capacity else 0, unit="percent", description="Demand divided by available quarterly team capacity."),
        PortfolioMetric(name="High and critical findings", value=sum(f.severity.score >= 3 for f in findings), unit="findings", description="Evidence-backed findings at or above the high threshold."),
        PortfolioMetric(name="Modeled cost delta", value=total_cost - recommended_cost, unit="USD", description="Current cost minus selected option costs; requires validation."),
    ]
