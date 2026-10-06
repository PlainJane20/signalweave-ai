# Tracing (optional OpenTelemetry)

Northstar can emit OpenTelemetry spans for an orchestrator run. It is **off by
default and changes no behaviour**: with `opentelemetry-api` not installed, or
installed but with no SDK `TracerProvider` configured, every span is a no-op.

## What is traced

```
northstar.run                      one DecisionOrchestrator.run()
├── northstar.agent  (x6)          one per specialist
│   └── northstar.fallback         only when the provider failed and the offline rules were used
└── northstar.policy.gate          the deterministic policy decision
```

| Span | Attribute | Type | Notes |
|---|---|---|---|
| `run` | `provider.mode` | enum string | `offline`, `openai`, ... |
| `run` | `agents.count`, `findings.count`, `options.count`, `recommended.count` | int | counts only |
| `run` | `gate.verdict` | enum string | `allow`, `human_review`, `block` |
| `agent` | `agent.name` | string | specialist class name (a code identifier) |
| `agent` | `model.name` | string | configured model id, or `none` in offline mode |
| `agent` | `provider.mode` | enum string | |
| `agent` | `analysis.mock` | bool | true for the offline (rule-based) provider |
| `agent` | `agent.success` | bool | false if the provider failed or an error was raised |
| `agent` | `agent.fallback` | bool | true if the deterministic fallback replaced a failed provider |
| `agent` | `findings.count`, `duration_ms` | int / float | |
| `fallback` | `agent.name`, `fallback.reason` | string | `fallback.reason` is the exception **type name** |
| `policy.gate` | `gate.verdict`, `gate.reason` | string | reason is one of the fixed policy strings |
| `policy.gate` | `findings.count`, `gate.blocking.count`, `gate.review.count` | int | |

Errors are recorded as a span status of `ERROR` plus an `exception` event that
carries only `exception.type`.

## What is deliberately NOT recorded

Prompts, system prompts, scenario content (titles, organization, initiative
names, constraints), finding text, evidence, report text, exception messages
(the report itself embeds provider error text; spans do not), API keys, and
environment values. Attributes are identifiers, counts, enums, verdicts and
durations only; strings are truncated to 64 characters as a backstop. A test
(`test_no_sensitive_strings_in_span_attributes`) runs scenarios containing
sentinel secrets and asserts none appear in any span, event or status.

## Enabling

```bash
pip install -e '.[tracing]'                 # opentelemetry-api only (still a no-op)
pip install opentelemetry-sdk               # needed to actually record/export
python examples/tracing_export.py           # console exporter, offline provider
```

For an OTLP collector, also install `opentelemetry-exporter-otlp-proto-http` and run
`OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 python examples/tracing_export.py`.

Either call `northstar.tracing.configure(provider)` with your own
`TracerProvider` (as the example does) or set the global provider with
`opentelemetry.trace.set_tracer_provider(...)` before running.

## Honest limits

- Not tested against a real collector or tracing backend. The OTLP path in the
  example is the standard SDK wiring and was not exercised here; only the
  console exporter and the in-memory exporter were run.
- No sampling configuration is provided; use the SDK's sampler on your provider.
- Tests use the offline provider and a stub failing provider only. The hosted
  OpenAI path is instrumented through the same `agent` span (model name from
  its configuration) but was not exercised live.
- The provider call itself has no dedicated span; its latency is the `agent` span.
- Verified on Python 3.14 locally; CI matrix (3.11, 3.12) will run the suite.
  Without the SDK the tracing tests skip, and the no-op path is tested by
  simulating an import failure.
