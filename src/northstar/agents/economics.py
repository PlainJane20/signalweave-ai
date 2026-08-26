"""Opportunity-cost and build-versus-buy specialist."""

from northstar.agents.base import SpecialistAgent
from northstar.contracts import Evidence, Finding, FindingCategory, ProgramScenario, Severity


class EconomicsAgent(SpecialistAgent):
    name = "economics"
    system_prompt = (
        "Act as a portfolio economics specialist. Compare value, cost, opportunity cost, and available "
        "vendor alternatives. Do not imply financial certainty. Return strict AgentAssessment JSON."
    )

    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        findings: list[Finding] = []
        for initiative in scenario.initiatives:
            net_value = initiative.expected_annual_value_usd - initiative.annual_cost_usd
            if net_value < 0:
                findings.append(Finding(
                    id=f"ECON-NEG-{initiative.id}", agent=self.name,
                    category=FindingCategory.ECONOMICS, severity=(
                        Severity.HIGH if -net_value > 250_000 else Severity.MEDIUM
                    ), title="Estimated annual cost exceeds modeled annual value",
                    affected_initiative_ids=[initiative.id],
                    evidence=[Evidence(source_id=initiative.id, statement=(
                        f"Modeled annual value is ${initiative.expected_annual_value_usd:,} versus "
                        f"${initiative.annual_cost_usd:,} annual cost."
                    ), metric_value=net_value, metric_unit="USD net annual value")],
                    recommendation="Validate assumptions and compare pause, stop, and redirect alternatives.",
                    confidence=0.88, requires_human_decision=True,
                ))
            vendor = initiative.alternative_vendor_cost_usd
            if vendor is not None and vendor < initiative.annual_cost_usd * 0.7:
                savings = initiative.annual_cost_usd - vendor
                findings.append(Finding(
                    id=f"ECON-BUY-{initiative.id}", agent=self.name,
                    category=FindingCategory.ECONOMICS, severity=Severity.MEDIUM,
                    title="Build-versus-buy decision has a material cost gap",
                    affected_initiative_ids=[initiative.id],
                    evidence=[Evidence(source_id=initiative.id, statement=(
                        f"Vendor estimate is ${vendor:,}, ${savings:,} below modeled internal annual cost."
                    ), metric_value=savings, metric_unit="USD potential annual savings")],
                    recommendation="Run due diligence on strategic control, switching cost, security, and total vendor cost.",
                    confidence=0.82, requires_human_decision=True,
                ))
        return findings
