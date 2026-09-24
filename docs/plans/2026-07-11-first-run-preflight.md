# First Real Run Preflight Plan

> **For Hermes:** Execute this plan manually from Observer. Do not start Red or Blue Hermes until every mandatory gate passes and the operator explicitly authorizes the run.

**Goal:** Prove that the live five-machine range can produce attributable, time-aligned evidence before autonomous Red and Blue agents are started.

**Architecture:** Observer is the control point for preflight evidence. It validates Red, Blue, Target, Traffic Proxy, and itself through the configured SSH destinations, while Juice Shop and the proxy remain passive test subjects. The preflight creates its own Observer run directory so every check is preserved without contaminating the later real-run identity.

**Systems:** Red, Blue, Observer, Juice Shop Target, Traffic Proxy, BBT, Hermes CLI, systemd, Docker, mitmproxy, Observer `sr-*` helpers.

---

## Operating constraints

- Do not start Red or Blue Hermes.
- Do not change model, tool, firewall, proxy, target, or Hermes configuration.
- Do not install or update packages.
- Do not restart services unless a failed gate is reviewed and the operator approves remediation.
- Do not create Proxmox snapshots; snapshots remain operator-owned.
- Never copy API keys, tokens, or full Hermes environment files into run evidence.
- Packet capture is disabled by default. A short scoped test requires explicit operator approval.
- Stop immediately if target identity, SSH destination, or capture scope differs from the declared lab.

## Deliverables

The preflight produces:

```text
/srv/synthrange/runs/<preflight-run-id>/
├── metadata.json
├── timeline.jsonl
├── observer/
│   ├── live-version-inventory.txt
│   ├── time-alignment.txt
│   └── model-inventory.json
├── proxy/
│   ├── status-before.txt
│   └── probe-event.jsonl
├── target/
│   ├── service-status.txt
│   └── health.txt
├── artifacts/
│   ├── bbt/preflight/
│   ├── validation/
│   └── pcaps/                 # only if explicitly approved
├── reports/preflight.md
└── artifact-index.json
```

The report ends with one verdict: `GO`, `CONDITIONAL GO`, or `NO-GO`.

---

## Task 1: Freeze and identify the live environment

**Objective:** Confirm that the preflight is pointed at the intended five machines before collecting evidence.

1. On Observer, resolve `/srv/synthrange/config/hosts.env` and confirm that all five role variables are present.
2. Record hostnames returned by each configured SSH destination; do not record secrets or full environment files.
3. Confirm the expected role mapping: Red, Blue, Target, Proxy, Observer.
4. Confirm there is no currently active run or packet-capture PID under `/srv/synthrange/latest/state/`.
5. Confirm no Hermes process or gateway is active on Red or Blue.
6. Record a `preflight.identity.validated` timeline event after the run directory exists.

**Pass:** Five unique expected hosts; Red and Blue Hermes stopped; no unexplained active capture or run process.

**Fail:** Wrong/duplicate host, unreachable Observer SSH destination, active autonomous agent, or ambiguous run state.

---

## Task 2: Create an isolated preflight run

**Objective:** Give preflight evidence its own run identity.

On Observer:

```bash
RUN_DIR=$(/srv/synthrange/scripts/sr-new-run first-run-preflight)
RUN_ID=$(basename "$RUN_DIR")
printf '%s\n' "$RUN_DIR" "$RUN_ID"
```

Then:

1. Copy this plan into `$RUN_DIR/observer/`.
2. Record the repository commit used for the plan and helper comparison.
3. Record `preflight.started` with the operator-approved scope.
4. Verify `metadata.json`, `timeline.jsonl`, and expected artifact directories exist.

**Pass:** New unique run directory, valid metadata, writable timeline, and `/srv/synthrange/latest` points to it.

**Fail:** Existing ID collision, unexpected permissions, stale symlink, or inability to append a timeline event.

---

## Task 3: Verify live/repository parity

**Objective:** Detect drift between the live machines and the canonical repository before relying on helper behavior.

Compare checksums or sanitized diffs for:

- Observer `/srv/synthrange/scripts/sr-*` and configuration shape;
- Traffic Proxy addon, helper scripts, environment-variable names, and systemd unit;
- Juice Shop Compose image/tag/digest and service name;
- BBT executable location (`/usr/local/bin/bbt`) on all five machines;
- Hermes versions and profile locations on Red and Blue.

Do not automatically overwrite live files.

