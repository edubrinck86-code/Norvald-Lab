"""Criterion incidents are observer-only, idempotent and cannot validate original failures."""
import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.runtime import DemoProvider
from norvald_lab.storage import digest, seal, verify_experiment, write_once
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult


def settle(client):
    async def wait():
        await asyncio.gather(*set(client.app.state.jobs.values()))
    client.portal.call(wait)


def bad_demo(monkeypatch):
    original = DemoProvider.execute

    async def execute(self, request, model):
        if request.agent_id == "analista-2":
            return ExecutionResult(content="Resposta sem o bloco de contribuição.",
                                   tokens=0, duration_seconds=0, provider="demo", model=model)
        return await original(self, request, model)

    monkeypatch.setattr(DemoProvider, "execute", execute)


def source_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in (root / "experiments").rglob("*") if p.is_file()}


def test_auto_detection_persists_is_idempotent_and_keeps_raw(tmp_path, monkeypatch):
    bad_demo(monkeypatch)
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        res = client.post("/api/experiments", json=demo_spec("incident-auto"))
        assert res.status_code == 202
        settle(client)
        assert verify_experiment(tmp_path, "incident-auto")["valid"]
        initial = source_bytes(tmp_path)

        listed = client.get("/api/criteria/incidents?experiment_id=incident-auto")
        assert listed.status_code == 200
        issues = listed.json()
        assert len(issues) == 2
        assert {i["criterion_id"] for i in issues} == {
            "arof.contribution.usable", "arof.contribution.fully_valid"}
        assert all(i["observation_id"] and i["validator_code"] == "missing_block"
                   for i in issues)
        first = client.post("/api/experiments/incident-auto/criteria/reconcile")
        second = client.post("/api/experiments/incident-auto/criteria/reconcile")
        assert first.status_code == second.status_code == 200
        assert first.json()["opened"] == second.json()["opened"] == []
        assert first.json()["unchanged"] == second.json()["unchanged"] == 2

        check = client.get("/api/criteria/incidents/" + issues[0]["id"]).json()
        assert len(check["history"]) == 1
        assert check["history"][0]["event"] == "detected"
        assert check["recovery"]["action"] == "new_collection_review"
        assert not check["recovery"]["allowed"]
        assert check["recovery"]["original_still_unmet"]
        assert client.app.state.lab_operations.call(
            "lab.incidents.list", {"experiment_id": "incident-auto"}) == issues
        assert client.app.state.lab_operations.call(
            "lab.incident.get", {"incident_id": issues[0]["id"]})["id"] == issues[0]["id"]
        assert source_bytes(tmp_path) == initial

    with TestClient(create_app(tmp_path, enable_demo=True)) as reopened:
        assert len(reopened.get("/api/criteria/incidents?experiment_id=incident-auto").json()) == 2
        assert reopened.get("/api/criteria/incidents/not-real").status_code == 404
        assert reopened.get("/api/criteria/incidents?status=invalid").status_code == 422


def test_owner_decisions_and_origin_guards_are_audited(tmp_path, monkeypatch):
    bad_demo(monkeypatch)
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        assert client.post("/api/experiments", json=demo_spec("incident-decision")).status_code == 202
        settle(client)
        issue = client.get("/api/criteria/incidents?experiment_id=incident-decision").json()[0]
        uri = "/api/criteria/incidents/" + issue["id"]
        assert client.post(uri + "/acknowledge", json={"note": "Ok", "role": "bot"}).status_code == 422
        assert client.post(uri + "/acknowledge", json={"note": ""}).status_code == 422
        assert client.post(uri + "/acknowledge", json={"note": "Conferir"},
                           headers={"Origin": "https://untrusted.example"}).status_code == 403
        assert client.post("/api/experiments/incident-decision/criteria/reconcile",
                           headers={"Origin": "https://untrusted.example"}).status_code == 403
        first = client.post(uri + "/acknowledge", json={"note": "Falha original registrada."})
        assert first.status_code == 200 and first.json()["status"] == "acknowledged"
        assert len(first.json()["history"]) == 2
        repeated = client.post(uri + "/acknowledge", json={"note": "Falha original registrada."})
        assert repeated.status_code == 200 and len(repeated.json()["history"]) == 2
        escalated = client.post(uri + "/escalate", json={"note": "Requer decisão científica."})
        assert escalated.status_code == 200 and escalated.json()["status"] == "escalated"
        assert [e["event"] for e in escalated.json()["history"]] == [
            "detected", "acknowledged", "escalated"]
        assert escalated.json()["recovery"]["original_still_unmet"]


