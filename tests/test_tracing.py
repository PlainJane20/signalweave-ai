from __future__ import annotations

import builtins
import json

import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

from northstar import DecisionOrchestrator, tracing  # noqa: E402
from northstar.providers import AnalysisProvider, OfflineProvider, ProviderError  # noqa: E402


class FailingProvider(AnalysisProvider):
    mode = "failing-test-provider"

    def assess(self, *, system_prompt, scenario, fallback):
        raise ProviderError("synthetic provider outage")


class CrashingProvider(AnalysisProvider):
    mode = "crashing-test-provider"

    def assess(self, *, system_prompt, scenario, fallback):
        raise ValueError("boom")


@pytest.fixture
def spans():
    exp = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exp))
    tracing.configure(provider)
    yield exp
    tracing.configure(None)


def _dump(report):
    return report.model_dump(exclude={"generated_at"})


def named(exp, name):
    return [s for s in exp.get_finished_spans() if s.name == f"northstar.{name}"]


def test_mock_run_span_structure(spans, baseline_scenario):
    DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)
    [run] = named(spans, "run")
    agents = named(spans, "agent")
    [gate] = named(spans, "policy.gate")
    assert len(agents) == 6
    assert {a.attributes["agent.name"] for a in agents} == {
        t.name for t in DecisionOrchestrator.agent_types
    }
    assert all(a.parent.span_id == run.context.span_id for a in agents)
    assert gate.parent.span_id == run.context.span_id
    assert named(spans, "fallback") == []


def test_attributes_present(spans, baseline_scenario):
    report = DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)
    [run] = named(spans, "run")
    assert run.attributes["gate.verdict"] == report.gate.status.value == "human_review"
    assert run.attributes["agents.count"] == 6
    assert run.attributes["provider.mode"] == "offline"
    for a in named(spans, "agent"):
        assert a.attributes["analysis.mock"] is True
        assert a.attributes["agent.success"] is True
        assert a.attributes["agent.fallback"] is False
        assert a.attributes["model.name"] == "none"
        assert a.attributes["duration_ms"] >= 0
        assert "findings.count" in a.attributes
    [gate] = named(spans, "policy.gate")
    assert gate.attributes["gate.verdict"] == "human_review"
    assert gate.attributes["gate.reason"]
    assert gate.attributes["gate.review.count"] >= 1


def test_fallback_is_traced(spans, baseline_scenario):
    DecisionOrchestrator(provider=FailingProvider()).run(baseline_scenario)
    agents = named(spans, "agent")
    fallbacks = named(spans, "fallback")
    assert len(agents) == len(fallbacks) == 6
    for a in agents:
        assert a.attributes["agent.success"] is False
        assert a.attributes["agent.fallback"] is True
        assert a.attributes["analysis.mock"] is False
    for f in fallbacks:
        assert f.attributes["fallback.reason"] == "ProviderError"
        assert f.status.status_code.name == "ERROR"
        assert f.parent.span_id in {a.context.span_id for a in agents}


def test_unexpected_error_recorded_without_message(spans, baseline_scenario):
    with pytest.raises(ValueError):
        DecisionOrchestrator(provider=CrashingProvider()).run(baseline_scenario)
    [agent] = named(spans, "agent")
    [run] = named(spans, "run")
    for s in (agent, run):
        assert s.status.status_code.name == "ERROR"
        [ev] = [e for e in s.events if e.name == "exception"]
        assert dict(ev.attributes) == {"exception.type": "ValueError"}
    assert agent.attributes["agent.success"] is False
    assert "boom" not in repr([(s.attributes, s.status.description, [e.attributes for e in s.events])
                               for s in spans.get_finished_spans()])


def test_no_sensitive_strings_in_span_attributes(spans, baseline_scenario):
    secret = "sk-test-SECRET-KEY-123"
    scenario = baseline_scenario.model_copy(update={
        "title": "TOPSECRET-TITLE patient Jane Doe",
        "organization": "ACME-CONFIDENTIAL-ORG",
        "constraints": ["PROMPT-LIKE constraint text with " + secret],
    })
    orch = DecisionOrchestrator(provider=OfflineProvider())
    orch.run(scenario)
    DecisionOrchestrator(provider=FailingProvider()).run(scenario)
    dump = json.dumps(
        [
            {"attrs": dict(s.attributes), "events": [dict(e.attributes) for e in s.events],
             "status": s.status.description, "name": s.name}
            for s in spans.get_finished_spans()
        ],
        default=str,
    )
    sensitive = [secret, "TOPSECRET", "Jane Doe", "ACME-CONFIDENTIAL", "PROMPT-LIKE",
                 baseline_scenario.initiatives[0].name]
    sensitive += [t.system_prompt[:40] for t in DecisionOrchestrator.agent_types]
    for needle in sensitive:
        assert needle not in dump
    # also: provider failure text (which the report embeds) stays out of spans
    assert "synthetic provider outage" not in dump


def test_tracing_off_changes_no_outputs(baseline_scenario):
    tracing.configure(None)
    off = DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)
    exp = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exp))
    tracing.configure(provider)
    try:
        on = DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)
    finally:
        tracing.configure(None)
    assert exp.get_finished_spans()
    assert _dump(off) == _dump(on)


def test_noop_without_sdk_provider(baseline_scenario):
    tracing.configure(None)
    with tracing.span("x", a=1) as s:
        assert not s.is_recording()
    assert DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario).report_id


def test_noop_when_api_not_installed(monkeypatch, baseline_scenario):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "opentelemetry" or name.startswith("opentelemetry."):
            raise ImportError("simulated: opentelemetry not installed")
        return real_import(name, *args, **kwargs)

    expected = DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    with tracing.span("x", a=1) as s:
        s.set_attribute("k", "v")
        tracing.record_error(s, RuntimeError("x"))
    got = DecisionOrchestrator(provider=FailingProvider()).run(baseline_scenario)
    again = DecisionOrchestrator(provider=OfflineProvider()).run(baseline_scenario)
    assert _dump(again) == _dump(expected)
    assert len(got.assessments) == 6
