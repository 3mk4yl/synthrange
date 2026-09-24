import os
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures/runs"
os.environ["SYNTHRANGE_RUNS_ROOTS"] = str(FIXTURE)

from fastapi.testclient import TestClient
from observer_ui.app import _markdown_to_html, app

client = TestClient(app)


def test_status_api():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "read_only_observer_files"
    assert "no SSH" in data["non_goals"]


def test_runs_page_loads():
    response = client.get("/runs")
    assert response.status_code == 200
    assert "sample-run" in response.text


def test_proxy_events_api():
    response = client.get("/api/runs/sample-run/proxy-events")
    assert response.status_code == 200
    assert any(event.get("red_action_id") == "sample-action" for event in response.json())


def test_markdown_renderer_escapes_raw_html():
    rendered = _markdown_to_html("# Report\n\n<script>alert('x')</script>")
    assert "<h1>Report</h1>" in rendered
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
