# SynthRange Run Brief

The YAML manifest is authoritative. This page is an authoring aid: it lists what a brief has to say, in the order the contract expects it. The brief you write must validate against [`schemas/run-brief.schema.json`](../schemas/run-brief.schema.json), and [`examples/runs/bounded-web-discovery.yaml`](../examples/runs/bounded-web-discovery.yaml) is a complete sanitized brief to copy from.

The schema rejects unknown fields, so anything you add here that is not in the contract belongs in your own notes rather than in the manifest.

## Metadata

- Run ID, name, and the objective the run is meant to answer.

## Target

- The target adapter and the endpoint the run is authorized to touch.

## Playbooks

- The Red, Blue, and shared playbooks composed for this run, by identifier.

## Participants

For Red and Blue each:

- Integration, provider, and model.
- Required outputs: the run-relative artifact paths that must exist and be non-empty before the role can finalize.

## Traffic policy

- Whether the proxy is required, which HTTP methods are allowed, the total request budget, the sustained request rate, and the permitted burst.

## Authority

For Red and Blue each:

- What the role may decide autonomously.
- What requires an approval before it happens.
- What is prohibited outright.

## Lifecycle

- Maximum run duration and baseline duration.
- Stop conditions, stated so that an observer can recognize one.
- The required run states the run must pass through.

## Evidence

- The artifacts the run must produce before it can be sealed.
- Confirmation that Observer evidence is authoritative.

## Approvals

- That approval decisions are recorded, and what the default decision is when no one answers.

## Artifacts

Runs are written under the Observer runtime root, which deployments configure. Do not hardcode a lab-specific path into the brief.
