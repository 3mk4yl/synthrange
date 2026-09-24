from pathlib import Path

from observer_ui import readers

SAMPLE = Path(__file__).resolve().parent / "fixtures/runs"


def test_discovers_sample_run():
    runs = readers.list_runs((SAMPLE,))
    assert any(run.run_id == "sample-run" for run in runs)


def test_sample_run_summary_counts():
    run = readers.find_run((SAMPLE,), "sample-run")
    assert run is not None
    summary = readers.run_summary(run)
    assert summary["timeline_events"] == 1
    assert summary["proxy_events"] == 1
    assert summary["final_report"] is True
    assert summary["red_report"] is True
    assert summary["blue_report"] is True


def test_safe_file_rejects_escape():
    run = readers.find_run((SAMPLE,), "sample-run")
    assert run is not None
    try:
        readers.safe_file(run.path, "../../README.md")
    except ValueError:
        return
    raise AssertionError("expected ValueError")
