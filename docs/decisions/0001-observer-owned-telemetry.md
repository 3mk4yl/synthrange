# ADR 0001: Observer-owned telemetry delivery

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Blue needs Proxy, Target, and host evidence but does not require general remote administration authority. Granting broad shell or sudo access solely for observation weakens role separation.

## Decision

Observer owns collection, provenance, run scoping, and delivery of read-only telemetry to Blue. Blue consumes immutable run-scoped artifacts or streams exposed by Observer. Direct Target or Proxy control requires separate, explicit authority in the run brief.

## Consequences

- Blue can investigate without receiving infrastructure-control credentials.
- Observer must provide timely and provenance-preserving telemetry.
- Missing telemetry is recorded as a visibility gap rather than bypassed with undeclared access.
- Future transports may vary, but Observer remains the authority boundary.
