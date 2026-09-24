from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COMMUNITY_FILES = {
    "LICENSE",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "ROADMAP.md",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/playbook.yml",
    ".github/ISSUE_TEMPLATE/target-adapter.yml",
}


def public_files() -> list[Path]:
    ignored = {".git", ".pytest_cache", "__pycache__", ".venv", "venv"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in ignored for part in path.parts)
    ]


def test_required_community_files_exist_and_are_nonempty():
    for relative in REQUIRED_COMMUNITY_FILES:
        path = ROOT / relative
        assert path.is_file(), f"missing community file: {relative}"
        assert path.stat().st_size > 0, f"empty community file: {relative}"


def test_apache_2_license_is_present():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "END OF TERMS AND CONDITIONS" in license_text


def test_github_yaml_is_parseable():
    for path in sorted((ROOT / ".github").rglob("*.yml")):
        assert yaml.safe_load(path.read_text(encoding="utf-8")) is not None, path


def test_relative_markdown_links_and_images_resolve():
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    errors = []
    for path in public_files():
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in pattern.finditer(text):
            target = match.group(1).split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "/")):
                continue
            if not (path.parent / target).resolve().exists():
                errors.append(f"{path.relative_to(ROOT)}: {target}")
    assert not errors, "broken relative links:\n" + "\n".join(errors)


def test_legacy_project_and_sequence_vocabulary_is_absent():
    forbidden = re.compile(
        r"BattleBots|BATTLEBOTS|battlebots|\bscenario\b|\bexercise(?:s|d)?\b",
        re.IGNORECASE,
    )
    violations = []
    for path in public_files():
        if path.resolve() in {Path(__file__).resolve(), (ROOT / "LICENSE").resolve()}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if forbidden.search(text):
            violations.append(str(path.relative_to(ROOT)))
    assert not violations, "legacy vocabulary found in:\n" + "\n".join(violations)


def test_first_run_lessons_and_architecture_decisions_are_present_and_sanitized():
    paths = [
        ROOT / "docs/lessons/first-real-run.md",
        *(ROOT / "docs/decisions").glob("*.md"),
    ]
    assert len(paths) == 5
    private_address = re.compile(
        r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not private_address.search(text), path


def test_hardened_runtime_scripts_are_executable():
    required = {
        "components/observer/scripts/sr-run-state",
        "components/observer/scripts/sr-approval",
        "components/observer/scripts/sr-blue-append-segment",
        "components/observer/scripts/sr-finalize-role",
        "components/observer/scripts/sr-lock-run",
        "components/observer/scripts/sr-validate-run-brief",
        "components/observer/scripts/sr-verify-required-artifacts",
        "components/observer/scripts/sr-archive-run",
        "components/traffic-proxy/scripts/sr-proxy-export-run",
        "scripts/dry-run-rehearsal.py",
    }
    for relative in required:
        path = ROOT / relative
        assert path.is_file(), relative
        assert path.stat().st_mode & 0o111, f"not executable: {relative}"


def test_collection_and_archive_regression_guards_are_present():
    collect = (ROOT / "components/observer/scripts/sr-collect").read_text(encoding="utf-8")
    archive = (ROOT / "components/observer/scripts/sr-archive-run").read_text(encoding="utf-8")
    assert "proxy-events-full" not in collect
    assert "sr-proxy-export-run" in collect
    assert "'$RUN_ID' '$SINCE' '$UNTIL'" in collect
    assert "--since '$SINCE' --until '$UNTIL'" in collect
    assert archive.index("run sealed") < archive.index("sr-index-artifacts") < archive.index("tar -C")
    assert "sr-event" not in archive
