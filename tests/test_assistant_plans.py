"""Staged execution is idempotent; emergency loop control is not a usage quota."""
import asyncio

import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.assistant_plans import AssistantPlans, EmergencyStop
from norvald_lab.cli import demo_spec
from norvald_lab.storage import verify_experiment


def create(store, key="same", evidence="a" * 64):
    return store.create(
        action="lab.experiment.start", experiment_id="experiment-test",
        payload={"spec": {"step": key}}, evidence_sha256=evidence,
    )


def test_emergency_stops_only_repeated_automatic_cycles_and_persists(tmp_path):
    store = AssistantPlans(tmp_path)
    for number in range(3):
        row = create(store)
        claimed, fresh = store.claim(row["id"], evidence_sha256="a" * 64,
                                     automatic=True)
        assert fresh and claimed["status"] == "running"
        assert store.finish(row["id"], {"step": number})["status"] == "accepted"

    repeating = create(store)
    with pytest.raises(EmergencyStop, match="Loop"):
        store.claim(repeating["id"], evidence_sha256="a" * 64, automatic=True)
    assert store.control()["stopped"]
    assert store.get(repeating["id"])["status"] == "planned"
    after_restart = AssistantPlans(tmp_path)
    with pytest.raises(EmergencyStop):
        after_restart.claim(repeating["id"], evidence_sha256="a" * 64)
    assert not after_restart.resume()["stopped"]
    claimed, fresh = after_restart.claim(repeating["id"], evidence_sha256="a" * 64)
    assert fresh and claimed["status"] == "running"
    assert after_restart.claim(repeating["id"], evidence_sha256="a" * 64)[1] is False


def test_many_distinct_actions_do_not_trigger_a_quota(tmp_path):
    store = AssistantPlans(tmp_path)
    for number in range(40):
        row = create(store, key="distinct-" + str(number))
        store.claim(row["id"], evidence_sha256="a" * 64, automatic=True)
        store.finish(row["id"], {"ok": True})
    assert not store.control()["stopped"]
    stale = create(store)
    with pytest.raises(ValueError, match="evidência mudou"):
        store.claim(stale["id"], evidence_sha256="b" * 64)
    assert store.get(stale["id"])["status"] == "planned"


def test_experiment_plan_is_visible_before_execution_and_emergency_blocks(tmp_path):
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        spec = demo_spec("assistant-plan-study")
        planned = client.post("/api/assistant/plans/experiment", json={"spec": spec})
        assert planned.status_code == 200, planned.text
        response = planned.json()
        assert response["requires_approval"] is False
        assert response["planning"]["repetitions"] == 1
        assert response["planning"]["participants"]
        plan_id = response["plan"]["id"]
        assert not (tmp_path / "experiments").exists()

        url = "/api/assistant/plans/" + plan_id + "/execute"
        assert client.post(url, json={"mutated": True}).status_code == 422
        assert client.post(url, json={}, headers={"Origin": "https://foreign.invalid"}).status_code == 403

        assert client.post("/api/assistant/emergency/stop").json()["stopped"]
        assert client.post(url, json={}).status_code == 423
        assert not (tmp_path / "experiments").exists()
        assert not client.post("/api/assistant/emergency/resume").json()["stopped"]

        accepted = client.post(url, json={})
        assert accepted.status_code == 202, accepted.text
        assert accepted.json()["new_execution"] is True
        assert accepted.json()["result"]["experiment_id"] == spec["experiment_id"]
        async def settle():
            await asyncio.gather(*list(client.app.state.jobs.values()))
        client.portal.call(settle)
        assert verify_experiment(tmp_path, spec["experiment_id"])["valid"]
        duplicate = client.post(url, json={})
        assert duplicate.status_code == 202
        assert duplicate.json()["new_execution"] is False
        assert client.get("/api/assistant/plans/" + plan_id).json()["status"] == "accepted"
