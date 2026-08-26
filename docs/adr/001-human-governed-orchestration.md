# ADR-001: Use human-governed, typed multi-agent orchestration

- Status: Accepted
- Date: 2026-08-26

## Context

Program decisions draw on several kinds of expertise. A single general prompt makes it difficult to tell which evidence produced a recommendation, how conflicting views were reconciled, or whether an important policy was ignored.

## Decision

Use narrow specialist analyzers that return strict contracts. A deterministic orchestrator validates and aggregates their findings. Explicit policy gates can allow, escalate, or block an action. An arbiter generates comparable options, but a human records the disposition for consequential decisions.

Provider-specific code remains behind adapters. The reference demo uses deterministic offline analyzers so results are reproducible and testable.

## Consequences

Benefits:

- findings can be traced and tested independently;
- provider failures do not redefine governance policy;
- offline demonstrations are reliable;
- human accountability is visible in the product, not buried in a disclaimer.

Costs:

- contracts and orchestration require more code than a single prompt;
- specialist findings may conflict and need explicit arbitration;
- deterministic scoring must be maintained and calibrated;
- adding an agent is only valuable when it adds a distinct, evaluable capability.

## Rejected alternatives

- **One general-purpose model call:** simpler, but weakly auditable and difficult to evaluate.
- **Model-controlled gating:** flexible, but policy enforcement becomes nondeterministic.
- **Automatic execution of recommendations:** inappropriate for portfolio, staffing, privacy, or high-impact program decisions.
