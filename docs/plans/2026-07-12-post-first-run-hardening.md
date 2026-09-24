# Post-First-Run Hardening Implementation Plan

> **For Hermes:** Use the software-development lifecycle and validate every runtime change with regression tests and a no-agent dry rehearsal.

**Goal:** Convert first-run evidence into documented architecture, machine-readable run contracts, mechanically enforced safety controls, deterministic collection/finalization, and a repeatable dry rehearsal.

**Architecture:** Observer remains the run authority and owns lifecycle, approvals, telemetry, collection, finalization, indexing, and sealing. Traffic Proxy enforces scope, methods, request budget, and token-bucket pacing. Agent outputs and self-improvement proposals remain evidence until Observer/human validation.

**Tech Stack:** JSON Schema Draft 2020-12, YAML fixtures, Python 3.11, Bash, mitmproxy addon, pytest, jsonschema.

---

### Task 1: Document first-run lessons

**Files:**
- Create: `docs/lessons/first-real-run.md`
- Create: `docs/decisions/0001-observer-owned-telemetry.md`
- Create: `docs/decisions/0002-observer-evidence-authority.md`
- Create: `docs/decisions/0003-run-lifecycle.md`
- Create: `docs/decisions/0004-self-improvement-quarantine.md`
- Modify: `docs/architecture.md`

**Acceptance:** Sanitized facts only; no private addresses, credentials, raw evidence, or unsupported model conclusions. Decisions state context, decision, consequences, and status.

### Task 2: Update maturity and roadmap

**Files:**
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `docs/concepts.md`
- Modify: `templates/run-report-template.md`

**Acceptance:** Core evidence path is accurately labeled Available; lifecycle/orchestration and Blue finalization remain Prototype; public readiness remains blocked; report template separates observed fact, target context, risk hypothesis, validated impact, confidence, and compliance evidence.

### Task 3: Define run contracts

**Files:**
- Create: `schemas/run-brief.schema.json`
- Create: `schemas/run-state.schema.json`
- Create: `examples/runs/bounded-web-discovery.yaml`
- Create: `examples/runs/run-state.created.json`
- Modify: `schemas/README.md`
- Modify: `tests/test_contracts.py`

**Acceptance:** Schemas validate as Draft 2020-12; examples validate; references resolve to existing target/playbook IDs; brief includes authority, models, methods, pacing, budget, approvals, evidence, lifecycle, and stop conditions.

### Task 4: Enforce Proxy policy

**Files:**
- Create: `components/traffic-proxy/addon/synthrange_policy.py`
- Modify: `components/traffic-proxy/addon/synthrange_jsonl_addon.py`
- Modify: `components/traffic-proxy/config/proxy.env.example`
- Create: `components/traffic-proxy/scripts/sr-proxy-export-run`
- Create: `tests/test_proxy_policy.py`

**Acceptance:** Token bucket limits sustained rate and burst; accepted-request budget is per run/source; methods and required run ID are enforced; blocked events are recorded; export emits only the requested run; tests cover allowed, paced, exhausted, forbidden-method, and missing-run-ID behavior.

### Task 5: Implement lifecycle, approvals, collection, and sealing

**Files:**
- Create: `components/observer/scripts/sr-run-state`
- Create: `components/observer/scripts/sr-approval`
- Create: `components/observer/scripts/sr-blue-append-segment`
- Create: `components/observer/scripts/sr-finalize-role`
- Modify: `components/observer/scripts/sr-new-run`
- Modify: `components/observer/scripts/sr-pull-logs`
- Modify: `components/observer/scripts/sr-collect`
- Modify: `components/observer/scripts/sr-archive-run`
- Modify: `components/observer/README.md`
- Modify: `components/observer/config/hosts.env.example`

**Acceptance:** State transitions are validated; approval decisions are structured and timeline-linked; Blue segments are immutable and monotonic; missing required role report fails finalization; collection is run-ID/time scoped; archive contains the final index and does not mutate the run afterward.

### Task 6: Add runtime regression tests

**Files:**
- Create: `tests/test_run_runtime.py`
- Extend: `tests/test_repository_health.py`

**Acceptance:** Tests execute scripts against temporary roots; invalid state transitions fail; approval and role finalization are recorded; segments never shrink/overwrite; collection/archive source invariants prevent regressions; sanitized lessons and ADRs are linked and free of legacy vocabulary/private addresses.

### Task 7: Run a no-agent dry rehearsal

**Files:**
- Create: `scripts/dry-run-rehearsal.py`
- Create: `tests/test_dry_run_rehearsal.py`
- Modify: `docs/development.md`

**Acceptance:** The rehearsal validates contracts, creates a temporary run, transitions lifecycle states, records approvals, tests Proxy policy, appends Blue telemetry, finalizes Red/Blue outputs, indexes artifacts, creates/verifies an archive, and proves the run remains unchanged after sealing. It uses documentation-only addresses and no network or model calls.

### Final verification

Run:

```bash
python3 -m pytest -q tests components/observer/ui/tests
python3 scripts/dry-run-rehearsal.py
python3 -m compileall -q components scripts tests
git diff --check
```

Then inspect the complete diff, perform an independent integration review, commit, push, and confirm Python 3.11/3.12 CI.
