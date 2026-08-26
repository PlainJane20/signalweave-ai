"""Policy-gated multi-agent orchestration and report synthesis."""

from __future__ import annotations

import hashlib

from northstar.agents import (
    ArchitectureAgent,
    EconomicsAgent,
    ExecutionAgent,
    GovernanceAgent,
    PremortemAgent,
    StrategyAgent,
)
from northstar.arbiter import build_metrics, build_options
from northstar.contracts import (
    AgentAssessment,
    DecisionReport,
    GateStatus,
    PolicyConfig,
    ProgramScenario,
)
from northstar.policy import evaluate_gate
from northstar.providers import AnalysisProvider, OfflineProvider, ProviderError, build_provider


class DecisionOrchestrator:
    """Runs specialists, degrades safely, applies policy, and synthesizes options."""

    agent_types = (
        StrategyAgent,
        ArchitectureAgent,
        ExecutionAgent,
        GovernanceAgent,
        EconomicsAgent,
        PremortemAgent,
    )

    def __init__(
        self,
        provider: AnalysisProvider | None = None,
        policy: PolicyConfig | None = None,
    ) -> None:
        self.provider = provider or build_provider()
        self.policy = policy or PolicyConfig()

    def _run_agent(self, agent_type: type, scenario: ProgramScenario) -> AgentAssessment:
        try:
            return agent_type(self.provider).run(scenario)
        except ProviderError as exc:
            fallback = agent_type(OfflineProvider()).run(scenario)
            return fallback.model_copy(update={
                "summary": f"{fallback.summary} Hosted analysis unavailable; deterministic fallback used ({exc})."
            })

    def run(self, scenario: ProgramScenario) -> DecisionReport:
        validated = ProgramScenario.model_validate(scenario)
        assessments = [self._run_agent(agent_type, validated) for agent_type in self.agent_types]
        findings = [finding for assessment in assessments for finding in assessment.findings]
        gate = evaluate_gate(findings, self.policy)
        options = build_options(validated, findings)
        metrics = build_metrics(validated, findings, options)
        recommended = [option.id for option in options if option.recommended]
        digest_input = "|".join([validated.id, *sorted(finding.id for finding in findings)])
        report_id = "RPT-" + hashlib.sha256(digest_input.encode()).hexdigest()[:12].upper()
        headline = {
            GateStatus.BLOCK: "Execution is blocked pending remediation of prohibited risk.",
            GateStatus.HUMAN_REVIEW: "Portfolio options are ready for accountable human review.",
            GateStatus.ALLOW: "No policy threshold blocks continued execution.",
        }[gate.status]
        return DecisionReport(
            report_id=report_id,
            scenario_id=validated.id,
            executive_summary=(
                f"{headline} Six specialists produced {len(findings)} evidence-linked finding(s), "
                f"{sum(f.severity.score >= 3 for f in findings)} rated high or critical, and "
                f"{len(options)} comparable decision option(s)."
            ),
            gate=gate,
            assessments=assessments,
            options=options,
            metrics=metrics,
            recommended_option_ids=recommended,
        )
