# Architecture

## Design goals

Northstar is built around five properties:

1. **Evidence before prose.** Findings identify the source entities and assumptions that support them.
2. **Determinism at the control plane.** Policy gates and workflow transitions are ordinary code, not prompts.
3. **Typed boundaries.** Every scenario, finding, option, and report is validated before another component consumes it.
4. **Provider independence.** Specialist analysis can be deterministic or model-assisted without changing domain contracts.
5. **Human ownership.** High-impact decisions are recommendations until an accountable person records a disposition.

## Processing model

```mermaid
sequenceDiagram
    actor User
    participant API
    participant Validator
    participant Orchestrator
    participant Agents
    participant Gate
    participant Arbiter
    participant Log

    User->>API: Select scenario / submit program
    API->>Validator: Parse strict contracts
    Validator-->>API: Validated program
    API->>Orchestrator: Analyze(program, shock)
    Orchestrator->>Agents: Run narrow analyses
    Agents-->>Orchestrator: Evidence-linked findings
    Orchestrator->>Gate: Evaluate findings and policy
    Gate-->>Orchestrator: Allow / escalate / block
    Orchestrator->>Arbiter: Findings + gate results
    Arbiter-->>API: Options + tradeoffs + confidence
    User->>API: Human decision and rationale
    API->>Log: Append auditable disposition
```

## Layer responsibilities

| Layer | Owns | Must not own |
|---|---|---|
| Contracts | Data shape, enums, numeric bounds | Business decisions |
| Agents | Narrow analysis and cited findings | Cross-program policy |
| Orchestration | Ordering, fan-out, aggregation | Provider-specific parsing |
| Policy gates | Escalation/block conditions | Free-form recommendations |
| Arbiter | Comparable decision options | Silent approval |
| API/UI | Transport and explanation | Domain logic |
| Provider adapters | SDK calls, timeout/retry, response conversion | Secrets in logs or domain policy |

## Failure behavior

- Invalid input fails before agent execution.
- One specialist failure is represented explicitly; it is never converted to a successful empty result.
- A malformed provider response fails schema validation.
- Provider timeouts and retry exhaustion surface a safe error without request contents or credentials.
- Missing evidence reduces confidence or triggers escalation.
- A blocked policy outcome cannot be overwritten by a model-generated recommendation.
- Offline analysis remains available when no external provider is configured.

## Trust boundaries

```mermaid
flowchart TB
    subgraph Untrusted
      U[User artifacts]
      M[Model output]
    end
    subgraph Validated application boundary
      C[Pydantic contracts]
      P[Deterministic policy]
      A[Audit-safe report]
    end
    subgraph Secrets boundary
      ENV[Environment variables]
      SDK[Optional provider SDK]
    end

    U --> C
    M --> C
    C --> P --> A
    ENV --> SDK
    SDK --> M
    ENV -. never logged .-> A
```

## Scoring interpretation

A confidence score is a transparent heuristic over the supplied synthetic facts; it is not a probability of real-world success. The UI should always expose contributing signals, assumptions, and sensitivity to scenario changes. Scores should be compared within the same configured model, not across organizations.