Record each item as:

```text
MATCH
DRIFT-UNDERSTOOD
DRIFT-BLOCKING
NOT-DEPLOYED
```

**Pass:** All evidence-critical files match or have understood, documented drift.

**Fail:** Drift changes run IDs, proxy event structure, target identity, collection paths, or stop behavior.

---

## Task 4: Verify connectivity, time, and storage

**Objective:** Ensure evidence from different systems can be correlated and retained.

From Observer:

1. Test non-interactive SSH to every configured host using the declared `SSH_OPTS`.
2. Record UTC epoch and ISO timestamps from all five hosts.
3. Calculate maximum clock skew relative to Observer.
4. Record filesystem usage with BBT.
5. Verify Observer has enough free space for the expected logs plus twice the estimated capture budget.
6. Verify DNS/host resolution used by Observer, Proxy, Red, and Blue resolves to the intended Target.

**Mandatory thresholds:**

- SSH succeeds for all five roles.
- Maximum clock skew is no more than two seconds.
- Observer has at least 5 GiB free without packet capture, or at least 20 GiB with packet capture.
- No filesystem is critically full.

**Fail:** Unreachable host, clock skew above threshold, ambiguous target resolution, or insufficient Observer space.

---

## Task 5: Capture the BBT baseline

**Objective:** Prove that Observer can collect structured facts from every machine.

```bash
/srv/synthrange/scripts/sr-snapshot "$RUN_DIR" preflight
```

Verify for every role:

- `hostname.txt` exists and is correct;
- host snapshot, process list, listener list, and disk usage JSON are non-empty and parseable;
- `.err` files are empty or explained;
- timeline events exist for all five captures.

**Pass:** Complete parseable baseline for five roles.

**Fail:** Missing BBT, SSH failure, malformed JSON, wrong host identity, or silent collection gap.

---

## Task 6: Verify Juice Shop target health and reset ownership

**Objective:** Confirm that the intended target is healthy without modifying it.

1. Record Docker service name, image reference, immutable digest, status, health, and published ports.
2. Verify the running image corresponds to the adapter version expected by the repository; document drift without pulling/recreating.
3. Run Observer target health:

```bash
/srv/synthrange/scripts/sr-health "$RUN_DIR"
```

4. Send one direct harmless `GET /` health request.
5. Confirm target logs are readable by the configured collection account.
6. Confirm who owns reset/recreate authority; do not reset during preflight.

**Pass:** Correct target, expected port, healthy response, readable logs, and explicit reset owner.

**Fail:** Wrong image/service, unstable health, inaccessible logs, or uncertainty about reset authority.

---

## Task 7: Verify Traffic Proxy policy and evidence

**Objective:** Prove that Red traffic can be attributed to the preflight run and cannot leave the declared target scope.

1. Capture proxy status with `sr-proxy-status`.
2. Verify service state, listener, log path, target allowlist, and allowed ports.
3. Confirm the proxy environment has a non-placeholder run ID policy for the real run.
4. Send one harmless proxied request carrying the run identity:

```bash
curl --fail --silent --show-error \
  --proxy "http://<proxy-host>:8080" \
  --header "x-synthrange-run-id: $RUN_ID" \
  "<target-url>/" >/dev/null
```

5. Extract only the matching event into `$RUN_DIR/proxy/probe-event.jsonl`.
6. Verify timestamp, `run_id`, target host/port, method, status, and source classification.
7. Do not test an unauthorized external destination. Validate deny behavior through configuration inspection or an operator-approved non-routable fixture only.

**Pass:** Exactly attributable probe event, correct target, no sensitive request headers recorded, and explicit allowlist.

**Fail:** Missing/duplicate event, wrong run ID, target bypass, unredacted credentials, or permissive/empty allowlist.

---

## Task 8: Verify Observer collection semantics

**Objective:** Determine whether the current collectors preserve attribution accurately enough for the first run.

Test and document these known caveats:

1. `sr-collect` copies the full proxy JSONL rather than a run-filtered slice.
2. Target Docker logs currently use a hardcoded two-hour window rather than the supplied `SINCE` argument.
3. `metadata.json` has one `playbook` string and cannot yet represent shared, Red, and Blue playbooks plus model metadata.

For preflight:

- run collection only after the proxy probe and target health test;
- verify the matching run ID can be deterministically filtered from collected proxy evidence;
- measure unrelated proxy events included in the full copy;
- verify target-log timestamps cover the preflight;
- write sanitized model/playbook metadata separately under `observer/`.

