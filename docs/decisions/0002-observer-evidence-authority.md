# ADR 0002: Observer evidence determines compliance

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Agent reports are useful interpretations but can conflict with measured behavior, omit failures, or overstate compliance.

## Decision

Observer evidence is authoritative for scope, timing, rate, method, availability, lifecycle, approval, and artifact-completeness decisions. Agent reports remain attributed evidence and may be corrected by the final run analysis.

## Consequences

- Compliance is computed from structured events and state, not self-report.
- Reports distinguish agent claims from Observer findings.
- Proxy policy decisions and blocked requests are preserved.
- Human interventions and approvals become first-class timeline evidence.
