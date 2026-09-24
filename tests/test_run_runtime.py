from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tarfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "components/observer/scripts"
PROXY_EXPORT = ROOT / "components/traffic-proxy/scripts/sr-proxy-export-run"


def make_writable(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not path.is_symlink():
            path.chmod(path.stat().st_mode | 0o700)
    root.chmod(root.stat().st_mode | 0o700)


def run_script(name: str, *args: object, check: bool = True, env: dict | None = None):
    return subprocess.run(
        [str(SCRIPTS / name), *(str(arg) for arg in args)],
        check=check,
        capture_output=True,
        text=True,
        env=env,
    )


def make_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "runs/test-run-001"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps({"run_id": run_dir.name, "status": "created"}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "timeline.jsonl").touch()
    (run_dir / "approvals.jsonl").touch()
    run_script("sr-run-state", run_dir, "init")
    return run_dir


def transition_run_to_collected(run_dir: Path) -> None:
    run_script("sr-run-state", run_dir, "run", "preflight", "test")
    run_script("sr-run-state", run_dir, "red", "ready", "test")
    run_script("sr-run-state", run_dir, "blue", "ready", "test")
    run_script("sr-run-state", run_dir, "run", "baseline", "test")
    run_script("sr-run-state", run_dir, "red", "running", "test")
    run_script("sr-run-state", run_dir, "blue", "running", "test")
    run_script("sr-run-state", run_dir, "run", "active", "test")
    run_script("sr-run-state", run_dir, "run", "finalizing", "test")
    run_script("sr-run-state", run_dir, "red", "stopped", "test")
    run_script("sr-run-state", run_dir, "blue", "stopped", "test")
    run_script("sr-run-state", run_dir, "run", "stopped", "test")
    run_script("sr-run-state", run_dir, "run", "collected", "test")


def test_new_run_validates_brief_and_derives_required_outputs(tmp_path: Path):
    brief = yaml.safe_load((ROOT / "examples/runs/bounded-web-discovery.yaml").read_text())
    brief["spec"]["participants"]["red"]["requiredOutputs"] = ["red/custom-report.md"]
    brief_path = tmp_path / "brief.yaml"
    brief_path.write_text(yaml.safe_dump(brief, sort_keys=False), encoding="utf-8")
    env = os.environ | {
        "SYNTHRANGE_ROOT": str(tmp_path),
        "SYNTHRANGE_SCHEMA_DIR": str(ROOT / "schemas"),
    }
    result = run_script("sr-new-run", "contract-test", brief_path, env=env)
    run_dir = Path(result.stdout.strip())
    state = json.loads((run_dir / "state/run-state.json").read_text())
    assert state["status"]["actors"]["red"]["requiredOutputs"] == ["red/custom-report.md"]

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("apiVersion: synthrange/v1alpha1\nkind: RunBrief\n", encoding="utf-8")
    rejected = run_script("sr-new-run", "invalid-test", invalid, check=False, env=env)
    assert rejected.returncode == 1
    assert "run brief validation failed" in rejected.stderr


def test_run_and_actor_state_transitions_fail_closed(tmp_path: Path):
    run_dir = make_run(tmp_path)
    invalid = run_script("sr-run-state", run_dir, "run", "active", check=False)
    assert invalid.returncode == 1
    assert "invalid run transition" in invalid.stderr

    run_script("sr-run-state", run_dir, "run", "preflight")
    run_script("sr-run-state", run_dir, "blue", "ready")
    run_script("sr-run-state", run_dir, "red", "ready")
    run_script("sr-run-state", run_dir, "run", "baseline")
    run_script("sr-run-state", run_dir, "red", "running")
    run_script("sr-run-state", run_dir, "blue", "running")
    run_script("sr-run-state", run_dir, "run", "active")
    run_script("sr-run-state", run_dir, "blue", "finalizing")

    document = json.loads((run_dir / "state/run-state.json").read_text())
    assert document["status"]["state"] == "active"
    assert document["status"]["actors"]["blue"]["state"] == "finalizing"
    assert document["status"]["sequence"] == 8


def test_approval_is_structured_and_timeline_linked(tmp_path: Path):
    run_dir = make_run(tmp_path)
    result = run_script(
        "sr-approval",
        run_dir,
        "operator",
        "approved",
        "start bounded discovery",
        "preflight passed",
        "run-brief.spec.authority",
    )
    approval = json.loads(result.stdout)
    stored = json.loads((run_dir / "approvals.jsonl").read_text())
    event = json.loads((run_dir / "timeline.jsonl").read_text().splitlines()[-1])
    assert stored == approval
    assert event["approval_id"] == approval["approval_id"]
    assert event["decision"] == "approved"


def test_role_finalization_requires_every_nonempty_output(tmp_path: Path):
    run_dir = make_run(tmp_path)
    for state in ["ready", "running"]:
        run_script("sr-run-state", run_dir, "red", state)
    failed = run_script("sr-finalize-role", run_dir, "red", check=False)
    assert failed.returncode == 1
    assert "missing required outputs" in failed.stderr

    (run_dir / "red").mkdir(exist_ok=True)
    (run_dir / "red/observations.md").write_text("observed\n")
    (run_dir / "red/report.md").write_text("reported\n")
    result = run_script("sr-finalize-role", run_dir, "red")
    assert result.stdout.strip() == "red: complete"
    state = json.loads((run_dir / "state/run-state.json").read_text())
    assert state["status"]["actors"]["red"]["state"] == "complete"


def test_blue_segments_are_monotonic_and_never_overwritten(tmp_path: Path):
    run_dir = make_run(tmp_path)
    proxy = tmp_path / "proxy.jsonl"
    target = tmp_path / "target.log"
    proxy.write_text('{"run_id":"test-run-001"}\n')
    target.write_text("first\n")
    first = Path(run_script("sr-blue-append-segment", run_dir, proxy, target, "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z").stdout.strip())
    first_hash = hashlib.sha256((first / "target.log").read_bytes()).hexdigest()
    target.write_text("second\n")
    second = Path(run_script("sr-blue-append-segment", run_dir, proxy, target, "2026-01-01T00:01:00Z", "2026-01-01T00:02:00Z").stdout.strip())
    overlap = run_script(
        "sr-blue-append-segment",
        run_dir,
        proxy,
        target,
        "2026-01-01T00:01:30Z",
        "2026-01-01T00:03:00Z",
        check=False,
    )
    assert overlap.returncode == 1
    assert "overlaps" in overlap.stderr
    assert first.name == "000001"
    assert second.name == "000002"
    assert (first / "target.log").stat().st_mode & 0o222 == 0
    assert first.stat().st_mode & 0o222 == 0
    assert hashlib.sha256((first / "target.log").read_bytes()).hexdigest() == first_hash
    index = [json.loads(line) for line in (run_dir / "blue/telemetry/index.jsonl").read_text().splitlines()]
    assert [item["sequence"] for item in index] == [1, 2]


def test_blue_segment_concurrent_append_has_one_atomic_winner(tmp_path: Path):
    run_dir = make_run(tmp_path)
    proxy = tmp_path / "proxy.jsonl"
    target = tmp_path / "target.log"
    proxy.write_text('{"run_id":"test-run-001"}\n')
    target.write_text("target\n")
    command = [
        str(SCRIPTS / "sr-blue-append-segment"),
        str(run_dir),
        str(proxy),
        str(target),
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:01:00Z",
    ]
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [process.communicate(timeout=10) for process in processes]
    assert sorted(process.returncode for process in processes) == [0, 1]
    assert any("overlaps" in stderr for _, stderr in results)
    segments = [path for path in (run_dir / "blue/telemetry/segments").iterdir() if path.name.isdigit()]
    assert [path.name for path in segments] == ["000001"]
    index = (run_dir / "blue/telemetry/index.jsonl").read_text().splitlines()
    assert len(index) == 1
    assert not [path for path in (run_dir / "blue/telemetry/segments").iterdir() if path.name.startswith(".")]


def test_proxy_export_contains_only_requested_run(tmp_path: Path):
    source = tmp_path / "proxy.jsonl"
    source.write_text(
        '\n'.join([
            json.dumps({"run_id": "run-a", "path": "/before", "ts": "2025-12-31T23:59:59Z"}),
            json.dumps({"run_id": "run-a", "path": "/a", "ts": "2026-01-01T00:00:00Z"}),
            json.dumps({"run_id": "run-b", "path": "/b", "ts": "2026-01-01T00:00:30Z"}),
            json.dumps({"run_id": "run-a", "path": "/c", "ts": "2026-01-01T00:01:00Z"}),
            json.dumps({"run_id": "run-a", "path": "/after", "ts": "2026-01-01T00:01:01Z"}),
        ]) + "\n"
    )
    result = subprocess.run(
        [str(PROXY_EXPORT), "run-a", "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert [event["path"] for event in events] == ["/a", "/c"]
    assert {event["run_id"] for event in events} == {"run-a"}


def test_archive_seals_once_and_contains_final_index(tmp_path: Path, request):
    run_dir = make_run(tmp_path)
    request.addfinalizer(lambda: make_writable(run_dir))
    (run_dir / "reports").mkdir()
    (run_dir / "reports/final-report.md").write_text("complete\n")
    transition_run_to_collected(run_dir)
    env = os.environ | {"SYNTHRANGE_ROOT": str(tmp_path)}
    archive = Path(run_script("sr-archive-run", run_dir, env=env).stdout.strip())
    assert archive.is_file()
    subprocess.run(["sha256sum", "--check", f"{archive}.sha256"], check=True, capture_output=True)
    state = json.loads((run_dir / "state/run-state.json").read_text())
    assert state["status"]["state"] == "sealed"
    assert state["status"]["evidenceSealed"] is True
    assert run_dir.stat().st_mode & 0o222 == 0
    assert (run_dir / "reports/final-report.md").stat().st_mode & 0o222 == 0
    index = json.loads((run_dir / "artifact-index.json").read_text())
    indexed_paths = {item["path"] for item in index["artifacts"]}
    assert "observer/run-state-final.json" in indexed_paths
    with tarfile.open(archive) as bundle:
        member = bundle.extractfile(f"{run_dir.name}/artifact-index.json")
        assert member is not None
        assert member.read() == (run_dir / "artifact-index.json").read_bytes()
    repeated = run_script("sr-archive-run", run_dir, check=False, env=env)
    assert repeated.returncode == 1
    blocked_event = run_script("sr-event", run_dir, "late.event", check=False)
    blocked_index = run_script("sr-index-artifacts", run_dir, check=False)
    assert blocked_event.returncode == 1
    assert blocked_index.returncode == 1
