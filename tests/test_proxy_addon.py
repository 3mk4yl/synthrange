from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON_PATH = ROOT / "components/traffic-proxy/addon/synthrange_jsonl_addon.py"


class Headers(dict):
    def items(self, multi=False):
        return super().items()


class FakeResponse:
    @staticmethod
    def make(status_code, content, headers):
        return types.SimpleNamespace(
            status_code=status_code,
            raw_content=content,
            headers=Headers(headers),
        )


class FakeLog:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)


def flow(run_id: str, *, method: str = "GET", host: str = "target.example"):
    request = types.SimpleNamespace(
        host=host,
        port=3000,
        method=method,
        headers=Headers({"x-synthrange-run-id": run_id, "host": f"{host}:3000"}),
        raw_content=b"",
        scheme="http",
        host_header=f"{host}:3000",
        path="/",
        pretty_url=f"http://{host}:3000/",
    )
    return types.SimpleNamespace(
        request=request,
        response=None,
        error=None,
        metadata={},
        client_conn=types.SimpleNamespace(peername=("198.51.100.10", 40000)),
    )


def load_addon(monkeypatch, log_path: Path):
    fake_log = FakeLog()
    fake_http = types.SimpleNamespace(HTTPFlow=object, Response=FakeResponse)
    fake_mitmproxy = types.ModuleType("mitmproxy")
    setattr(fake_mitmproxy, "http", fake_http)
    setattr(fake_mitmproxy, "ctx", types.SimpleNamespace(log=fake_log))
    monkeypatch.setitem(sys.modules, "mitmproxy", fake_mitmproxy)
    monkeypatch.setenv("LOG_PATH", str(log_path))
    monkeypatch.setenv("RUN_ID", "run-1")
    monkeypatch.setenv("TARGET_ALLOW_HOSTS", "target.example")
    monkeypatch.setenv("TARGET_ALLOW_PORTS", "3000")
    monkeypatch.setenv("RED_SOURCE_IPS", "198.51.100.10")
    monkeypatch.setenv("REQUIRE_RUN_ID", "true")
    monkeypatch.setenv("ALLOWED_METHODS", "GET,HEAD,OPTIONS")
    monkeypatch.setenv("MAX_REQUESTS_PER_RUN", "3")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_SECOND", "1")
    monkeypatch.setenv("RATE_LIMIT_BURST", "2")
    spec = importlib.util.spec_from_file_location("synthrange_addon_test", ADDON_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.addons[0], fake_log


def test_addon_binds_configured_run_restores_budget_and_logs_blocks(monkeypatch, tmp_path: Path):
    log_path = tmp_path / "proxy-events.jsonl"
    prior = [
        {"run_id": "run-1", "event_type": "request_response", "source_ip": "198.51.100.10"},
        {"run_id": "run-1", "event_type": "error", "source_ip": "198.51.100.10", "accepted_requests": 2},
    ]
    log_path.write_text("".join(json.dumps(event) + "\n" for event in prior), encoding="utf-8")
    addon, fake_log = load_addon(monkeypatch, log_path)
    assert any("restored SynthRange budget state" in message for message in fake_log.messages)

    mismatch = flow("run-2")
    addon.request(mismatch)
    assert mismatch.response.status_code == 403

    key = ("run-1", "198.51.100.10")
    addon.policy._buckets[key]["tokens"] = 1.0
    accepted = flow("run-1")
    addon.request(accepted)
    assert accepted.response is None
    accepted.response = FakeResponse.make(200, b"ok", {"content-type": "text/plain"})
    addon.response(accepted)

    exhausted = flow("run-1")
    addon.request(exhausted)
    assert exhausted.response.status_code == 429

    events = [json.loads(line) for line in log_path.read_text().splitlines()[2:]]
    assert [event["event_type"] for event in events] == ["blocked", "request_response", "blocked"]
    assert events[0]["policy_reason"] == "run_id_mismatch"
    assert events[1]["accepted_requests"] == 3
    assert events[2]["policy_reason"] == "request_budget_exhausted"
    assert all(event["source_host"] == "red-agent" for event in events)
