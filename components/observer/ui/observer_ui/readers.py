from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT_CANDIDATES = {
    "final": ["reports/final-report.md", "final-report.md"],
    "red": ["red/red-recon-report.md", "red/report.md"],
    "blue_baseline": ["blue/initial-baseline.md"],
    "blue_triage": ["blue/post-red-triage.md", "blue/report.md"],
    "human_observation": ["observer/human-observation.md"],
}


@dataclass(frozen=True)
class RunRef:
    run_id: str
    path: Path
    root: Path


def jsonl(path: Path, limit: int = 500) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                item = {"parse_error": str(exc), "raw": line}
            events.append(item)
    if limit and len(events) > limit:
        return events[-limit:]
    return events


def list_runs(roots: tuple[Path, ...]) -> list[RunRef]:
    runs: list[RunRef] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
            if not child.is_dir():
                continue
            run_id = child.name
            key = str(child.resolve())
            if key in seen:
                continue
            seen.add(key)
            runs.append(RunRef(run_id=run_id, path=child.resolve(), root=root.resolve()))
    return runs


def find_run(roots: tuple[Path, ...], run_id: str) -> RunRef | None:
    for run in list_runs(roots):
        if run.run_id == run_id:
            return run
    return None


def _first_existing(run_path: Path, rels: list[str]) -> Path | None:
    for rel in rels:
        p = run_path / rel
        if p.exists() and p.is_file():
            return p
    return None


def proxy_event_files(run_path: Path) -> list[Path]:
    files = sorted((run_path / "proxy").glob("*.jsonl")) if (run_path / "proxy").exists() else []
    root_files = sorted(run_path.glob("*proxy*.jsonl"))
    return files + [p for p in root_files if p not in files]


def proxy_events(run_path: Path, limit: int = 500) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in proxy_event_files(run_path):
        for event in jsonl(path, limit=0):
            event.setdefault("_file", str(path.relative_to(run_path)))
            events.append(event)
    events.sort(key=lambda e: e.get("ts") or e.get("time_utc") or "")
    if limit and len(events) > limit:
        return events[-limit:]
    return events


def reports(run_path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, candidates in REPORT_CANDIDATES.items():
        p = _first_existing(run_path, candidates)
        if p:
            out[name] = {
                "name": name,
                "path": str(p.relative_to(run_path)),
                "exists": True,
                "size": p.stat().st_size,
            }
        else:
            out[name] = {"name": name, "path": None, "exists": False, "size": 0}
    return out


def artifact_tree(run_path: Path, max_files: int = 500) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for p in sorted(run_path.rglob("*")):
        if len(items) >= max_files:
            break
        if p.is_dir():
            continue
        rel = p.relative_to(run_path)
        items.append({
            "path": str(rel),
            "size": p.stat().st_size,
            "kind": mimetypes.guess_type(str(p))[0] or "text/plain",
        })
    return items


def safe_file(run_path: Path, rel_path: str) -> Path:
    target = (run_path / rel_path).resolve()
    run_resolved = run_path.resolve()
    if target != run_resolved and run_resolved not in target.parents:
        raise ValueError("path escapes run directory")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(rel_path)
    return target


def read_text_file(path: Path, max_chars: int = 200_000) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[truncated]"
    return text


def run_summary(run: RunRef, max_events: int = 500) -> dict[str, Any]:
    timeline = jsonl(run.path / "timeline.jsonl", limit=max_events)
    score = jsonl(run.path / "score_events.jsonl", limit=max_events)
    pevents = proxy_events(run.path, limit=max_events)
    reps = reports(run.path)
    final_event = next((e for e in reversed(timeline) if str(e.get("type", "")).endswith("finished") or e.get("type") == "run.finished"), None)
    first_event = timeline[0] if timeline else None
    mtime = datetime.fromtimestamp(run.path.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "run_id": run.run_id,
        "path": str(run.path),
        "root": str(run.root),
        "mtime_utc": mtime,
        "status": "finished" if final_event else ("active_or_incomplete" if timeline else "unknown"),
        "started_at": (first_event or {}).get("time_utc") or (first_event or {}).get("ts"),
        "finished_at": (final_event or {}).get("time_utc") or (final_event or {}).get("ts") if final_event else None,
        "timeline_events": len(timeline),
        "score_events": len(score),
        "proxy_events": len(pevents),
        "reports": reps,
        "final_report": reps.get("final", {}).get("exists", False),
        "red_report": reps.get("red", {}).get("exists", False),
        "blue_report": any(reps.get(k, {}).get("exists", False) for k in ["blue_baseline", "blue_triage"]),
    }


def status(roots: tuple[Path, ...], max_events: int = 500) -> dict[str, Any]:
    runs = list_runs(roots)
    summaries = [run_summary(run, max_events=max_events) for run in runs]
    return {
        "mode": "read_only_observer_files",
        "runs_roots": [{"path": str(p), "exists": p.exists(), "is_dir": p.is_dir()} for p in roots],
        "run_count": len(runs),
        "latest_run": summaries[0] if summaries else None,
        "non_goals": ["no SSH", "no orchestration", "no evidence edits", "no firewall controls"],
    }
