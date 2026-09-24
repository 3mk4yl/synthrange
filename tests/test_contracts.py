from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
TARGET_SCHEMA_PATH = ROOT / "schemas/target-adapter.schema.json"
PLAYBOOK_SCHEMA_PATH = ROOT / "schemas/playbook.schema.json"
RUN_BRIEF_SCHEMA_PATH = ROOT / "schemas/run-brief.schema.json"
RUN_STATE_SCHEMA_PATH = ROOT / "schemas/run-state.schema.json"
RUN_BRIEF_EXAMPLE_PATH = ROOT / "examples/runs/bounded-web-discovery.yaml"
RUN_STATE_EXAMPLE_PATH = ROOT / "examples/runs/run-state.created.json"
TARGET_MANIFESTS = sorted((ROOT / "targets").glob("*/target.yaml"))
PLAYBOOK_MANIFESTS = sorted((ROOT / "playbooks").glob("*/*/playbook.yaml"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def target_documents() -> list[tuple[Path, dict]]:
    return [(path, load_yaml(path)) for path in TARGET_MANIFESTS]


def playbook_documents() -> list[tuple[Path, dict]]:
    return [(path, load_yaml(path)) for path in PLAYBOOK_MANIFESTS]


def test_contract_schemas_are_valid_draft_2020_12():
    jsonschema.Draft202012Validator.check_schema(load_json(TARGET_SCHEMA_PATH))
    jsonschema.Draft202012Validator.check_schema(load_json(PLAYBOOK_SCHEMA_PATH))
    jsonschema.Draft202012Validator.check_schema(load_json(RUN_BRIEF_SCHEMA_PATH))
    jsonschema.Draft202012Validator.check_schema(load_json(RUN_STATE_SCHEMA_PATH))


def test_run_examples_validate_and_resolve_contract_references():
    run_brief = load_yaml(RUN_BRIEF_EXAMPLE_PATH)
    run_state = load_json(RUN_STATE_EXAMPLE_PATH)
    jsonschema.Draft202012Validator(load_json(RUN_BRIEF_SCHEMA_PATH)).validate(run_brief)
    jsonschema.Draft202012Validator(load_json(RUN_STATE_SCHEMA_PATH)).validate(run_state)

    target_ids = {document["metadata"]["id"] for _, document in target_documents()}
    playbook_ids = {document["metadata"]["id"] for _, document in playbook_documents()}
    assert run_brief["spec"]["target"]["adapterId"] in target_ids
    assert set(run_brief["spec"]["playbooks"]) <= playbook_ids
    assert run_state["metadata"]["runId"] == run_brief["metadata"]["id"]


def test_run_brief_mechanically_bounds_web_traffic():
    policy = load_yaml(RUN_BRIEF_EXAMPLE_PATH)["spec"]["trafficPolicy"]
    assert policy["proxyRequired"] is True
    assert policy["allowedMethods"] == ["GET", "HEAD", "OPTIONS"]
    assert policy["sustainedRequestsPerSecond"] <= 1
    assert policy["burst"] <= 2
    assert policy["maxRequests"] <= 60


def test_run_brief_rejects_output_and_artifact_path_traversal():
    schema = load_json(RUN_BRIEF_SCHEMA_PATH)
    document = load_yaml(RUN_BRIEF_EXAMPLE_PATH)
    output_escape = copy.deepcopy(document)
    output_escape["spec"]["participants"]["red"]["requiredOutputs"] = ["red/../../outside"]
    artifact_escape = copy.deepcopy(document)
    artifact_escape["spec"]["evidence"]["requiredArtifacts"] = ["artifacts/../../outside"]
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(output_escape))
    assert list(validator.iter_errors(artifact_escape))


def test_run_state_schema_couples_sealed_state_and_evidence_flag():
    schema = load_json(RUN_STATE_SCHEMA_PATH)
    document = load_json(RUN_STATE_EXAMPLE_PATH)
    sealed_without_flag = copy.deepcopy(document)
    sealed_without_flag["status"]["state"] = "sealed"
    flag_without_sealed = copy.deepcopy(document)
    flag_without_sealed["status"]["evidenceSealed"] = True
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(sealed_without_flag))
    assert list(validator.iter_errors(flag_without_sealed))


def test_at_least_one_target_and_each_playbook_role_exist():
    assert TARGET_MANIFESTS
    roles = {document["spec"]["role"] for _, document in playbook_documents()}
    assert roles == {"red", "blue", "shared"}


def test_target_manifests_validate_and_reference_existing_entrypoints():
    validator = jsonschema.Draft202012Validator(load_json(TARGET_SCHEMA_PATH))
    for path, document in target_documents():
        validator.validate(document)
        entrypoint = path.parent / document["spec"]["deployment"]["entrypoint"]
        assert entrypoint.exists(), f"{path}: missing deployment entrypoint {entrypoint}"
        assert (path.parent / "README.md").exists(), f"{path}: missing adapter README"


def test_playbook_manifests_validate_and_match_their_role_directories():
    validator = jsonschema.Draft202012Validator(load_json(PLAYBOOK_SCHEMA_PATH))
    for path, document in playbook_documents():
        validator.validate(document)
        assert document["spec"]["role"] == path.parents[1].name
        assert (path.parent / "README.md").exists(), f"{path}: missing playbook README"


def test_manifest_ids_are_unique():
    target_ids = [document["metadata"]["id"] for _, document in target_documents()]
    playbook_ids = [document["metadata"]["id"] for _, document in playbook_documents()]
    assert len(target_ids) == len(set(target_ids))
    assert len(playbook_ids) == len(set(playbook_ids))


def test_playbook_composition_references_resolve():
    documents = {document["metadata"]["id"]: document for _, document in playbook_documents()}
    for playbook_id, document in documents.items():
        composition = document["spec"]["composition"]
        references = composition["requiresPlaybooks"] + composition["complements"]
        assert playbook_id not in references, f"{playbook_id}: self reference"
        missing = sorted(set(references) - documents.keys())
        assert not missing, f"{playbook_id}: unknown playbooks {missing}"


def test_every_available_playbook_matches_an_available_target():
    targets = [
        document
        for _, document in target_documents()
        if document["metadata"]["status"] == "available"
    ]
    assert targets
    for path, playbook in playbook_documents():
        if playbook["metadata"]["status"] != "available":
            continue
        required = set(playbook["spec"]["requires"]["targetCapabilities"])
        compatible = [
            target["metadata"]["id"]
            for target in targets
            if required <= set(target["spec"]["capabilities"])
        ]
        assert compatible, f"{path}: no available target exposes {sorted(required)}"


def test_juice_shop_supports_the_initial_playbook_set():
    juice_shop = next(
        document
        for _, document in target_documents()
        if document["metadata"]["id"] == "juice-shop"
    )
    capabilities = set(juice_shop["spec"]["capabilities"])
    expected = {
        "run-evidence-baseline",
        "web-activity-triage",
        "web-surface-discovery",
    }
    compatible = {
        document["metadata"]["id"]
        for _, document in playbook_documents()
        if set(document["spec"]["requires"]["targetCapabilities"]) <= capabilities
    }
    assert expected <= compatible
