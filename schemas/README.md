# Contracts and schemas

SynthRange uses versioned YAML or JSON documents validated by JSON Schema Draft 2020-12.

- [`target-adapter.schema.json`](target-adapter.schema.json) defines target deployment, capabilities, endpoints, telemetry, and lifecycle.
- [`playbook.schema.json`](playbook.schema.json) defines role, requirements, authority, phases, evidence, composition, and outputs.
- [`run-brief.schema.json`](run-brief.schema.json) binds target, playbooks, participants, models, authority, traffic policy, approvals, evidence, and stop conditions.
- [`run-state.schema.json`](run-state.schema.json) records authoritative run/role lifecycle, timestamps, output requirements, and sealing state.

Example run documents live under [`examples/runs/`](../examples/runs/).

All contracts currently use `synthrange/v1alpha1`. Breaking changes require a new API version rather than silently changing existing documents.
