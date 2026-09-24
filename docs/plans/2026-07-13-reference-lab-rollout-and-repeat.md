# Reference-Lab Rollout and Controlled Repeat — Withdrawn Plan

**Status:** Withdrawn as executable guidance. Retained at this path to prevent stale links or historical commits from being mistaken for deployment authority.

- VM authorization: NONE.
- Inventory commands, file transfer, deployment, service restart, snapshot, Target reset, agent execution, and live repeats are not authorized by this notice.

**Last reviewed:** 2026-07-13

---

## Why this plan was withdrawn

The original rollout plan and its first review correction were committed before all asynchronous safety reviews had completed:

- `0843aa4` — initial rollout and repeat plan;
- `d9ff301` — first review-correction pass.

Later reviews found that the plan still depended on guarantees that do not exist in the current source. Continued edits then attempted to specify security-critical implementation details inside the operational runbook. That made the plan larger without making those guarantees executable or testable.

The rejected drafts exposed valid concerns, including:

- privileged manifest reconciliation and path-containment risks;
- transport-to-root staging races;
- mixed-version Observer helper replacement;
- unsafe destructive Target-reset scoping;
- incomplete active-run Blue publication coverage;
- overlapping final telemetry collection;
- weak first-run versus repeat identity anchoring.

A deployment runbook must describe tested interfaces that already exist. It must not invent their contracts while simultaneously serving as deployment authority.

## Current source position

`cce8c1868f9170fbd56df1a0786112a3e727c6c3` remains the hardened source baseline produced after the first real run. It includes tested lifecycle, policy, collection, finalization, indexing, and sealing improvements, but it is **not** sufficient authority for the proposed reference-lab rollout and controlled repeat.

No later documentation commit should be interpreted as implementing the blockers below.

## Source blockers before another rollout plan

### 1. Crash-durable Proxy request accounting

Implement and test:

- durable accepted-request intent/accounting before forwarding;
- budget restoration after process and host crashes;
- no fresh burst or budget after restart;
- a persistent fatal fail-closed state when accounting cannot be committed;
- nonzero Proxy status while the fatal state remains;
- failure-injection tests proving that an unrecorded accepted request cannot escape the restored watermark.

### 2. Transactional active-run Blue publication

Implement and test:

- immutable, contiguous half-open publication windows;
- durable transaction state and exact-sequence resumption;
- idempotent remote publication with hash verification;
- gap and overlap rejection;
- final collection of only the unpublished tail;
- collection and sealing rejection while a publication is incomplete;
- failure injection after each publication stage.

### 3. Observer-wide runtime/deployment exclusion

Implement and test a lock or maintenance mechanism that is honored by run creation, lifecycle transitions, publication, collection, indexing, and sealing. It must prevent an Observer upgrade from crossing an active helper invocation or creating a mixed-version run.

### 4. Bounded deployment and rollback mechanism

Choose the smallest mechanism justified by the actual implementation. Prefer an additive or whole-directory atomic replacement for the first rollout when it avoids privileged stale-file deletion.

If manifest reconciliation is still required, implement it as reviewed source with normalized relative paths, root-owned metadata, no-follow traversal, exact-plan approval, adversarial tests, and verified rollback. Do not recreate this boundary as inline shell deletion.

## Required sequence

1. Write focused architecture decisions for the source blockers.
2. Implement each blocker in source with adversarial and failure-injection tests.
3. Obtain a clean review of the exact frozen code diff.
4. Run the complete local suite and exact-commit GitHub Actions.
5. Test the implemented interfaces in a no-network/no-agent rehearsal.
6. Write a new, concise rollout runbook from the tested CLI and service behavior.
7. Independently review that frozen runbook before committing it.
8. Obtain separate operator authorization before any reference-lab action.

## Requirements for the replacement runbook

The replacement must:

- pin one exact source SHA and its successful exact-SHA CI run;
- begin with read-only inventory and quantitative stop conditions;
- preserve private configuration, evidence, logs, certificates, and manifests;
- deploy only the explicitly approved Observer and Proxy surfaces;
- use a tested rollback path;
- test active Blue publication during the no-agent smoke;
- bind Target reset to a validated host, adapter path, Compose project, image identity, and immediate approval—or omit reset entirely;
- compare first-run and repeat identities from checksum-anchored evidence;
- leave snapshots, destructive actions, service changes, and live execution operator-controlled.

## Historical material

Earlier detailed commands remain available through Git history for forensic and design reference only. They are not approved procedures and must not be copied into an operator session without being re-derived from tested source behavior.

The next deliverable is source implementation and review—not another expansion of this withdrawn plan.
