"""Capacity, ownership, sequencing, and critical-path specialist."""

from collections import defaultdict

from northstar.agents.base import SpecialistAgent
from northstar.contracts import Evidence, Finding, FindingCategory, ProgramScenario, Severity


class ExecutionAgent(SpecialistAgent):
    name = "execution"
    system_prompt = (
        "Act as a technical program execution specialist. Find ownership, capacity, and dependency "
        "failures. Use only supplied data and return a strict AgentAssessment."
    )

    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        findings: list[Finding] = []
        by_id = {item.id: item for item in scenario.initiatives}
        team_load: dict[str, int] = defaultdict(int)
        for initiative in scenario.initiatives:
            if initiative.owner_team_id:
                team_load[initiative.owner_team_id] += initiative.required_capacity_points
            else:
                findings.append(Finding(
                    id=f"EXEC-OWNER-{initiative.id}", agent=self.name,
                    category=FindingCategory.OWNERSHIP, severity=Severity.HIGH,
                    title="Critical work lacks an accountable team",
                    affected_initiative_ids=[initiative.id],
                    evidence=[Evidence(source_id=initiative.id, statement="Initiative owner_team_id is not assigned.")],
                    recommendation="Assign one accountable team before work enters execution.",
                    confidence=1.0, requires_human_decision=True,
                ))
            for dependency_id in initiative.dependency_ids:
                dependency = by_id[dependency_id]
                if dependency.target_quarter >= initiative.target_quarter:
                    findings.append(Finding(
                        id=f"EXEC-SEQ-{initiative.id}-{dependency_id}", agent=self.name,
                        category=FindingCategory.DEPENDENCY, severity=Severity.HIGH,
                        title="Dependency is scheduled too late for its consumer",
                        affected_initiative_ids=[initiative.id, dependency_id],
                        evidence=[Evidence(source_id=initiative.id, statement=(
                            f"{initiative.id} targets Q{initiative.target_quarter}, but dependency "
                            f"{dependency_id} targets Q{dependency.target_quarter}."
                        ), metric_value=dependency.target_quarter - initiative.target_quarter + 1, metric_unit="quarters at risk")],
                        recommendation="Move the dependency earlier, add a compatibility layer, or rebaseline the consumer milestone.",
                        confidence=0.99, requires_human_decision=True,
                    ))
        for team in scenario.teams:
            load = team_load[team.id]
            if load > team.quarterly_capacity_points:
                overage = load - team.quarterly_capacity_points
                affected = [i.id for i in scenario.initiatives if i.owner_team_id == team.id]
                findings.append(Finding(
                    id=f"EXEC-CAP-{team.id}", agent=self.name,
                    category=FindingCategory.CAPACITY, severity=(
                        Severity.CRITICAL if load > team.quarterly_capacity_points * 1.5 else Severity.HIGH
                    ), title=f"{team.name} is overcommitted",
                    affected_initiative_ids=affected,
                    evidence=[Evidence(source_id=team.id, statement=(
                        f"Demand is {load} points against {team.quarterly_capacity_points} points of capacity."
                    ), metric_value=overage, metric_unit="points over capacity")],
                    recommendation="Stop or redirect lower-value work until demand fits demonstrated capacity.",
                    confidence=0.99, requires_human_decision=True,
                ))
        return findings
