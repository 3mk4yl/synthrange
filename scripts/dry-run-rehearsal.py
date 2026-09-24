#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
OBSERVER = ROOT / "components/observer/scripts"
POLICY_PATH = ROOT / "components/traffic-proxy/addon/synthrange_policy.py"


def command(name: str, *args: object, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(OBSERVER / name), *(str(arg) for arg in args)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def file_hashes(run_dir: Path) -> dict[str, str]:
    return {
        path.relative_to(run_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(run_dir.rglob("*"))
        if path.is_file()
    }


def make_writable(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not path.is_symlink():
            path.chmod(path.stat().st_mode | 0o700)
    root.chmod(root.stat().st_mode | 0o700)


def load_policy_module():
    spec = importlib.util.spec_from_file_location("synthrange_policy", POLICY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_contracts() -> None:
    brief_schema = json.loads((ROOT / "schemas/run-brief.schema.json").read_text())
    state_schema = json.loads((ROOT / "schemas/run-state.schema.json").read_text())
    brief = yaml.safe_load((ROOT / "examples/runs/bounded-web-discovery.yaml").read_text())
    state = json.loads((ROOT / "examples/runs/run-state.created.json").read_text())
    jsonschema.Draft202012Validator.check_schema(brief_schema)
    jsonschema.Draft202012Validator.check_schema(state_schema)
    jsonschema.Draft202012Validator(brief_schema).validate(brief)
    jsonschema.Draft202012Validator(state_schema).validate(state)


def rehearse(workspace: Path) -> dict:
    validate_contracts()
    env = os.environ | {
        "SYNTHRANGE_ROOT": str(workspace),
        "SYNTHRANGE_SCHEMA_DIR": str(ROOT / "schemas"),
    }
    (workspace / "config").mkdir(parents=True)
    brief = ROOT / "examples/runs/bounded-web-discovery.yaml"
    run_dir = Path(command("sr-new-run", "bounded-web-discovery", brief, env=env).stdout.strip())

    command("sr-run-state", run_dir, "run", "preflight", env=env)
    command("sr-run-state", run_dir, "red", "ready", env=env)
    command("sr-run-state", run_dir, "blue", "ready", env=env)
    command("sr-run-state", run_dir, "run", "baseline", env=env)
    command("sr-approval", run_dir, "operator", "approved", "start bounded discovery", "dry preflight passed", "run-brief.spec.authority", env=env)
    command("sr-run-state", run_dir, "red", "running", env=env)
    command("sr-run-state", run_dir, "blue", "running", env=env)
    command("sr-run-state", run_dir, "run", "active", env=env)

    module = load_policy_module()
    policy = module.RunTrafficPolicy(
        allowed_methods={"GET", "HEAD", "OPTIONS"},
        max_requests=3,
        requests_per_second=1.0,
        burst=2,
        require_run_id=True,
        expected_run_id=run_dir.name,
    )
    attempts = [
        ("GET", 0.0),
        ("HEAD", 0.0),
        ("GET", 0.0),
        ("GET", 1.0),
        ("POST", 2.0),
        ("GET", 3.0),
    ]
    events = []
    for sequence, (method, timestamp) in enumerate(attempts, 1):
        decision = policy.evaluate(run_dir.name, "red", method, now=timestamp)
        events.append({
            "sequence": sequence,
            "run_id": run_dir.name,
            "source_host": "red-agent",
            "target_host": "192.0.2.30",
            "method": method,
            "event_type": "request_response" if decision.allowed else "blocked",
            "policy_reason": decision.reason,
            "accepted_requests": decision.accepted_requests,
        })
    proxy = run_dir / "proxy/proxy-events.jsonl"
    proxy.parent.mkdir(parents=True, exist_ok=True)
    proxy.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
    target = run_dir / "target/target.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("dry target remained healthy\n", encoding="utf-8")
    command("sr-blue-append-segment", run_dir, proxy, target, "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z", env=env)

    for role in ("red", "blue"):
        role_dir = run_dir / role
        role_dir.mkdir(exist_ok=True)
        (role_dir / "observations.md").write_text(f"# {role.title()} observations\n\nDry rehearsal evidence.\n", encoding="utf-8")
        (role_dir / "report.md").write_text(f"# {role.title()} report\n\nDry rehearsal complete.\n", encoding="utf-8")
        command("sr-finalize-role", run_dir, role, env=env)

    command("sr-run-state", run_dir, "run", "finalizing", env=env)
    command("sr-run-state", run_dir, "run", "stopped", "dry rehearsal complete", env=env)
    command("sr-run-state", run_dir, "run", "collected", "local evidence complete", env=env)
    archive = Path(command("sr-archive-run", run_dir, env=env).stdout.strip())
    expected_hash = Path(f"{archive}.sha256").read_text().split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected_hash
    with tarfile.open(archive) as bundle:
        member = bundle.extractfile(f"{run_dir.name}/artifact-index.json")
        assert member is not None
        assert member.read() == (run_dir / "artifact-index.json").read_bytes()

    sealed_hashes = file_hashes(run_dir)
    blocked_event = subprocess.run([str(OBSERVER / "sr-event"), str(run_dir), "late.event"], capture_output=True, text=True)
    blocked_index = subprocess.run([str(OBSERVER / "sr-index-artifacts"), str(run_dir)], capture_output=True, text=True)
    assert blocked_event.returncode != 0
    assert blocked_index.returncode != 0
    assert file_hashes(run_dir) == sealed_hashes

    state = json.loads((run_dir / "state/run-state.json").read_text())
    return {
        "status": "passed",
        "run_id": run_dir.name,
        "run_state": state["status"]["state"],
        "red_state": state["status"]["actors"]["red"]["state"],
        "blue_state": state["status"]["actors"]["blue"]["state"],
        "proxy_attempts": len(events),
        "proxy_allowed": sum(event["event_type"] == "request_response" for event in events),
        "proxy_blocked": sum(event["event_type"] == "blocked" for event in events),
        "archive": str(archive),
        "archive_sha256": expected_hash,
        "sealed_files": len(sealed_hashes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a no-network, no-agent SynthRange lifecycle rehearsal")
    parser.add_argument("--workspace", type=Path, help="Keep artifacts under this directory")
    args = parser.parse_args()
    if args.workspace:
        args.workspace.mkdir(parents=True, exist_ok=True)
        result = rehearse(args.workspace.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="synthrange-rehearsal-") as temporary:
            temporary_path = Path(temporary)
            try:
                result = rehearse(temporary_path)
            finally:
                make_writable(temporary_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
