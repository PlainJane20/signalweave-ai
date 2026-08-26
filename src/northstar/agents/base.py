"""Base implementation shared by isolated specialists."""

from __future__ import annotations

from abc import ABC, abstractmethod

from northstar.contracts import AgentAssessment, Finding, ProgramScenario
from northstar.providers import AnalysisProvider


class SpecialistAgent(ABC):
    name: str
    system_prompt: str

    def __init__(self, provider: AnalysisProvider) -> None:
        self.provider = provider

    @abstractmethod
    def findings(self, scenario: ProgramScenario) -> list[Finding]:
        raise NotImplementedError

    def run(self, scenario: ProgramScenario) -> AgentAssessment:
        findings = self.findings(scenario)
        fallback = AgentAssessment(
            agent=self.name,
            summary=(
                f"{self.name} identified {len(findings)} evidence-linked finding(s)."
                if findings
                else f"{self.name} found no material exception under configured rules."
            ),
            findings=findings,
        )
        return self.provider.assess(
            system_prompt=self.system_prompt,
            scenario=scenario,
            fallback=fallback,
        )