def test_separately_sealed_adjustment_revalidates_without_changing_original(tmp_path, monkeypatch):
    bad_demo(monkeypatch)
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        assert client.post("/api/experiments", json=demo_spec("incident-followup")).status_code == 202
        settle(client)
        originals = source_bytes(tmp_path)
        incident = next(i for i in client.get("/api/criteria/incidents").json()
                        if i["criterion_id"] == "arof.contribution.fully_valid")
        adjustment_id = "ajuste-teste-verificavel"
        directory = tmp_path / "observer" / "adjustments" / "incident-followup" / adjustment_id
        write_once(directory / "request.json", {
            "id": adjustment_id, "observation_id": incident["observation_id"],
            "source_integrity_sha256": digest(tmp_path / "experiments" / "incident-followup" / "integrity.json"),
            "created_at": "2026-10-15T12:00:00Z",
            "independent_sample": False,
        })
        write_once(directory / "result.json", {
            "status": "complete", "check": {"code": "usable", "usable": True, "fully_valid": True},
        })
        seal(directory)
        detail = client.get("/api/criteria/incidents/" + incident["id"]).json()
        status = detail["recovery"]["revalidations"]
        assert len(status) == 1
        assert status[0]["criterion_status"] == "met_in_adjustment"
        assert status[0]["source_link_verified"] and status[0]["integrity_verified"]
        assert not status[0]["independent_sample"]
        assert detail["recovery"]["original_still_unmet"]
        assert verify_experiment(tmp_path, "incident-followup")["valid"]
        assert source_bytes(tmp_path) == originals

        # A missing adjustment seal never establishes a successful revalidation.
        (directory / "integrity.json").unlink()
        incomplete = client.get("/api/criteria/incidents/" + incident["id"]).json()
        assert incomplete["recovery"]["revalidations"][0]["criterion_status"] == "not_evaluable"


def test_corrupted_original_blocks_recovery_but_keeps_audit(tmp_path, monkeypatch):
    bad_demo(monkeypatch)
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        client.post("/api/experiments", json=demo_spec("incident-tampered"))
        settle(client)
        incident = client.get("/api/criteria/incidents").json()[0]
        raw = next((tmp_path / "experiments" / "incident-tampered" / "raw").rglob("*.jsonl"))
        raw.write_text(raw.read_text().replace("Resposta", "Alterado"))
        outcome = client.get("/api/criteria/incidents/" + incident["id"])
        assert outcome.status_code == 200
        assert outcome.json()["recovery"]["action"] == "investigate_integrity"
        assert not outcome.json()["recovery"]["allowed"]
        assert outcome.json()["recovery"]["revalidations"] == []
        reconciled = client.post("/api/experiments/incident-tampered/criteria/reconcile").json()
        assert reconciled["status"] == "reconciled"
        assert len(reconciled["opened"]) == 1
        assert "lab.dataset.integrity" in {
            i["criterion_id"] for i in client.get("/api/criteria/incidents").json()}

def test_incomplete_run_is_not_mislabeled_complete(tmp_path, monkeypatch):
    original = DemoProvider.execute

    async def sometimes_fails(self, request, model):
        if request.agent_id == "analista-2":
            raise RuntimeError("Falha simulada de execução.")
        return await original(self, request, model)

    monkeypatch.setattr(DemoProvider, "execute", sometimes_fails)
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        response = client.post("/api/experiments", json=demo_spec("incident-incomplete"))
        assert response.status_code == 202
        settle(client)
        report = client.get("/api/experiments/incident-incomplete/criteria").json()
        assert next(c for c in report["evaluations"]
                    if c["criterion_id"] == "lab.experiment.complete")["status"] == "not_met"
        issues = client.get("/api/criteria/incidents?experiment_id=incident-incomplete").json()
        assert any(i["criterion_id"] == "lab.experiment.complete" and
                   i["validator_code"] == "incomplete" for i in issues)
        assert verify_experiment(tmp_path, "incident-incomplete")["valid"]


def test_live_recovery_proposes_preview_but_never_executes(tmp_path):
    from norvald_lab.criterion_recovery import recovery_plan

    class NoAdjustments:
        def list(self, _):
            return []

    incident = {
        "id": "ci-test", "status": "open", "experiment_id": "one",
        "criterion_id": "arof.contribution.fully_valid",
        "criterion_version": "1", "observation_id": "obs", "participant_id": "a",
        "run_id": "r0001", "validator_code": "partial",
    }
    report = {"evaluations": [
        {"criterion_id": "lab.dataset.integrity", "status": "met"},
        {"criterion_id": "lab.experiment.complete", "status": "met"},
        {"criterion_id": "arof.contribution.fully_valid", "criterion_version": "1",
         "status": "not_met",
         "evidence": {"observation_id": "obs", "participant_id": "a", "run_id": "r0001"}},
    ]}
    preview = recovery_plan(incident, report, NoAdjustments(), tmp_path, mode="live")
    assert preview["action"] == "preview_adjustment"
    assert preview["allowed"] is True
    assert preview["requires_approval"] is False
    assert preview["automatic"] is False
    assert preview["proposed_payload"]["observation_id"] == "obs"
    assert not (tmp_path / "experiments").exists()
    refused = recovery_plan(incident, report, NoAdjustments(), tmp_path, mode="demo")
    assert refused["action"] == "new_collection_review"
    assert not refused["allowed"]
