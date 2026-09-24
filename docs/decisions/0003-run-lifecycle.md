# ADR 0003: Explicit run and role lifecycle

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

Starting a chat does not define when a role is ready, active, finalizing, complete, or stopped. Background workers can outlive active work, and required reports can remain missing.

## Decision

Every run uses the versioned run-state contract. Normal run transitions are:

```text
created → preflight → baseline → active → finalizing → stopped → collected → sealed
```

Normal role transitions are:

```text
pending → ready → running → finalizing → complete
```

A role cannot complete until its required outputs exist and are non-empty. Invalid transitions fail closed. Stop reasons and timestamps are recorded.

## Consequences

- Orchestration has explicit gates and resumable state.
- Background workers require lifecycle ownership.
- Finalization failures are visible rather than silently accepted.
- Sealed runs cannot be mutated by lifecycle helpers.
