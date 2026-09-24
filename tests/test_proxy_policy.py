from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "components/traffic-proxy/addon/synthrange_policy.py"


def load_policy_module():
    spec = importlib.util.spec_from_file_location("synthrange_policy", POLICY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_policy(**overrides):
    module = load_policy_module()
    defaults = {
        "allowed_methods": {"GET", "HEAD", "OPTIONS"},
        "max_requests": 3,
        "requests_per_second": 1.0,
        "burst": 2,
        "require_run_id": True,
    }
    defaults.update(overrides)
    return module.RunTrafficPolicy(**defaults)


def test_policy_requires_run_id_and_rejects_forbidden_method():
    policy = make_policy()
    missing = policy.evaluate("", "red", "GET", now=0.0)
    forbidden = policy.evaluate("run-1", "red", "POST", now=0.0)
    assert (missing.allowed, missing.status_code, missing.reason) == (
        False,
        400,
        "missing_run_id",
    )
    assert (forbidden.allowed, forbidden.status_code, forbidden.reason) == (
        False,
        405,
        "method_not_allowed",
    )


def test_policy_rejects_a_different_run_id_before_budgeting():
    policy = make_policy(expected_run_id="run-1")
    mismatch = policy.evaluate("run-2", "red", "GET", now=0.0)
    assert (mismatch.allowed, mismatch.status_code, mismatch.reason) == (
        False,
        403,
        "run_id_mismatch",
    )
    assert policy.evaluate("run-1", "red", "GET", now=0.0).allowed


def test_policy_restores_budget_and_starts_restored_source_cold():
    policy = make_policy(max_requests=3, requests_per_second=1.0, burst=2, expected_run_id="run-1")
    policy.restore("run-1", "red", 2, now=10.0)
    cold = policy.evaluate("run-1", "red", "GET", now=10.0)
    assert not cold.allowed
    assert cold.reason == "rate_limited"
    assert policy.evaluate("run-1", "red", "GET", now=11.0).allowed
    exhausted = policy.evaluate("run-1", "red", "GET", now=12.0)
    assert not exhausted.allowed
    assert exhausted.reason == "request_budget_exhausted"


def test_policy_enforces_token_bucket_pacing():
    policy = make_policy(max_requests=10)
    assert policy.evaluate("run-1", "red", "GET", now=0.0).allowed
    assert policy.evaluate("run-1", "red", "GET", now=0.0).allowed
    limited = policy.evaluate("run-1", "red", "GET", now=0.0)
    assert not limited.allowed
    assert limited.status_code == 429
    assert limited.reason == "rate_limited"
    assert policy.evaluate("run-1", "red", "GET", now=1.0).allowed


def test_policy_enforces_accepted_request_budget():
    policy = make_policy(requests_per_second=100.0, burst=100)
    for index in range(3):
        assert policy.evaluate("run-1", "red", "GET", now=float(index)).allowed
    exhausted = policy.evaluate("run-1", "red", "GET", now=4.0)
    assert not exhausted.allowed
    assert exhausted.status_code == 429
    assert exhausted.reason == "request_budget_exhausted"
    assert exhausted.accepted_requests == 3


def test_policy_applies_budget_per_run_and_pacing_per_source():
    policy = make_policy(max_requests=2, requests_per_second=1.0, burst=1)
    assert policy.evaluate("run-1", "red-a", "GET", now=0.0).allowed
    assert not policy.evaluate("run-1", "red-a", "GET", now=0.0).allowed
    assert policy.evaluate("run-1", "red-b", "GET", now=0.0).allowed
    exhausted = policy.evaluate("run-1", "red-c", "GET", now=1.0)
    assert not exhausted.allowed
    assert exhausted.reason == "request_budget_exhausted"
    assert policy.evaluate("run-2", "red-a", "GET", now=0.0).allowed
