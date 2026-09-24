from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEXER = ROOT / "components/observer/scripts/sr-index-artifacts"


def test_artifact_index_is_hashed_and_excludes_transient_state(tmp_path: Path):
    run_dir = tmp_path / "sample-run"
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "state").mkdir()
    report = run_dir / "reports/final-report.md"
    report.write_text("# Result\n", encoding="utf-8")
    (run_dir / "state/tcpdump.pid").write_text("123\n", encoding="utf-8")

    subprocess.run([str(INDEXER), str(run_dir)], check=True, capture_output=True, text=True)

    index = json.loads((run_dir / "artifact-index.json").read_text(encoding="utf-8"))
    assert index["run_id"] == "sample-run"
    assert index["schema_version"] == 1
    assert index["artifacts"] == [
        {
            "path": "reports/final-report.md",
            "size": report.stat().st_size,
            "sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
        }
    ]


def test_artifact_index_is_stable_on_rebuild(tmp_path: Path):
    run_dir = tmp_path / "sample-run"
    run_dir.mkdir()
    (run_dir / "timeline.jsonl").write_text('{"event_type":"run.created"}\n', encoding="utf-8")

    subprocess.run([str(INDEXER), str(run_dir)], check=True)
    first = json.loads((run_dir / "artifact-index.json").read_text(encoding="utf-8"))
    subprocess.run([str(INDEXER), str(run_dir)], check=True)
    second = json.loads((run_dir / "artifact-index.json").read_text(encoding="utf-8"))

    assert first["artifacts"] == second["artifacts"]
    assert all(item["path"] != "artifact-index.json" for item in second["artifacts"])
