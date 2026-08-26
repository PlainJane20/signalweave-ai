"""Analysis-provider adapters. Domain logic intentionally lives in agents."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from northstar.contracts import AgentAssessment, ProgramScenario

T = TypeVar("T", bound=BaseModel)


class ProviderError(RuntimeError):
    """A safe, secret-free provider failure."""


class AnalysisProvider(ABC):
    mode: str

    @abstractmethod
    def assess(
        self,
        *,
        system_prompt: str,
        scenario: ProgramScenario,
        fallback: AgentAssessment,
    ) -> AgentAssessment:
        raise NotImplementedError


class OfflineProvider(AnalysisProvider):
    """Returns rule-based specialist output with no network or credentials."""

    mode = "offline"

    def assess(
        self,
        *,
        system_prompt: str,
        scenario: ProgramScenario,
        fallback: AgentAssessment,
    ) -> AgentAssessment:
        del system_prompt, scenario
        return fallback.model_copy(update={"analysis_mode": "offline"})


class OpenAIProvider(AnalysisProvider):
    """Optional structured-output adapter for the OpenAI Responses API."""

    mode = "openai"

    def __init__(self) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError("OPENAI_API_KEY is required when NORTHSTAR_PROVIDER=openai")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("Install the 'openai' extra to use the OpenAI provider") from exc
        self._allow_sensitive = os.environ.get(
            "NORTHSTAR_ALLOW_SENSITIVE_EXTERNAL", "false"
        ).lower() in {"1", "true", "yes"}
        self._model = os.environ.get("NORTHSTAR_OPENAI_MODEL", "gpt-5.4-mini")
        try:
            timeout = float(os.environ.get("NORTHSTAR_OPENAI_TIMEOUT_SECONDS", "30"))
            max_retries = int(os.environ.get("NORTHSTAR_OPENAI_MAX_RETRIES", "2"))
        except ValueError as exc:
            raise ProviderError("OpenAI timeout and retry settings must be numeric") from exc
        self._client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)

    def assess(
        self,
        *,
        system_prompt: str,
        scenario: ProgramScenario,
        fallback: AgentAssessment,
    ) -> AgentAssessment:
        if (not scenario.synthetic_data or any(service.contains_phi for service in scenario.services)) and (
            not scenario.external_processing_allowed or not self._allow_sensitive
        ):
            raise ProviderError(
                "External analysis denied: scenario may contain sensitive data and lacks explicit authorization"
            )
        payload = {
            "scenario": scenario.model_dump(mode="json"),
            "deterministic_baseline": fallback.model_dump(mode="json"),
        }
        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=system_prompt,
                input=json.dumps(payload, separators=(",", ":")),
                text_format=AgentAssessment,
            )
            if response.output_parsed is None:
                raise ProviderError("OpenAI returned no structured assessment")
            return response.output_parsed.model_copy(update={"analysis_mode": "openai"})
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"OpenAI assessment failed: {type(exc).__name__}") from exc


def build_provider(name: str | None = None) -> AnalysisProvider:
    provider_name = (name or os.environ.get("NORTHSTAR_PROVIDER", "offline")).strip().lower()
    if provider_name == "offline":
        return OfflineProvider()
    if provider_name == "openai":
        return OpenAIProvider()
    raise ProviderError(f"Unsupported NORTHSTAR_PROVIDER: {provider_name}")
