"""Owner approval applies only to destructive effects; no RAW deletion."""
import asyncio

from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.storage import verify_experiment


def test_destructive_exclusion_requires_specific_owner_confirmation(tmp_path):
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        spec = demo_spec("owner-exclusion")
        assert client.post("/api/experiments", json=spec).status_code == 202
        async def settle():
            await asyncio.gather(*list(client.app.state.jobs.values()))
        client.portal.call(settle)
        raw = {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
               if p.is_file()}
        assert verify_experiment(tmp_path, "owner-exclusion")["valid"]
        staged = client.post("/api/assistant/destructive/exclusion/plan",
                             json={"experiment_id": "owner-exclusion"})
        assert staged.status_code == 200, staged.text
        assert staged.json()["requires_owner_confirmation"]
        assert not staged.json()["raw_deleted"]
        request_id = staged.json()["request"]["id"]
        endpoint = "/api/assistant/destructive/requests/" + request_id + "/confirm"
        assert client.post(endpoint, json={
            "experiment_id": "owner-exclusion", "confirmed": False}).status_code == 409
        assert client.post(endpoint, json={
            "experiment_id": "wrong-experiment", "confirmed": True}).status_code == 409
        assert client.post(endpoint, json={
            "experiment_id": "owner-exclusion", "confirmed": True},
            headers={"Origin": "https://untrusted.invalid"}).status_code == 403
        assert client.get("/api/experiments") != []
        approved = client.post(endpoint, json={
            "experiment_id": "owner-exclusion", "confirmed": True})
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "executed"
        assert client.post(endpoint, json={
            "experiment_id": "owner-exclusion", "confirmed": True}).status_code == 409
        assert client.get("/api/experiments").json() == []
        assert client.post("/api/experiments/owner-exclusion/restore").status_code == 204
        assert client.get("/api/experiments").json()[0]["experiment_id"] == "owner-exclusion"
        assert verify_experiment(tmp_path, "owner-exclusion")["valid"]
        assert raw == {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
                       if p.is_file()}


def test_destructive_actions_unavailable_to_model_tools(tmp_path):
    from norvald_lab.assistant_tools import dispatch

    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        catalogue = client.app.state.lab_operations
        names = {item["name"] for item in dispatch(catalogue, "list_operations", {})["operations"]}
        assert not any("exclude" in name or "delete" in name or "destructive" in name
                       for name in names)
        assert "lab.experiment.plan" in names
        assert "lab.experiment.start" not in names
        assert client.post("/api/assistant/destructive/exclusion/plan",
                           json={"experiment_id": "../private"}).status_code in {404, 422}
