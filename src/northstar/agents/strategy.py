"""Strategy-to-execution alignment specialist."""

from northstar.agents.base import SpecialistAgent
from northstar.contracts import Evidence, Finding, FindingCategory, ProgramScenario, Severity


class StrategyAgent(SpecialistAgent):
    name = "strategy"
    system_prompt = (
        "Act as a portfolio strategy specialist. Validate evidence, flag work not aligned to an "
        "objective, and return only the AgentAssessment schema. Do not invent source facts."
    )

    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        findings: list[Finding] = []
        for initiative in scenario.initiatives:
            if not initiative.objective_ids:
                findings.append(
                    Finding(
                        id=f"STRAT-{initiative.id}", agent=self.name,
                        category=FindingCategory.STRATEGY, severity=Severity.HIGH,
                        title="Initiative has no traceable strategic objective",
                        affected_initiative_ids=[initiative.id],
                        evidence=[Evidence(source_id=initiative.id, statement=(
                            f"{initiative.name} has zero objective links while consuming "
                            f"{initiative.required_capacity_points} capacity points."
                        ), metric_value=initiative.required_capacity_points, metric_unit="points")],
                        recommendation="Pause funding until an objective, outcome metric, and accountable owner are recorded.",
                        confidence=0.99, requires_human_decision=True,
                    )
                )
            elif initiative.strategic_value < 40:
                findings.append(
                    Finding(
                        id=f"STRAT-LOW-{initiative.id}", agent=self.name,
                        category=FindingCategory.STRATEGY, severity=Severity.MEDIUM,
                        title="Low strategic value relative to portfolio demand",
                        affected_initiative_ids=[initiative.id],
                        evidence=[Evidence(source_id=initiative.id, statement=(
                            f"Recorded strategic value is {initiative.strategic_value:.0f} out of 100."
                        ), metric_value=initiative.strategic_value, metric_unit="score")],
                        recommendation="Compare redirect and stop options at the next portfolio review.",
                        confidence=0.9, requires_human_decision=True,
                    )
                )
        return findings
