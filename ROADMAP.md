# Roadmap

The roadmap describes direction, not delivery dates. Status in manifests and canonical documentation remains authoritative.

## Available foundation

- target-adapter, playbook, run-brief, and run-state contracts;
- Juice Shop target adapter;
- shared evidence baseline;
- Red Web Surface Discovery and Blue Web Activity Triage playbooks;
- Observer evidence helpers and hashed artifact index;
- Traffic Proxy JSONL evidence;
- tested Proxy pacing, request-budget, method, and run-ID policy in source;
- tested lifecycle, approval, role-finalization, and deterministic sealing helpers in source;
- one sanitized, evidence-backed first-run review;
- read-only Observer UI prototype;
- canonical architecture diagrams.

## Next: repeatability before expansion

- treat the [withdrawn reference-lab rollout plan](docs/plans/2026-07-13-reference-lab-rollout-and-repeat.md) as a blocker notice, not executable guidance;
- implement and review crash-durable Proxy accounting, transactional active-run Blue publication, Observer-wide runtime/deployment exclusion, and a bounded deployment/rollback mechanism in source;
- make Observer and Traffic Proxy installation reproducible through that tested deployment/rollback boundary;
- after all four blockers pass adversarial tests and exact-commit CI, author a new concise rollout runbook from their tested behavior;
- prove paced traffic, run-scoped append-only telemetry, Blue finalization, approval capture, and one-time sealing under live conditions only after that runbook receives a clean frozen-diff review;
- package public Hermes Red and Blue integrations only after that repeat passes;
- provide a zero-to-first-run deployment path;
- stabilize the `synthrange/v1alpha1` contracts through repeated use.

## Expand

- Linux target adapters and host-focused playbooks;
- Windows target adapters and defensive telemetry;
- macOS target adapters;
- additional agent-framework integrations;
- richer Observer reporting and read-only UI views;
- portable run bundles and comparison across runs.

## Later

- whole-range provisioning and environment profiles;
- distributed or multi-target runs;
- plugin discovery and version negotiation;
- signed adapters, playbooks, and evidence bundles;
- stable versioned releases.

## Public-launch gates

- public history and secret review;
- reproducible onboarding from a clean environment;
- license and community health files;
- security reporting path;
- CI on every pull request;
- approved SynthRange header image and basic identity;
- clear separation of Available, Prototype, Planned, and Vision capabilities;
- successful repeat of the bounded reference run with hardened controls.
