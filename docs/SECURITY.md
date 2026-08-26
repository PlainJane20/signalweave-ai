# Security, privacy, and limitations

## Safe defaults

- The demo runs offline and uses synthetic data.
- No API key is required for test or demo execution.
- Optional provider credentials are read from environment variables only.
- Tests mock provider clients and must never call a live service.
- Error messages identify the failed operation without reproducing potentially sensitive input.

## Production gaps

This portfolio implementation is intentionally not a production control plane. A real deployment would require:

- enterprise authentication, authorization, and tenant isolation;
- encryption and key management aligned to the deployment environment;
- data classification, minimization, retention, deletion, and residency policies;
- prompt-injection and artifact-content controls;
- immutable audit trails and privileged-action review;
- rate limits, budgets, circuit breakers, and provider outage handling;
- evaluation for accuracy, bias, calibration, and unsafe recommendations;
- dependency and container scanning plus incident response procedures;
- legal, privacy, security, and workforce review appropriate to the use case.

## Human-control policy

Northstar recommends; it does not authorize. A decision should require human review when it is high severity, low confidence, irreversible, affects people or access, invokes a privacy/security rule, or is not supported by traceable evidence. The deterministic policy layer owns these rules.

## Reporting a concern

Do not include real credentials, confidential artifacts, production records, PHI, or personal employee data in an issue. Describe the behavior with synthetic reproduction steps.
