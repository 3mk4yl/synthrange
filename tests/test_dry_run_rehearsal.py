from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_agent_dry_rehearsal_passes_end_to_end():
    result = subprocess.run(
        ["python3", str(ROOT / "scripts/dry-run-rehearsal.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["status"] == "passed"
    assert summary["run_state"] == "sealed"
    assert summary["red_state"] == "complete"
    assert summary["blue_state"] == "complete"
    assert summary["proxy_attempts"] == 6
    assert summary["proxy_allowed"] == 3
    assert summary["proxy_blocked"] == 3
    assert len(summary["archive_sha256"]) == 64
