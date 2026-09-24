# Target adapters

Target adapters describe reproducible systems SynthRange can assess. Each adapter has a `target.yaml` manifest validated by [`schemas/target-adapter.schema.json`](../schemas/target-adapter.schema.json).

## Contract

An adapter declares:

- **identity and maturity** — stable ID, version, and status;
- **deployment** — implementation type and entrypoint;
- **capabilities** — portable features playbooks can require;
- **endpoints** — adversarial, defender, Observer, or management surfaces;
- **telemetry** — evidence available from the target;
- **lifecycle** — start, verify, reset, and stop operations;
- **requirements** — tools and SynthRange components needed to operate it.

Capabilities use dotted names such as `web.http`, `service.health`, and `telemetry.container-logs`. A playbook is compatible when all of its required target capabilities are a subset of the adapter's capabilities and its required components are available in the deployment.

## Target families

| Target family | Manifest | Status |
|---|---|---|
| [OWASP Juice Shop](juice-shop/) | [`target.yaml`](juice-shop/target.yaml) | Available |
| [Linux](linux/) | Not yet defined | Planned |
| [Windows](windows/) | Not yet defined | Planned |
| [macOS](macos/) | Not yet defined | Planned |

A target adapter is infrastructure and capability metadata. It does not prescribe Red or Blue behavior.
