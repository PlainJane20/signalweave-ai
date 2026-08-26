"""Architecture, compatibility, and resilience specialist."""

from northstar.agents.base import SpecialistAgent
from northstar.contracts import Evidence, Finding, FindingCategory, ProgramScenario, Severity


class ArchitectureAgent(SpecialistAgent):
    name = "architecture"
    system_prompt = (
        "Act as a staff architecture reviewer. Assess cross-domain breaking APIs and service "
        "single points of failure. Cite scenario IDs and return only AgentAssessment JSON."
    )

    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        findings: list[Finding] = []
        for service in scenario.services:
            if service.replicas < 2:
                severity = Severity.CRITICAL if service.replicas == 0 else Severity.HIGH
                affected = [i.id for i in scenario.initiatives if service.id in i.systems]
                findings.append(Finding(
                    id=f"ARCH-SPOF-{service.id}", agent=self.name,
                    category=FindingCategory.SPOF, severity=severity,
                    title=f"{service.name} is a deployment single point of failure",
                    affected_initiative_ids=affected,
                    evidence=[Evidence(source_id=service.id, statement=(
                        f"Service has {service.replicas} replica(s) and a "
                        f"{service.recovery_time_minutes}-minute recovery objective."
                    ), metric_value=service.replicas, metric_unit="replicas")],
                    recommendation="Add multi-zone redundancy, automated failover, and a tested recovery runbook.",
                    confidence=0.98, requires_human_decision=severity is Severity.CRITICAL,
                ))
        for change in scenario.api_changes:
            if not change.backward_compatible:
                severity = Severity.HIGH if change.consumer_team_ids else Severity.MEDIUM
                affected = [
                    initiative.id for initiative in scenario.initiatives
                    if initiative.owner_team_id in change.consumer_team_ids
                    or change.service_id in initiative.systems
                ]
                findings.append(Finding(
                    id=f"ARCH-BREAK-{change.id}", agent=self.name,
                    category=FindingCategory.BREAKING_API, severity=severity,
                    title="Breaking API change crosses team boundaries",
                    affected_initiative_ids=affected,
                    evidence=[Evidence(source_id=change.id, statement=(
                        f"Non-compatible change affects {len(change.consumer_team_ids)} consumer team(s) "
                        f"with a {change.compatibility_window_days}-day compatibility window."
                    ), metric_value=len(change.consumer_team_ids), metric_unit="teams")],
                    recommendation="Version the contract, publish a migration plan, and preserve compatibility through the agreed window.",
                    confidence=0.97, requires_human_decision=True,
                ))
        return findings