**Pass:** Attribution remains deterministic despite documented extra data.

**Conditional pass:** Extra data exists but can be filtered safely and reproducibly before analysis.

**Fail:** The probe or target activity cannot be attributed uniquely to the run.

---

## Task 9: Verify Red and Blue Hermes readiness without starting agents

**Objective:** Record comparable agent environments and model metadata without making an inference call.

On both Red and Blue, capture sanitized output from:

```bash
hermes --version
hermes config check
hermes doctor
hermes status --all
hermes tools list
hermes auth list
```

Additionally record, without credential values:

- active Hermes profile;
- configured provider and exact model ID;
- model endpoint/base URL classification (`hosted`, `local`, or `custom`), not credentials;
- reasoning/temperature settings where configured;
- enabled toolsets and relevant skills;
- terminal backend and working directory;
- network/proxy environment relevant to Red;
- current session/process state.

Compare Red and Blue and label every difference as intentional or unexplained.

Do not run `hermes chat`, start a gateway, or create a model session during preflight.

**Pass:** Both installations are healthy, authenticated, model IDs are known, tool differences are intentional, and no agent process is active.

**Fail:** Unknown model, expired/missing authentication, config errors, unexplained tool access, or unintended active session.

---

## Task 10: Decide packet-capture status

**Objective:** Make packet capture an explicit evidence decision, not an accidental default.

Default decision for the first run: **disabled**, because proxied web traffic already produces structured evidence.

Enable only if the operator approves and all conditions hold:

- `CAPTURE_FILTER` is explicit and limited to declared range hosts;
- `CAPTURE_INTERFACE` is correct;
- `sudo tcpdump` works non-interactively for the intended service account;
- retention and estimated storage are acceptable;
- captured data adds a stated analytical benefit.

If approved, perform a 10–15 second start/stop test using:

```bash
/srv/synthrange/scripts/sr-capture-rotated "$RUN_DIR"
/srv/synthrange/scripts/sr-stop-capture "$RUN_DIR"
```

Verify a readable PCAP, timeline start/stop events, and no surviving PID.

**Fail:** Broad filter, wrong interface, unexplained sudo behavior, unreadable PCAP, or lingering capture process.

---

## Task 11: Finalize and review preflight evidence

**Objective:** Produce an auditable go/no-go decision.

1. Run final target health.
2. Build the artifact index:

```bash
/srv/synthrange/scripts/sr-index-artifacts "$RUN_DIR"
```

3. Verify every indexed file exists and each SHA-256 hash matches.
4. Write `reports/preflight.md` with:
   - host and service verdicts;
   - time skew;
   - storage;
   - live/repository drift;
   - target and proxy checks;
   - Observer attribution caveats;
   - Red/Blue Hermes versions, models, and tool differences;
   - packet-capture decision;
   - unresolved blockers;
   - final verdict.
5. Record `preflight.completed` or `preflight.failed`.
6. Do not start agents in the same session as the review. Obtain explicit operator authorization afterward.

---

## GO criteria

All are mandatory:

- [ ] Five correct machines reachable
- [ ] Clock skew ≤ 2 seconds
- [ ] Adequate storage
- [ ] BBT baseline complete for all machines
- [ ] Juice Shop healthy and correctly identified
- [ ] Proxy allowlist explicit
- [ ] Harmless proxied request attributable to the preflight run
- [ ] Observer timeline and artifact hashes valid
- [ ] Collection caveats do not prevent attribution
- [ ] Red and Blue Hermes healthy but stopped
- [ ] Exact Red and Blue provider/model IDs recorded
- [ ] Tool and authority differences understood
- [ ] Packet capture explicitly enabled or disabled
- [ ] Stop and target-reset ownership understood
- [ ] No unexplained blocking drift

## Verdict meanings

- **GO:** Start the real run after explicit operator authorization.
- **CONDITIONAL GO:** Only non-attribution-breaking caveats remain and are accepted in writing.
- **NO-GO:** Fix the stated blockers, create a new preflight run, and repeat affected checks.

## Expected duration

- Identity, drift, connectivity: 20–30 minutes
- BBT, target, proxy, Observer evidence checks: 20–30 minutes
- Hermes/model inventory: 15–20 minutes
- Evidence review and verdict: 15–20 minutes

Expected total: **70–100 minutes**, with no autonomous agent activity.
