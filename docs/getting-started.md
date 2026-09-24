# Getting started

SynthRange is an open research idea and reference implementation. This page shows what exists today and how to read it; it is not an installation guide.

There is no public zero-to-first-run workflow. That is a current boundary of the project, not a task waiting for a contributor to pick up. Read the building blocks below to understand the architecture and the contracts, and treat the reference lab as unreproducible from this repository alone.

## Available building blocks

- Observer helpers: [`components/observer/`](../components/observer/)
- Traffic Proxy: [`components/traffic-proxy/`](../components/traffic-proxy/)
- Juice Shop target adapter: [`targets/juice-shop/`](../targets/juice-shop/)
- Target and playbook schemas: [`schemas/`](../schemas/)
- Initial composable playbooks: [`playbooks/`](../playbooks/)
- Sanitized example contract documents: [`examples/runs/`](../examples/runs/README.md)
- Observer UI prototype: [`components/observer/ui/`](../components/observer/ui/)
- Run and reporting templates: [`templates/`](../templates/)

## Planned first-run path

The architecture assumes this sequence. It is documented direction, not a procedure you can follow today.

1. Prepare Red, Blue, Observer, Proxy, and Target hosts.
2. Deploy the Juice Shop target adapter.
3. Deploy Observer and Traffic Proxy components.
4. Install an agent integration on Red and Blue.
5. Select playbooks and create a run brief.
6. Execute the run and preserve Observer evidence.
7. Produce defensive intelligence and detection opportunities.

Component READMEs describe the pieces that are implemented. The [roadmap](../ROADMAP.md) records what must be proven before deployment becomes reproducible.
