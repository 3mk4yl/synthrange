# SynthRange Observer UI

**Status: Prototype; not deployed in the reference lab**

This read-only UI renders Observer run summaries, timelines, proxy events, reports, and artifacts. It does not orchestrate agents, SSH into hosts, modify evidence, or control runs.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest -q
SYNTHRANGE_RUNS_ROOTS=tests/fixtures/runs uvicorn observer_ui.app:app --host 127.0.0.1 --port 8088
```

## Runtime

The expected Observer data root is `/srv/synthrange/runs`. Bind to localhost and use an operator-controlled tunnel or reverse proxy when remote access is required.

| Variable | Default |
|---|---|
| `SYNTHRANGE_RUNS_ROOTS` | `/srv/synthrange/runs` |
| `SYNTHRANGE_UI_TITLE` | `SynthRange Observer UI` |
| `SYNTHRANGE_UI_MAX_EVENTS` | `500` |
