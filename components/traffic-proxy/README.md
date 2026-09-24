# Traffic Proxy

**Evidence and policy source: Available · hardened reference-lab rollout: Pending**

The Traffic Proxy uses mitmproxy to record structured HTTP events and reject requests that violate declared target, port, method, run-ID, sustained-rate, burst, or accepted-request-budget policy.

- `addon/synthrange_jsonl_addon.py` records JSONL evidence and applies policy.
- `addon/synthrange_policy.py` contains the dependency-free per-run/source policy engine.
- `scripts/sr-proxy-export-run` emits only events matching one run ID and exact collection window.
- `scripts/` contains status and tail helpers.
- `config/proxy.env.example` documents policy and deployment settings.
- `deploy/systemd/` contains the component service definition.

Policy values must match the approved run brief. `RUN_ID` binds the only accepted run namespace. Accepted-request counts are restored from existing Proxy evidence after a service restart, and restored sources resume with an empty token bucket. Blocked requests are evidence and do not count as accepted requests. Generated mitmproxy certificates, private CA material, and Proxy logs must never be committed.
