# SignalWeave competency map

This document maps demonstrated competencies to inspectable evidence. It intentionally avoids unsupported proficiency claims: every entry names the implementation, scenario behavior, or test that demonstrates the capability.

## Strategic program leadership

**Demonstrated behavior:** Translate ambiguous strategy into objectives, initiatives, constraints, metrics, and comparable choices.

**Evidence:**

- `Objective`, `Initiative`, and `ProgramScenario` contracts establish an explicit strategy-to-execution model.
- The Strategy Agent identifies work with no objective link or low strategic value.
- The arbiter produces continue, mitigate, buy, and stop options rather than a single opaque answer.
- The dashboard expresses portfolio implications in executive-ready language.

## Technical integration and architecture

**Demonstrated behavior:** Identify risks that cross service, API, team, and roadmap boundaries.

**Evidence:**

- The Architecture Agent detects deployment single points of failure and incompatible API changes.
- The Execution Agent checks ownership, capacity, and dependency sequencing.
- The synthetic scenario traces Marketplace API v2 into Mobile Launch and Seller Insights.
- The SVG dependency graph makes the propagation path visible.

## Execution systems and operating models

**Demonstrated behavior:** Create repeatable mechanisms that scale beyond one program manager or team.

**Evidence:**

- Six specialists inherit a common agent contract and return one validated assessment type.
- The orchestrator owns ordering, safe fallback, aggregation, and report synthesis.
- Deterministic policy code separates analytical breadth from approval authority.
- The decision log represents a repeatable governance cadence rather than a one-time recommendation.

## Risk, privacy, and governance

**Demonstrated behavior:** Convert policy into enforceable controls and escalate consequential decisions.

**Evidence:**

- Critical privacy/security categories can block execution.
- High-severity findings require accountable human review.
- External provider use is denied for sensitive or PHI-bearing scenarios without two explicit authorizations.
- Provider errors avoid logging prompts, credentials, or sensitive request contents.
- `docs/SECURITY.md` records trust boundaries and production limitations.

## Portfolio economics and hard choices

**Demonstrated behavior:** Balance cost, expected value, capacity, architectural risk, and strategic alignment.

**Evidence:**

- The Economics Agent detects negative modeled value and material build-versus-buy gaps.
- The checked-in scenario includes a lower-value legacy reporting initiative suitable for a stop decision.
- The reproducible report calculates a $487K modeled cost delta across recommended options.
- All financial values are labeled as synthetic inputs rather than forecasts or business claims.

## Applied AI and software architecture

**Demonstrated behavior:** Use AI within typed, observable, provider-independent system boundaries.

**Evidence:**

- Offline and OpenAI providers implement one interface.
- Hosted output must validate against the same Pydantic schema as deterministic output.
- Timeout, retry, model, and provider selection are environment-configurable.
- Safe fallback preserves deterministic analysis when hosted processing fails.
- No API key is required for the complete demonstration.

## Quality engineering

**Demonstrated behavior:** Make the system testable, reproducible, and safe under failure.

**Evidence:**

- Forty tests cover contracts, specialists, policy, orchestration, provider mocking, CLI, and HTTP behavior.
- GitHub Actions runs Python 3.11 and 3.12 matrices.
- Unexpected fields, invalid references, malformed hosted output, provider failures, and invalid HTTP requests have explicit tests.
- The frontend has no CDN or runtime framework dependency and includes an offline fallback.

## Communication and decision clarity

**Demonstrated behavior:** Distill technical complexity into evidence, options, and accountable next actions.

**Evidence:**

- Every finding contains a category, severity, confidence, source evidence, recommendation, and human-decision flag.
- Decision options expose modeled cost, value, confidence, and risk reduction.
- The dashboard combines executive metrics with expandable technical evidence.
- Architecture and agent behavior are documented with Mermaid, SVG, HTML, CSS, and concrete JSON examples.
