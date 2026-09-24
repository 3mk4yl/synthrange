from mitmproxy import http, ctx
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synthrange_policy import RunTrafficPolicy


def _csv_env(name, default=""):
    return {x.strip() for x in os.environ.get(name, default).split(",") if x.strip()}


def _int_csv_env(name, default=""):
    out = set()
    for x in _csv_env(name, default):
        try:
            out.add(int(x))
        except ValueError:
            pass
    return out


def _bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class SynthRangeJsonlLogger:
    def __init__(self):
        self.log_path = os.environ.get("LOG_PATH", "/srv/synthrange-traffic-proxy/logs/proxy-events.jsonl")
        self.run_id = os.environ.get("RUN_ID", "prep")
        self.allowed_hosts = _csv_env("TARGET_ALLOW_HOSTS")
        self.allowed_ports = _int_csv_env("TARGET_ALLOW_PORTS", "3000,80,443")
        self.red_source_ips = _csv_env("RED_SOURCE_IPS")
        self.require_run_id = _bool_env("REQUIRE_RUN_ID", True)
        if not self.allowed_hosts:
            raise ValueError("TARGET_ALLOW_HOSTS must name at least one approved target")
        self.policy = RunTrafficPolicy(
            allowed_methods=_csv_env("ALLOWED_METHODS", "GET,HEAD,OPTIONS"),
            max_requests=int(os.environ.get("MAX_REQUESTS_PER_RUN", "60")),
            requests_per_second=float(os.environ.get("RATE_LIMIT_REQUESTS_PER_SECOND", "1")),
            burst=int(os.environ.get("RATE_LIMIT_BURST", "2")),
            require_run_id=self.require_run_id,
            expected_run_id=self.run_id if self.require_run_id else None,
        )
        self.redact_headers = {h.lower() for h in [
            "authorization", "cookie", "set-cookie", "proxy-authorization", "x-api-key"
        ]}
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self._restore_policy_state()

    def _restore_policy_state(self):
        path = self.log_path
        if not os.path.isfile(path):
            return
        accepted_watermark = 0
        legacy_accepted = 0
        sources = set()
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid Proxy evidence at {path}:{line_number}: {error}") from error
                if event.get("run_id") != self.run_id:
                    continue
                recorded = event.get("accepted_requests")
                if isinstance(recorded, int):
                    accepted_watermark = max(accepted_watermark, recorded)
                    sources.add(event.get("source_ip", ""))
                elif event.get("event_type") == "request_response":
                    legacy_accepted += 1
                    sources.add(event.get("source_ip", ""))
        accepted = max(accepted_watermark, legacy_accepted)
        for source in sources or {""}:
            self.policy.restore(self.run_id, source, accepted)
        if accepted:
            ctx.log.info(f"restored SynthRange budget state run={self.run_id} accepted={accepted}")

    def _client_peer(self, flow):
        try:
            peer = flow.client_conn.peername
            if peer:
                return peer[0], peer[1]
        except Exception:
            pass
        return "", None

    def request(self, flow: http.HTTPFlow):
        flow.metadata["sr_request_started"] = time.time()
        host = flow.request.host
        port = int(flow.request.port or 0)
        if self.allowed_hosts and host not in self.allowed_hosts:
            flow.metadata["sr_blocked"] = True
            flow.response = http.Response.make(
                403,
                b"SynthRange traffic proxy: target host out of scope\n",
                {"content-type": "text/plain"},
            )
            self._write(flow, "blocked", summary=f"blocked host {host}:{port}")
            return
        if self.allowed_ports and port not in self.allowed_ports:
            flow.metadata["sr_blocked"] = True
            flow.response = http.Response.make(
                403,
                b"SynthRange traffic proxy: target port out of scope\n",
                {"content-type": "text/plain"},
            )
            self._write(flow, "blocked", summary=f"blocked port {host}:{port}")
            return
        client_ip, _ = self._client_peer(flow)
        header_run_id = flow.request.headers.get("x-synthrange-run-id", "")
        run_id = header_run_id or ("" if self.require_run_id else self.run_id)
        decision = self.policy.evaluate(run_id, client_ip, flow.request.method)
        flow.metadata["sr_policy_reason"] = decision.reason
        flow.metadata["sr_accepted_requests"] = decision.accepted_requests
        if not decision.allowed:
            flow.metadata["sr_blocked"] = True
            flow.response = http.Response.make(
                decision.status_code,
                f"SynthRange traffic proxy: {decision.reason}\n".encode(),
                {"content-type": "text/plain"},
            )
            self._write(flow, "blocked", summary=decision.reason)
            return

    def response(self, flow: http.HTTPFlow):
        if flow.metadata.get("sr_blocked"):
            return
        self._write(flow, "request_response")

    def error(self, flow: http.HTTPFlow):
        self._write(flow, "error", summary=str(flow.error) if flow.error else "unknown proxy error")

    def _headers_meta(self, headers):
        safe = {}
        redacted = []
        for k, v in headers.items(multi=True):
            lk = k.lower()
            if lk in self.redact_headers:
                redacted.append(k)
            elif lk in {"user-agent", "content-type", "accept", "host"}:
                safe[k] = v[:200]
        return safe, sorted(set(redacted))

    def _body_hash(self, content):
        if not content:
            return ""
        return "sha256:" + hashlib.sha256(content).hexdigest()

    def _write(self, flow: http.HTTPFlow, event_type: str, summary: str = ""):
        req = flow.request
        resp = flow.response
        started = flow.metadata.get("sr_request_started")
        duration_ms = round((time.time() - started) * 1000, 2) if started else None
        request_headers, request_redacted = self._headers_meta(req.headers)
        response_headers, response_redacted = self._headers_meta(resp.headers) if resp else ({}, [])
        client_ip, client_port = self._client_peer(flow)
        header_run_id = req.headers.get("x-synthrange-run-id", "")
        run_id = header_run_id or ("" if self.require_run_id else self.run_id)
        policy_reason = flow.metadata.get("sr_policy_reason", "")
        event = {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "component": "traffic-proxy",
            "event_type": event_type,
            "run_id": run_id,
            "source_host": "red-agent" if client_ip in self.red_source_ips else "unknown",
            "source_ip": client_ip,
            "source_port": client_port,
            "target_host": req.host,
            "target_ip": req.host,
            "target_port": req.port,
            "method": req.method,
            "scheme": req.scheme,
            "host": req.host_header,
            "path": req.path,
            "status": resp.status_code if resp else None,
            "request_bytes": len(req.raw_content or b""),
            "response_bytes": len(resp.raw_content or b"") if resp else 0,
            "duration_ms": duration_ms,
            "request_body_hash": self._body_hash(req.raw_content),
            "response_body_hash": self._body_hash(resp.raw_content) if resp else "",
            "request_headers": request_headers,
            "response_headers": response_headers,
            "redacted_headers": sorted(set(request_redacted + response_redacted)),
            "red_action_id": req.headers.get("x-synthrange-action-id", ""),
            "mitre_technique": req.headers.get("x-mitre-technique", ""),
            "summary": summary,
            "policy_reason": policy_reason,
            "accepted_requests": flow.metadata.get("sr_accepted_requests"),
            "scope_status": (
                "in_scope"
                if event_type != "blocked"
                else "out_of_scope_blocked"
                if not policy_reason
                else "policy_blocked"
            ),
        }
        line = json.dumps(event, sort_keys=True, separators=(",", ":"))
        directory = os.path.dirname(self.log_path)
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".proxy-event-", dir=directory, text=True)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(line + "\n")
            with open(self.log_path, "a") as out, open(tmp) as inp:
                out.write(inp.read())
        finally:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
        ctx.log.info(f"synthrange event {event_type} {req.method} {req.pretty_url} -> {event.get('status')}")


addons = [SynthRangeJsonlLogger()]
