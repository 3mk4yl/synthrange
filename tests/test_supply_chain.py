from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SHA256_IMAGE = re.compile(r"^[^\s]+@sha256:[0-9a-f]{64}$")
PINNED_ACTION = re.compile(r"^[^\s]+@[0-9a-f]{40}$")


def test_compose_images_are_pinned_to_sha256_digests():
    manifests = sorted(ROOT.glob("targets/**/compose.y*ml"))
    assert manifests
    images: list[tuple[Path, str]] = []
    for path in manifests:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for service in (data.get("services") or {}).values():
            if "image" in service:
                images.append((path, str(service["image"])))
    assert images
    for path, image in images:
        assert SHA256_IMAGE.fullmatch(image), f"{path}: image is not digest-pinned"


def test_github_actions_are_immutable_and_checkout_drops_credentials():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    checkout_seen = False
    for job in jobs.values():
        for step in job.get("steps", []):
            action = step.get("uses")
            if not action:
                continue
            assert PINNED_ACTION.fullmatch(action.split(" #", 1)[0]), f"unpinned action: {action}"
            if action.startswith("actions/checkout@"):
                checkout_seen = True
                assert step.get("with", {}).get("persist-credentials") is False
    assert checkout_seen


def test_public_host_example_uses_documentation_addresses():
    text = (ROOT / "components/observer/config/hosts.env.example").read_text(encoding="utf-8")
    assert "192.0.2.10" in text
    assert not re.search(r"\b(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)", text)
