# First real run: lessons learned

## Scope

SynthRange's first bounded web-discovery run tested one target adapter, one Red playbook, one Blue playbook, the Traffic Proxy, Observer collection, and human supervision. This document contains sanitized platform lessons. Raw run evidence remains private and is not part of the repository.

## What the run proved

- Observer can create and preserve a neutral run record across five roles.
- Traffic Proxy can constrain the target host and attribute requests to a run and source role.
- Red can operate through the required traffic path and produce reproducible evidence.
- Observer can provide Blue with read-only telemetry without granting remote control of Target or Proxy.
- Opening and closing host snapshots, target health, proxy events, agent outputs, and human events can be combined into one hashed bundle.
- Human supervision can detect differences between agent self-report and measured behavior.

## What the run did not prove

- Reliable autonomous Blue analysis and final-report completion.
- Mechanical request pacing and budget enforcement.
- Explicit agent ready, finalize, complete, and stopped acknowledgements.
- Append-only, strictly run-scoped telemetry for every source.
- Safe automatic promotion of agent-generated skills.
- Controlled comparison of model quality.
- Reproducible zero-to-first-run deployment.

## Evidence-backed lessons

### Observer evidence is authoritative

An agent described its own traffic as low rate while Observer measured a short high-rate burst. Compliance decisions must use Proxy, Target, lifecycle, approval, and human evidence rather than narrative self-assessment.

### Safety constraints need mechanical enforcement

Prompt instructions are necessary but insufficient. Host, port, method, run identifier, request rate, burst, and request budget belong at the Traffic Proxy or runner boundary.

### Blue needs telemetry, not broad control

Blue lacked direct telemetry access. Observer supplied read-only copies instead of granting a general remote shell. This preserved the baseline authority model and exposed a durable orchestration requirement.

### Rolling windows are not append-only evidence

Replacing a log with a moving time window caused apparent negative deltas when older lines expired. Run telemetry needs immutable segments, explicit cursors, and exact time bounds.

### Finalization is a protocol

A background monitor continued after active work and no Blue final report was produced. Every role needs explicit lifecycle states, required outputs, graceful stop behavior, and completion acknowledgement.

### Self-improvement is a proposal

A generated skill mixed stale terminology, target-specific conclusions, pacing mistakes, and unsupported analytical mappings. Generated procedures must be quarantined as evidence and promoted only after review.

### Reports need an evidence hierarchy

Reports must separate observed fact, target context, risk hypothesis, validated impact, confidence, and compliance evidence. Security-framework mappings are optional and must match observed semantics.

## Resulting priorities

1. Versioned run-brief and run-state contracts.
2. Proxy-enforced method, rate, burst, and budget limits.
3. Run-ID and exact-time collection.
4. Append-only Blue telemetry segments and mandatory finalization.
5. Structured human and guardrail approval events.
6. Deterministic sealing and portable archive verification.
7. Quarantined self-improvement proposals.
8. Repeat the same bounded run after these controls pass a dry rehearsal.
