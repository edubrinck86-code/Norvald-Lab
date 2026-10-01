import asyncio
import hashlib

from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.storage import verify_experiment


def settle(client):
    async def wait():
        await asyncio.gather(*set(client.app.state.jobs.values()))
    client.portal.call(wait)


def block(id="primeiro", content="## Minha hipótese\n\n$N_{eff}$\n\nTexto."):
    return {"id": id, "title": "Hipótese", "content": content, "type": "Hipótese", "source_note": None}


def test_workbook_corpus_freezes_exact_markdown_and_preserves_dataset(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        expid = client.post("/api/demo").json()["experiment_id"]
        settle(client)
        book = client.post("/api/workbooks", json={"title": "Meu estudo", "blocks": [block()]}).json()
        capture = client.post(f'/api/workbooks/{book["id"]}/corpus', json={"revision": 1}).json()
        assert capture["sha256"] == hashlib.sha256(capture["document"]["text"].encode()).hexdigest()
        assert block()["content"] in capture["document"]["text"]
        spec = client.get("/api/demo-template").json()
        spec["documents"] = [capture["document"]]
        assert client.post("/api/prepare", json=spec).status_code == 200
        new_exp = client.post("/api/experiments", json=spec).json()["experiment_id"]
        settle(client)
        changed = client.put(f'/api/workbooks/{book["id"]}', json={"revision": 1, "title": "Meu estudo", "blocks": [block(content="Mudou depois da coleta.")]}).json()
        assert changed["revision"] == 2
        closed = client.get(f"/api/experiments/{new_exp}/observe").json()
        assert closed["spec"]["documents"] == [capture["document"]]
        assert verify_experiment(tmp_path, expid)["valid"] and verify_experiment(tmp_path, new_exp)["valid"]
        assert client.get("/api/workbooks").json()[0]["revision"] == 2


def test_revision_conflict_does_not_overwrite_or_export_stale_draft(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        book = client.post("/api/workbooks", json={"blocks": [block()]}).json()
        url = '/api/workbooks/' + book["id"]
        assert client.put(url, json={"revision": 1, "blocks": [block(content="Nova versão")]}).status_code == 200
        assert client.put(url, json={"revision": 1, "blocks": [block(content="Texto atrasado")]}).status_code == 409
        assert client.post(url + "/corpus", json={"revision": 1}).status_code == 409
        assert client.get(url).json()["blocks"][0]["content"] == "Nova versão"


def test_note_capture_remains_when_note_is_changed_or_removed(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        expid = client.post("/api/demo").json()["experiment_id"]
        settle(client)
        record = client.get(f"/api/experiments/{expid}/observe").json()["records"][0]
        anchor = {"experiment_id": expid, "observation_id": record["observation_id"], "excerpt": "Escolha simulada:"}
        note = client.post("/api/notes", json={"title": "Meu olhar", "content": "Anotação original", "anchor": anchor}).json()
        book = client.post("/api/workbooks", json={}).json()
        url = '/api/workbooks/' + book["id"]
        captured = client.post(url + "/capture-note", json={"revision": 1, "note_id": note["id"]}).json()
        source = captured["blocks"][0]["source_note"]
        assert source["content"] == note["content"] and source["anchor"] == anchor
        edited_block = {**captured["blocks"][0], "content": "Análise desenvolvida"}
        saved = client.put(url, json={"revision": 2, "blocks": [edited_block]}).json()
        assert saved["blocks"][0]["source_note"] == source
        assert client.put(url, json={"revision": 3, "blocks": [{**edited_block, "source_note": None}]}).status_code == 422
        client.put('/api/notes/' + note["id"], json={"content": "Nova anotação"})
        client.delete('/api/notes/' + note["id"])
        assert client.get(url).json()["blocks"][0]["source_note"] == source
        assert verify_experiment(tmp_path, expid)["valid"]
        assert not list((tmp_path / "experiments" / expid).glob("*workbook*"))


def test_workbook_rejects_fabricated_sources_invalid_blocks_and_paths(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        assert client.post("/api/workbooks", json={"blocks": [block(), block()]}).status_code == 422
        assert client.post("/api/workbooks", json={"blocks": [{**block(), "source_note": {"id": "inventada"}}]}).status_code == 422
        assert client.get("/api/workbooks/bad!id").status_code == 422
        book = client.post("/api/workbooks", json={"blocks": [block(), block("segundo", "Outra observação")]}).json()
        url = '/api/workbooks/' + book["id"]
        assert client.post(url + "/capture-note", json={"revision": 1, "note_id": "ausente"}).status_code == 404
        assert client.post(url + "/corpus", json={"revision": 1, "block_ids": ["ausente"]}).status_code == 422
        capture = client.post(url + "/corpus", json={"revision": 1, "block_ids": ["segundo"]}).json()
        assert capture["block_ids"] == ["segundo"] and "Outra observação" in capture["document"]["text"]
        assert "Minha hipótese" not in capture["document"]["text"]
