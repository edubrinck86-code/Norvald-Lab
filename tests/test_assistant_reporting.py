"""Internal report provenance and conservative restart recovery."""
import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.assistant_automation import LabAutomation, iso, utc
from norvald_lab.assistant_plans import AssistantPlans, _sha
from norvald_lab.cli import demo_spec
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from datetime import timedelta


@pytest.mark.asyncio
async def test_internal_report_references_only_verified_dataset(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec("report-evidence")),
                     monitor_capacity=False)
    originals = {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
                 if p.is_file()}
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        report = client.get("/api/assistant/reports/report-evidence")
        assert report.status_code == 200, report.text
        data = report.json()
        assert data["schema_version"] == "norvald.lab.report.v1"
        assert data["provenance"]["integrity_valid"] is True
        assert data["summary"]["responses"] == 3
        assert data["design"]["repetitions"] == 1
        assert len(data["observations"]) == 3
        assert all("content" not in item for item in data["observations"])
        report_operation = client.app.state.lab_operations.call(
            "lab.experiment.report", {"experiment_id": "report-evidence"})
        assert report_operation["provenance"]["integrity_sha256"] == data["provenance"]["integrity_sha256"]
        assert report_operation["limitations"]
    assert originals == {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
                         if p.is_file()}

    raw = next((tmp_path / "experiments" / "report-evidence" / "raw").rglob("*.jsonl"))
    raw.write_text(raw.read_text() + "\n")
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        assert client.get("/api/assistant/reports/report-evidence").status_code == 409


def test_restart_marks_unknown_side_effects_interrupted_without_relaunch(tmp_path):
    plans = AssistantPlans(tmp_path)
    spec = demo_spec("interrupted-spec")
    plan = plans.create(action="lab.experiment.start",
                        experiment_id=spec["experiment_id"],
                        payload={"spec": spec}, evidence_sha256=_sha(spec))
    plans.claim(plan["id"], evidence_sha256=_sha(spec))
    routine = LabAutomation(tmp_path)
    configured = routine.schedule(ExperimentRunner(tmp_path),
                                  demo_spec("interrupted-routine"), 60,
                                  iso(utc() + timedelta(minutes=1)))
    occurrence = routine.claim_due(now=utc() + timedelta(minutes=2))
    assert occurrence and len(routine.history(configured["id"])) == 1
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        recovered = client.get("/api/assistant/plans/" + plan["id"]).json()
        assert recovered["status"] == "interrupted"
        assert recovered["result"]["reason"]
        assert client.get("/api/assistant/routines/" + configured["id"] + "/history").json()[0]["status"] == "interrupted"
        assert client.post("/api/assistant/plans/" + plan["id"] + "/execute",
                           json={}).json()["new_execution"] is False
        assert not (tmp_path / "experiments").exists()
