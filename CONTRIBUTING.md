# Contributing to SynthRange

Thank you for helping build an open platform for AI-assisted adversarial simulation and defensive intelligence.

## Before you start

- Read the [architecture](docs/architecture.md), [concepts](docs/concepts.md), and [roadmap](ROADMAP.md).
- Search existing issues before opening a new one.
- Use a security advisory—not a public issue—for vulnerabilities in SynthRange itself. See [SECURITY.md](SECURITY.md).
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e 'components/observer/ui[test]'
python3 -m pytest -q tests components/observer/ui/tests
```

## Ways to contribute

- target adapters under `targets/<id>/`;
- Red, Blue, or shared playbooks under `playbooks/<role>/<id>/`;
- Observer and Traffic Proxy components;
- agent-framework integrations;
- tests, documentation, diagrams, and deployment tooling.

## Contract contributions

Target and playbook manifests are public APIs.

- Validate target adapters against `schemas/target-adapter.schema.json`.
- Validate playbooks against `schemas/playbook.schema.json`.
- Prefer portable capabilities over target-name checks.
- Add or update tests whenever a contract changes.
- Breaking contract changes require a new API version.

## Pull requests

1. Keep each pull request focused.
2. Explain motivation, behavior, risks, and verification.
3. Add tests for functional changes.
4. Update canonical documentation with architecture changes.
5. Run the full test command locally.
6. Confirm no credentials, logs, packet captures, private certificates, or host-specific secrets are included.

Maintainers may ask that broad proposals begin as a discussion or issue. Small fixes can go directly to a pull request.

## Licensing

By submitting a contribution, you agree that it is licensed under the [Apache License 2.0](LICENSE), consistent with section 5 of that license.
