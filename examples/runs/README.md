# Example run documents

Two sanitized files that show what SynthRange's run contracts look like when filled in:

- [`bounded-web-discovery.yaml`](bounded-web-discovery.yaml) — a run brief. It is the input: the authorization boundary an operator writes before anything starts, declaring the target, the composed playbooks, the Red and Blue participants and their required outputs, the traffic policy, per-role authority, lifecycle and stop conditions, required evidence, and how approvals are handled. It validates against [`schemas/run-brief.schema.json`](../../schemas/run-brief.schema.json).
- [`run-state.created.json`](run-state.created.json) — the run state Observer would record for that brief at the moment the run directory is created. Both roles are `pending`, no evidence is sealed, and the history is empty. It validates against [`schemas/run-state.schema.json`](../../schemas/run-state.schema.json).

The two files share the run identifier `bounded-web-discovery-001`: the brief declares the intent, and the state document is the first entry in the machine-owned record that follows from it. Reading them side by side shows which fields are authored by a person and which are owned by Observer.

## What these are not

These are illustrative contract documents, not a completed public run. The endpoint is an RFC 5737 documentation address, the provider and model names are placeholders, and no evidence, timeline, or report from a real run is published here. Nothing downstream of `created` is shown.

They are also not an onboarding recipe. This repository has no zero-to-first-run deployment path, so these files cannot be executed as written — read them to understand the contracts, and see [`schemas/`](../../schemas/README.md) for the full field definitions.
