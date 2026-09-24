from __future__ import annotations

import html
from pathlib import Path

import markdown as markdown_lib
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import load_settings
from . import readers

settings = load_settings()
app = FastAPI(title=settings.title)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _run_or_404(run_id: str) -> readers.RunRef:
    run = readers.find_run(settings.runs_roots, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
    return run


def _markdown_to_html(text: str) -> str:
    try:
        # Reports are evidence artifacts and may contain strings copied from
        # targets, proxy events, or agent output. Preserve Markdown formatting,
        # but escape raw HTML first so the read-only UI does not become an XSS
        # surface for untrusted run content.
        return markdown_lib.markdown(html.escape(text), extensions=["tables", "fenced_code"])
    except Exception:
        return "<pre>" + html.escape(text) + "</pre>"


@app.get("/api/status")
def api_status():
    return readers.status(settings.runs_roots, settings.max_events)


@app.get("/api/runs")
def api_runs():
    return [readers.run_summary(run, settings.max_events) for run in readers.list_runs(settings.runs_roots)]


@app.get("/api/runs/{run_id}")
def api_run(run_id: str):
    return readers.run_summary(_run_or_404(run_id), settings.max_events)


@app.get("/api/runs/{run_id}/timeline")
def api_timeline(run_id: str):
    run = _run_or_404(run_id)
    return readers.jsonl(run.path / "timeline.jsonl", settings.max_events)


@app.get("/api/runs/{run_id}/proxy-events")
def api_proxy_events(run_id: str):
    run = _run_or_404(run_id)
    return readers.proxy_events(run.path, settings.max_events)


@app.get("/api/runs/{run_id}/artifacts")
def api_artifacts(run_id: str):
    run = _run_or_404(run_id)
    return readers.artifact_tree(run.path)


@app.get("/api/runs/{run_id}/reports")
def api_reports(run_id: str):
    run = _run_or_404(run_id)
    return readers.reports(run.path)


@app.get("/api/runs/{run_id}/threat-intel")
def api_threat_intel(run_id: str):
    run = _run_or_404(run_id)
    reps = readers.reports(run.path)
    final = reps.get("final", {})
    return {
        "run_id": run_id,
        "source": final.get("path"),
        "note": "v0 renders threat-intel from reports; structured extraction comes later",
        "available_reports": reps,
    }


@app.get("/", response_class=HTMLResponse)
def page_home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"status": readers.status(settings.runs_roots, settings.max_events), "title": settings.title})


@app.get("/runs", response_class=HTMLResponse)
def page_runs(request: Request):
    runs = [readers.run_summary(run, settings.max_events) for run in readers.list_runs(settings.runs_roots)]
    return templates.TemplateResponse(request, "runs.html", {"runs": runs, "title": settings.title})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def page_run(request: Request, run_id: str):
    run = _run_or_404(run_id)
    summary = readers.run_summary(run, settings.max_events)
    timeline = readers.jsonl(run.path / "timeline.jsonl", 20)
    pevents = readers.proxy_events(run.path, 20)
    return templates.TemplateResponse(request, "run_detail.html", {"run": summary, "timeline": timeline, "proxy_events": pevents, "title": settings.title})


@app.get("/runs/{run_id}/timeline", response_class=HTMLResponse)
def page_timeline(request: Request, run_id: str):
    run = _run_or_404(run_id)
    events = readers.jsonl(run.path / "timeline.jsonl", settings.max_events)
    return templates.TemplateResponse(request, "timeline.html", {"run_id": run_id, "events": events, "title": settings.title})


@app.get("/runs/{run_id}/proxy", response_class=HTMLResponse)
def page_proxy(request: Request, run_id: str):
    run = _run_or_404(run_id)
    events = readers.proxy_events(run.path, settings.max_events)
    return templates.TemplateResponse(request, "proxy.html", {"run_id": run_id, "events": events, "title": settings.title})


@app.get("/runs/{run_id}/artifacts", response_class=HTMLResponse)
def page_artifacts(request: Request, run_id: str):
    run = _run_or_404(run_id)
    items = readers.artifact_tree(run.path)
    return templates.TemplateResponse(request, "artifacts.html", {"run_id": run_id, "items": items, "title": settings.title})


@app.get("/runs/{run_id}/reports", response_class=HTMLResponse)
def page_reports(request: Request, run_id: str):
    run = _run_or_404(run_id)
    reps = readers.reports(run.path)
    rendered = {}
    for name, info in reps.items():
        if info.get("exists") and info.get("path"):
            path = readers.safe_file(run.path, info["path"])
            rendered[name] = {**info, "html": _markdown_to_html(readers.read_text_file(path))}
        else:
            rendered[name] = info
    return templates.TemplateResponse(request, "reports.html", {"run_id": run_id, "reports": rendered, "title": settings.title})


@app.get("/runs/{run_id}/file/{file_path:path}")
def raw_file(run_id: str, file_path: str):
    run = _run_or_404(run_id)
    try:
        path = readers.safe_file(run.path, file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=file_path) from exc
    return PlainTextResponse(readers.read_text_file(path))


def main() -> None:
    import uvicorn
    uvicorn.run("observer_ui.app:app", host="127.0.0.1", port=8088, reload=False)


if __name__ == "__main__":
    main()
