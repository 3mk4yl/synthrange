from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    title: str
    runs_roots: tuple[Path, ...]
    max_events: int = 500


def _default_runs_roots() -> tuple[Path, ...]:
    return (Path("/srv/synthrange/runs"),)


def load_settings() -> Settings:
    title = os.environ.get("SYNTHRANGE_UI_TITLE", "SynthRange Observer UI")
    max_events = int(os.environ.get("SYNTHRANGE_UI_MAX_EVENTS", "500"))
    roots_env = os.environ.get("SYNTHRANGE_RUNS_ROOTS")
    if roots_env:
        roots = tuple(Path(part).expanduser().resolve() for part in roots_env.split(":") if part.strip())
    else:
        roots = tuple(path.resolve() for path in _default_runs_roots())
    return Settings(title=title, runs_roots=roots, max_events=max_events)
