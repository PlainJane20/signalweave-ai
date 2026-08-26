from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from northstar.contracts import AgentAssessment
from northstar.providers import OfflineProvider, OpenAIProvider, ProviderError, build_provider


def test_offline_provider_returns_deterministic_fallback(baseline_scenario) -> None:
    fallback = AgentAssessment(agent="test", summary="A deterministic assessment.")

    result = OfflineProvider().assess(
        system_prompt="Analyze only the supplied evidence.",
        scenario=baseline_scenario,
        fallback=fallback,
    )

    assert result == fallback
    assert result.analysis_mode == "offline"


def test_provider_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderError, match="Unsupported"):
        build_provider("not-a-provider")


def test_openai_provider_requires_environment_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        OpenAIProvider()


def test_openai_provider_parses_structured_response_without_network(
    monkeypatch, baseline_scenario
) -> None:
    parsed = AgentAssessment(agent="mock", summary="Mock provider result.", analysis_mode="openai")
    parse = Mock(return_value=SimpleNamespace(output_parsed=parsed))
    fake_client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    constructor = Mock(return_value=fake_client)
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-placeholder")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=constructor))
    provider = OpenAIProvider()

    result = provider.assess(
        system_prompt="Return a typed assessment.",
        scenario=baseline_scenario,
        fallback=AgentAssessment(agent="mock", summary="Fallback."),
    )

    assert result == parsed
    assert parse.call_count == 1
    constructor.assert_called_once()


def test_openai_provider_wraps_sdk_errors_without_payload(
    monkeypatch, baseline_scenario
) -> None:
    parse = Mock(side_effect=TimeoutError("request contained private payload"))
    fake_client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-placeholder")
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=Mock(return_value=fake_client)),
    )
    provider = OpenAIProvider()

    with pytest.raises(ProviderError) as caught:
        provider.assess(
            system_prompt="Typed assessment.",
            scenario=baseline_scenario,
            fallback=AgentAssessment(agent="mock", summary="Fallback."),
        )

    assert "TimeoutError" in str(caught.value)
    assert "private payload" not in str(caught.value)


def test_external_provider_blocks_phi_without_explicit_authorization(
    monkeypatch, baseline_scenario
) -> None:
    parse = Mock()
    fake_client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-placeholder")
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=Mock(return_value=fake_client)),
    )
    provider = OpenAIProvider()
    sensitive = baseline_scenario.model_copy(
        update={
            "services": [
                baseline_scenario.services[0].model_copy(update={"contains_phi": True})
            ]
        }
    )

    with pytest.raises(ProviderError, match="External analysis denied"):
        provider.assess(
            system_prompt="Typed assessment.",
            scenario=sensitive,
            fallback=AgentAssessment(agent="mock", summary="Fallback."),
        )

    parse.assert_not_called()
