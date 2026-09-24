# Playbook: <name>

The YAML manifest is authoritative. This page is an authoring aid. Copy an existing `playbook.yaml`, keep the manifest as the source of truth, and validate it against [`schemas/playbook.schema.json`](../schemas/playbook.schema.json). The schema rejects unknown fields.

## Metadata

- Identifier, human-readable name, semantic version, status (`available`, `prototype`, or `planned`), and a description of what the playbook is for.

## Objective

Describe the outcome without prescribing commands.

## Role

`red | blue | shared`

## Requirements

- Target capabilities: portable dotted capability names the target must offer.
- Components: the SynthRange components the playbook needs, such as `observer` or `traffic-proxy`.

## Inputs

For each input, give a name, whether it is required, and a description of what the caller must supply.

## Authority

- Autonomous decisions:
- Approval required:
- Prohibited:

## Phases

For each phase, give an identifier, its intent, and the decision space open to the agent within it. Describe intent and decision space, not commands.

## Evidence

For each expected artifact, give a type, a source, and a description.

## Success and stopping

- Success criteria: observable outcomes that mean the playbook achieved its objective.
- Stop conditions: the circumstances under which the playbook must halt.

## Composition

- Playbooks this one strictly requires.
- Playbooks it complements without depending on.

## Outputs

- Named artifacts the playbook produces.

## ATT&CK mapping

Optional. Include technique identifiers only when the observed semantics support them.
