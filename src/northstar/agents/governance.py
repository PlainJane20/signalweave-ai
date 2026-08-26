"""Privacy, security, and auditable-governance specialist."""

from northstar.agents.base import SpecialistAgent
from northstar.contracts import Evidence, Finding, FindingCategory, ProgramScenario, Severity


class GovernanceAgent(SpecialistAgent):
    name = "governance"
    system_prompt = (
        "Act as a privacy and governance guard. Identify concrete PHI, encryption, audit, and approval "
        "gaps without reproducing sensitive data. Return only the AgentAssessment schema."
    )

    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        findings: list[Finding] = []
        for service in scenario.services:
            if service.contains_phi and not service.encryption_at_rest:
                findings.append(Finding(
                    id=f"GOV-ENC-{service.id}", agent=self.name,
                    category=FindingCategory.PRIVACY, severity=Severity.CRITICAL,
                    title="PHI-bearing service lacks encryption at rest",
                    evidence=[Evidence(source_id=service.id, statement="Control metadata marks PHI present and encryption_at_rest false.")],
                    recommendation="Block release until approved encryption and key-management controls are verified.",
                    confidence=1.0, requires_human_decision=True,
                ))
            if service.contains_phi and not service.audit_logging:
                findings.append(Finding(
                    id=f"GOV-AUDIT-{service.id}", agent=self.name,
                    category=FindingCategory.COMPLIANCE, severity=Severity.CRITICAL,
                    title="PHI access is not covered by an audit trail",
                    evidence=[Evidence(source_id=service.id, statement="Control metadata marks PHI present and audit_logging false.")],
                    recommendation="Block production use until tamper-resistant access auditing and retention are validated.",
                    confidence=1.0, requires_human_decision=True,
                ))
        return findings
