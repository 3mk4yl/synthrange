# ADR 0004: Quarantine agent-generated self-improvement

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

An agent can generate useful procedural improvements, but a single run can also produce target overfitting, stale terminology, unsupported conclusions, or unsafe defaults.

## Decision

Agent-generated skills, prompts, and procedural changes are stored under the run's proposal evidence. They are never promoted automatically. Promotion requires:

1. provenance and diff review;
2. comparison with Observer evidence;
3. removal of target-private and run-specific assumptions;
4. safety and pacing review;
5. regression tests or a controlled rehearsal;
6. explicit maintainer approval.

## Consequences

- Self-improvement remains possible without mutating trusted behavior during a run.
- Rejected proposals remain available for research.
- Canonical skills use SynthRange terminology and target-neutral contracts.
- Promotion is auditable and reversible.
