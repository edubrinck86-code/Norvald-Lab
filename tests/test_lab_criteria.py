"""The first Lab Assistant slice is read-only and cannot fix experimental evidence."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.criteria import evaluate_snapshot, evaluate_spec
from norvald_lab.lab_operations import build_read_catalogue
from norvald_lab.runner import ExperimentRunner


def by_id(result, criterion):
    return [item for item in result["evaluations"] if item["criterion_id"] == criterion]


def test_preflight_is_read_only_and_reports_errors(tmp_path):
    runner = ExperimentRunner(tmp_path)
    spec = demo_spec("draft-criteria")
    original = deepcopy(spec)
    ready = evaluate_spec(runner, spec)
    assert ready["overall"] == "met"
    assert ready["fingerprint"]
    assert by_id(ready, "lab.spec.preparation")[0]["evidence"]["planned_requests"] == len(spec["participants"])
    assert spec == original
    assert not (tmp_path / "experiments").exists()

    broken = deepcopy(spec)
    broken["repetitions"] = 0
    refused = evaluate_spec(runner, broken)
    assert refused["overall"] == "not_met"
    assert by_id(refused, "lab.spec.structure")[0]["code"] == "invalid_spec"
    assert by_id(refused, "lab.spec.preparation")[0]["status"] == "not_evaluable"
    assert not (tmp_path / "experiments").exists()


def test_snapshot_separates_usable_from_fully_valid():
    content = {"experiment_id": "b1", "status": "complete", "provisional": False,
               "integrity": {"valid": True, "issues": []},
               "spec": {"participants": [{"id": "p1"}], "repetitions": 1},
               "contribution_checks": [{"observation_id": "obs1", "participant_id": "p1",
                                        "run_id": "r0001", "code": "partial",
                                        "usable": True, "fully_valid": False,
                                        "declared_items": 2, "accepted_items": 2,
                                        "declared_relations": 1, "accepted_relations": 0,
                                        "rejected": [{"kind": "relation", "identifier": "r1",
                                                      "reason": "Not permitted."}]}]}
    result = evaluate_snapshot(content)
    assert result["overall"] == "not_met"
    assert by_id(result, "arof.contribution.coverage")[0]["status"] == "met"
    assert by_id(result, "arof.contribution.usable")[0]["status"] == "met"
    assert by_id(result, "arof.contribution.fully_valid")[0]["status"] == "not_met"
    assert by_id(result, "arof.contribution.fully_valid")[0]["evidence"]["validator_code"] == "partial"

    missing = deepcopy(content)
    missing["contribution_checks"] = []
    assert by_id(evaluate_snapshot(missing), "arof.contribution.coverage")[0]["status"] == "not_met"


def test_invalid_integrity_never_claims_valid_contribution():
    value = {"experiment_id": "broken", "status": "complete", "provisional": False,
             "integrity": {"valid": False, "issues": ["tampered"]},
             "spec": {"participants": [{"id": "p1"}], "repetitions": 1},
             "contribution_checks": [{"participant_id": "p1", "run_id": "r0001",
                                      "usable": True, "fully_valid": True}]}
    result = evaluate_snapshot(value)
    assert result["overall"] == "not_met"
    assert by_id(result, "lab.dataset.integrity")[0]["code"] == "integrity_failed"
    assert by_id(result, "arof.contribution.coverage")[0]["status"] == "not_evaluable"
    assert not by_id(result, "arof.contribution.usable")


def test_catalogue_is_whitelisted_and_validated(tmp_path):
    runner = ExperimentRunner(tmp_path)
    catalog = build_read_catalogue(runner, lambda: demo_spec("draft"), lambda expid: {"id": expid})
    assert {item["name"] for item in catalog.describe()} == {
        "lab.spec.template", "lab.spec.evaluate", "lab.experiment.criteria"}
    assert catalog.call("lab.spec.template")["experiment_id"] == "draft"
    assert catalog.call("lab.experiment.criteria", {"experiment_id": "b1"}) == {"id": "b1"}
    with pytest.raises(ValueError, match="Unknown or unauthorized"):
        catalog.call("lab.experiment.start", {"spec": {}})
    with pytest.raises(ValidationError):
        catalog.call("lab.experiment.criteria", {"experiment_id": "b1", "extra": "forbidden"})
    with pytest.raises(ValidationError):
        catalog.call("lab.spec.evaluate", {"spec": "not a dict"})


def test_http_criteria_and_internal_catalogue(tmp_path):
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        spec = demo_spec("draft-http")
        response = client.post("/api/criteria/spec", json=spec)
        assert response.status_code == 200
        assert response.json()["overall"] == "met"
        assert not (tmp_path / "experiments").exists()
        assert client.get("/api/experiments/missing/criteria").status_code == 404
        catalogue = client.app.state.lab_operations
        assert catalogue.call("lab.spec.evaluate", {"spec": spec})["overall"] == "met"
        assert not (tmp_path / "experiments").exists()

@pytest.mark.asyncio
async def test_finished_experiment_criteria_cannot_rewrite_raw(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec("original-criteria")), monitor_capacity=False)
    originals = {str(path): path.read_bytes()
                 for path in (tmp_path / "experiments").rglob("*") if path.is_file()}
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        result = client.get("/api/experiments/original-criteria/criteria")
        assert result.status_code == 200
        report = result.json()
        assert report["subject"]["experiment_id"] == "original-criteria"
        assert by_id(report, "lab.dataset.integrity")[0]["status"] == "met"
        assert by_id(report, "arof.contribution.coverage")[0]["status"] == "met"
        assert len(by_id(report, "arof.contribution.usable")) == 3
        assert not by_id(report, "arof.contribution.coverage")[0]["evidence"]["missing"]
        assert client.get("/api/experiments/original-criteria/criteria",
                          headers={"Origin": "https://untrusted.example"}).status_code == 403
        assert client.post("/api/criteria/spec", json=demo_spec("untrusted"),
                           headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert originals == {str(path): path.read_bytes()
                         for path in (tmp_path / "experiments").rglob("*") if path.is_file()}
