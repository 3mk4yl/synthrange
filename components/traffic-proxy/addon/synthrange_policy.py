from __future__ import annotations

import time
from collections.abc import Iterable


class PolicyDecision:
    def __init__(
        self,
        allowed: bool,
        status_code: int,
        reason: str,
        accepted_requests: int,
    ) -> None:
        self.allowed = allowed
        self.status_code = status_code
        self.reason = reason
        self.accepted_requests = accepted_requests


class RunTrafficPolicy:
    """Per-run/source method, token-bucket, and accepted-request enforcement."""

    def __init__(
        self,
        *,
        allowed_methods: Iterable[str],
        max_requests: int,
        requests_per_second: float,
        burst: int,
        require_run_id: bool = True,
        expected_run_id: str | None = None,
    ) -> None:
        methods = {method.upper() for method in allowed_methods}
        if not methods:
            raise ValueError("allowed_methods must not be empty")
        if max_requests < 1:
            raise ValueError("max_requests must be positive")
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if burst < 1:
            raise ValueError("burst must be positive")
        self.allowed_methods = methods
        self.max_requests = max_requests
        self.requests_per_second = requests_per_second
        self.burst = burst
        self.require_run_id = require_run_id
        self.expected_run_id = expected_run_id.strip() if expected_run_id else None
        self._buckets: dict[tuple[str, str], dict[str, float]] = {}
        self._accepted_by_run: dict[str, int] = {}

    def restore(self, run_id: str, source: str, accepted_requests: int, *, now: float | None = None) -> None:
        """Restore durable budget state from prior accepted Proxy events."""
        if accepted_requests < 0:
            raise ValueError("accepted_requests must not be negative")
        timestamp = time.monotonic() if now is None else now
        self._accepted_by_run[run_id] = max(
            self._accepted_by_run.get(run_id, 0),
            accepted_requests,
        )
        self._buckets[(run_id, source)] = {"tokens": 0.0, "last": timestamp}

    def evaluate(
        self,
        run_id: str,
        source: str,
        method: str,
        *,
        now: float | None = None,
    ) -> PolicyDecision:
        run_id = run_id.strip()
        method = method.upper()
        if self.require_run_id and not run_id:
            return PolicyDecision(False, 400, "missing_run_id", 0)
        if self.expected_run_id and run_id != self.expected_run_id:
            return PolicyDecision(False, 403, "run_id_mismatch", 0)
        if method not in self.allowed_methods:
            return PolicyDecision(False, 405, "method_not_allowed", 0)

        timestamp = time.monotonic() if now is None else now
        accepted = self._accepted_by_run.get(run_id, 0)
        if accepted >= self.max_requests:
            return PolicyDecision(
                False,
                429,
                "request_budget_exhausted",
                accepted,
            )

        key = (run_id, source)
        bucket = self._buckets.setdefault(
            key,
            {"tokens": float(self.burst), "last": timestamp},
        )
        elapsed = max(0.0, timestamp - bucket["last"])
        bucket["tokens"] = min(
            float(self.burst),
            bucket["tokens"] + elapsed * self.requests_per_second,
        )
        bucket["last"] = timestamp
        if bucket["tokens"] < 1.0:
            return PolicyDecision(False, 429, "rate_limited", accepted)

        bucket["tokens"] -= 1.0
        self._accepted_by_run[run_id] = accepted + 1
        return PolicyDecision(True, 0, "allowed", accepted + 1)
