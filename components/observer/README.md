# Observer

**Evidence helpers: Available · lifecycle hardening: Available in source, lab rollout pending · UI: Prototype**

Observer is the neutral evidence and run-authority component. It creates run directories, records lifecycle and approval events, captures traffic, pulls exact-window logs, optionally collects Better Basic Tools (BBT) host snapshots, builds immutable Blue telemetry segments, verifies required role outputs, builds a hashed artifact index, archives runs once, and maintains a run index. It does not run a Hermes agent in the reference architecture.

Key helpers:

- `sr-new-run` validates a run brief, then creates metadata, timeline, approvals, and initial run state.
- `sr-validate-run-brief` validates the versioned brief before any run directory is created.
- `sr-run-state` enforces run and role transitions.
- `sr-approval` records structured decisions linked to timeline events.
- `sr-blue-append-segment` creates monotonic read-only telemetry segments.
- `sr-finalize-role` verifies required non-empty role outputs.
- `sr-verify-required-artifacts` enforces the run brief's evidence list before sealing.
- `sr-collect` performs run-ID and exact-time bounded collection.
- `sr-archive-run` seals once, captures final state, locks the run tree read-only, indexes final evidence, and verifies the portable archive.
- `sr-lock-run` removes write bits from the sealed evidence tree after final indexing.

Better Basic Tools (BBT) is a separate, private helper toolkit the reference lab happens to have installed on its hosts. `sr-snapshot` calls it only where the `bbt` command already exists and continues without it otherwise, so BBT is neither a SynthRange dependency nor a public integration. Runs without it simply have no BBT snapshot artifacts.

The default runtime root is `/srv/synthrange`; tests and rehearsals may set `SYNTHRANGE_ROOT`, and deployments may set `SYNTHRANGE_SCHEMA_DIR`. Install `requirements.txt` before using run-brief validation. Generated runs, packet captures, logs, and host-specific configuration must not be committed.
