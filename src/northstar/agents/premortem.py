"""Failure-chain and leading-indicator specialist."""

from northstar.agents.base import SpecialistAgent
from northstar.contracts import Evidence, Finding, FindingCategory, ProgramScenario, Severity


class PremortemAgent(SpecialistAgent):
    name = "premortem"
    system_prompt = (
        "Act as a program pre-mortem facilitator. Convert supplied dependency and confidence signals "
        "into plausible, evidence-linked failure chains and leading indicators. Return strict JSON."
    )

    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        findings: list[Finding] = []
        by_id = {item.id: item for item in scenario.initiatives}
        for initiative in scenario.initiatives:
            if initiative.delivery_confidence < 0.65 and initiative.dependency_ids:
                dependencies = [by_id[item].name for item in initiative.dependency_ids]
                findings.append(Finding(
                    id=f"PRE-{initiative.id}", agent=self.name,
                    category=FindingCategory.PREMORTEM,
                    severity=Severity.HIGH if initiative.delivery_confidence < 0.5 else Severity.MEDIUM,
                    title="Low-confidence dependency chain threatens the target milestone",
                    affected_initiative_ids=[initiative.id, *initiative.dependency_ids],
                    evidence=[Evidence(source_id=initiative.id, statement=(
                        f"Delivery confidence is {initiative.delivery_confidence:.0%}; upstream dependency chain: "
                        f"{' → '.join(dependencies)} → {initiative.name}."
                    ), metric_value=initiative.delivery_confidence * 100, metric_unit="percent confidence")],
                    recommendation=(
                        "Track weekly dependency burn-up and contract readiness; trigger replan when either "
                        "misses two consecutive checkpoints."
                    ), confidence=0.86, requires_human_decision=True,
                ))
        return findings
