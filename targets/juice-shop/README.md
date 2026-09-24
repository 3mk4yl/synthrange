# OWASP Juice Shop target adapter

**Status: Available · Contract: `synthrange/v1alpha1`**

This adapter provides a containerized intentionally vulnerable web application target.

- [`target.yaml`](target.yaml) declares capabilities, endpoint, telemetry, lifecycle, and requirements.
- [`compose.yaml`](compose.yaml) provides the current deployment.

## Exposed capabilities

```text
deployment.compose
reset.container-recreate
service.health
telemetry.container-logs
web.http
web.single-page-application
web.unauthenticated-surface
```

## Lifecycle

```bash
docker compose up -d
docker compose ps
curl --fail http://localhost:3000/
docker compose down --volumes --remove-orphans
docker compose up -d --force-recreate
docker compose down
```

The deployment pins Juice Shop `v20.1.1` to its immutable multi-architecture OCI digest (Linux AMD64 and ARM64). Version upgrades must update the tag and digest together, then pass adapter health and contract tests.
