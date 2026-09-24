# Development

SynthRange is being converted from a working private lab into a public community project.

## Design rules

- Keep active documentation concise and canonical.
- Keep components independent from agent-framework integrations.
- Keep target adapters independent from individual playbooks.
- Mark future architecture as Planned or Vision.
- Store component deployment beside the component; reserve `deploy/` for whole-range assembly.
- Treat Observer evidence as authoritative for measured run compliance.
- Quarantine agent-generated skills and procedures until reviewed and tested.
- Never commit credentials, private keys, generated certificates, raw logs, packet captures, or host-specific secrets.

## Validation

Run the complete local suite:

```bash
python3 -m pytest -q tests components/observer/ui/tests
python3 scripts/dry-run-rehearsal.py
python3 -m compileall -q components scripts tests
git diff --check
```

The rehearsal uses a temporary root, documentation-only addresses, synthetic evidence, and no network or model calls. To retain its artifacts:

```bash
python3 scripts/dry-run-rehearsal.py --workspace /tmp/synthrange-rehearsal
```

The retained workspace is intentionally read-only after sealing. To remove a disposable retained rehearsal later, restore owner write permission first.

```bash
chmod -R u+w /tmp/synthrange-rehearsal
rm -rf /tmp/synthrange-rehearsal
```

A passing rehearsal proves contract validation, lifecycle transitions, structured approval capture, Proxy policy behavior, append-only Blue telemetry, role output verification, deterministic indexing, one-time sealing, and archive checksum verification. It does not replace a live reference-range run.

## Near-term contribution areas

- public Hermes Red and Blue integration templates after the hardened repeat run;
- complete Observer and Traffic Proxy packaging;
- zero-to-first-run deployment;
- target adapters for Linux, Windows, and macOS;
- composable Red and Blue playbooks;
- whole-range deployment and release automation.
