import asyncio
import json

from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.storage import verify_experiment


def settle(client):
    async def wait():
        await asyncio.gather(*set(client.app.state.jobs.values()))
    client.portal.call(wait)


def test_ui_demo_family_prepare_and_notebook_preserve_dataset(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        template = client.get("/api/demo-template").json()
        prepared = client.post("/api/prepare", json=template)
        assert prepared.status_code == 200
        assert len(prepared.json()["requests"]) == 3
        assert not (tmp_path / "experiments").exists()
        response = client.post("/api/demo")
        assert response.status_code == 202
        ids = response.json()["experiment_ids"]
        settle(client)
        observations = [client.get(f"/api/experiments/{expid}/observe").json() for expid in ids]
        assert [s["spec"]["condition"]["exposure"] for s in observations] == ["blind", "self", "exposed"]
        assert all(s["integrity"]["valid"] and not s["provisional"] for s in observations)
        assert all(len(s["records"]) == 3 and len(s["requests"]) == 3 for s in observations)
        index = client.get("/api/experiments").json()
        assert len(index) == 3 and index[-1]["synthetic"]
        assert {row["source_experiment_id"] for row in index if row["exposure"] != "blind"} == {ids[0]}
        source = observations[0]
        record = source["records"][0]
        excerpt = "Escolha simulada:"
        anchor = {"experiment_id": ids[0], "observation_id": record["observation_id"], "excerpt": excerpt}
        note = client.post("/api/notes", json={"title": "Minha hipótese", "content": "## Observação\n\nTexto", "anchor": anchor}).json()
        update = client.put("/api/notes/" + note["id"], json={"title": "Meu olhar", "content": "## Observação\n\n==Mudou== $N_{eff}$"})
        assert update.status_code == 200 and update.json()["anchor"] == anchor
        assert update.json()["created_at"] == note["created_at"]
        assert client.get("/api/notes").json()[0]["content"].endswith("$N_{eff}$")
        assert verify_experiment(tmp_path, ids[0])["valid"]  # notas nunca entram no seal
        assert not list((tmp_path / "experiments" / ids[0]).glob("*note*"))
        assert client.put("/api/notes/" + note["id"], json={"content": "", "anchor": None}).status_code == 422
        assert client.post("/api/notes", json={"anchor": dict(anchor, excerpt="Trecho inventado")}).status_code == 422
        moment = client.post("/api/notes", json={"anchor": {"experiment_id": ids[0], "event_index": 0}}).json()
        assert moment["anchor"]["event_index"] == 0
        assert client.post("/api/notes", json={"anchor": {"experiment_id": ids[0], "event_index": 900}}).status_code == 422
        assert client.delete("/api/notes/" + note["id"]).status_code == 204
        assert verify_experiment(tmp_path, ids[0])["valid"]
        derived = client.post("/api/derive", json={"source_id": ids[0], "experiment_id": "nova-condicao", "exposure": "self"})
        assert derived.status_code == 200
        assert derived.json()["task"] == source["spec"]["task"]
        assert not (tmp_path / "experiments/nova-condicao").exists()


def test_observer_blocks_tampered_closed_data_and_bad_paths(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        expid = client.post("/api/demo").json()["experiment_id"]
        settle(client)
        target = next((tmp_path / "experiments" / expid / "raw").rglob("*.jsonl"))
        target.write_text(target.read_text().replace("Escolha simulada", "Alteração manual"))
        snapshot = client.get(f"/api/experiments/{expid}/observe").json()
        assert not snapshot["integrity"]["valid"]
        assert not snapshot["records"] and not snapshot["requests"]
        assert client.post("/api/derive", json={"source_id": expid, "experiment_id": "alterada", "exposure": "exposed"}).status_code == 422
        assert client.put("/api/notes/bad!id", json={"content": "x"}).status_code == 422
        assert client.delete("/api/notes/bad!id").status_code == 400


def test_read_partial_live_events_without_inventing_rows(tmp_path):
    from norvald_lab.observer import read_jsonl
    path = tmp_path / "events.jsonl"
    path.write_text('{"event":"real"}\n{"event":"em construção"')
    assert read_jsonl(path, provisional=True) == [{"event": "real"}]
    path.write_text('{"event":\n{"event":"real"}\n')
    try:
        read_jsonl(path, provisional=True)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("Linha inválida no meio do arquivo não pode desaparecer.")


def test_preflight_failure_is_observable_without_a_fake_running_collection(tmp_path, monkeypatch):
    from norvald_lab.cli import demo_spec
    monkeypatch.delenv("LAB_TEST_MISSING_KEY", raising=False)
    spec = demo_spec("missing-credential")
    spec["mode"] = "live"
    spec["providers"] = {"simulador": {"kind": "openai", "credential_env": "LAB_TEST_MISSING_KEY"}}
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        assert client.post("/api/experiments", json=spec).status_code == 202
        settle(client)
        response = client.get("/api/experiments/missing-credential/observe")
        assert response.status_code == 409
        assert "LAB_TEST_MISSING_KEY" in response.json()["detail"]
        assert client.get("/api/experiments/missing-credential").json()["status"] == "failed"
        assert not (tmp_path / "experiments/missing-credential").exists()
