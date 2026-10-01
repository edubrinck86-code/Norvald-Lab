"""API e bancada local. A execução usa exatamente o mesmo serviço da CLI."""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from norvald_lab.config import identifier
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from norvald_lab.observer import NotebookStore, snapshot
from norvald_lab.workbook import WorkbookStore, RevisionConflict
from norvald_lab.cli import demo_spec, derive_spec
from uuid import uuid4


def create_app(root: str | Path | None = None, *, allow_live=False) -> FastAPI:
    root = Path(root).expanduser() if root is not None else arof_data_root()
    runner = ExperimentRunner(root)
    jobs = {}
    failures = {}
    notebook = NotebookStore(root)
    workbooks = WorkbookStore(root)

    @asynccontextmanager
    async def lifespan(app):
        yield
        tasks = list(jobs.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="Norvald Lab", version="0.2.0", lifespan=lifespan)
    app.state.jobs = jobs

    def directory(expid):
        try:
            identifier(expid)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return root / "experiments" / expid

    def read(path):
        if not path.exists():
            raise HTTPException(404, "Registro ainda não disponível.")
        return json.loads(path.read_text(encoding="utf-8"))

    @app.get("/health")
    def health():
        return {"status": "ok", "studio_required": False, "live_enabled": allow_live}

    @app.get("/api/experiments")
    def experiments():
        result = []
        for path in sorted((root / "experiments").glob("*/manifest.json")):
            final = path.parent / "result.json"
            spec = read(path.parent / "spec.json")
            result.append({"experiment_id": path.parent.name, "status": read(final)["status"] if final.exists() else "running" if path.parent.name in jobs else "unclosed", "task": spec["task"]["objective"], "exposure": spec["condition"]["exposure"], "source_experiment_id": spec["condition"].get("prior_experiment"), "synthetic": spec["mode"] == "demo"})
        return result

    @app.post("/api/prepare")
    def prepare(spec: dict):
        try:
            prepared = runner.prepare(spec)
            return {"spec": prepared.spec, "requests": [json.loads(r) for r in prepared.requests_json], "fingerprint": prepared.condition_fingerprint, "live_enabled": allow_live}
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/demo-template")
    def template():
        return demo_spec("experimento-" + uuid4().hex[:10])

    @app.post("/api/derive")
    def derive(payload: dict):
        try:
            exposure = payload["exposure"]
            if exposure not in {"self", "exposed"}:
                raise ValueError("Exposição deve ser self ou exposed.")
            spec = derive_spec(root, payload["source_id"], payload["experiment_id"], exposure)
            return runner.prepare(spec).spec
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/demo", status_code=202)
    async def demo():
        label = "demo-" + uuid4().hex[:12]
        ids = [label + suffix for suffix in ("-b1", "-b3", "-e")]
        async def suite():
            try:
                await runner.run(runner.prepare(demo_spec(ids[0])))
                for expid, exposure in zip(ids[1:], ("self", "exposed")):
                    await runner.run(runner.prepare(derive_spec(root, ids[0], expid, exposure)))
            except Exception as exc:
                failures[ids[0]] = str(exc)
            finally:
                for expid in ids:
                    jobs.pop(expid, None)
        task = asyncio.create_task(suite())
        for expid in ids:
            jobs[expid] = task
        return {"experiment_id": ids[0], "experiment_ids": ids, "status": "accepted"}

    @app.post("/api/experiments", status_code=202)
    async def execute(spec: dict):
        try:
            prepared = runner.prepare(spec)
            normalized = prepared.spec
            if normalized["mode"] == "live" and not allow_live:
                raise HTTPException(403, "Este backend está em modo demonstração. Inicie serve --live para APIs reais.")
            expid = normalized["experiment_id"]
            if expid in jobs or directory(expid).exists():
                raise HTTPException(409, "ID de experimento já utilizado.")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        async def run():
            try:
                await runner.run(prepared, allow_live=allow_live)
            except Exception as exc:
                failures[expid] = str(exc)
            finally:
                jobs.pop(expid, None)
        jobs[expid] = asyncio.create_task(run())
        return {"experiment_id": expid, "status": "accepted"}

    @app.get("/api/experiments/{experiment_id}")
    def experiment(experiment_id: str):
        target = directory(experiment_id)
        if (target / "result.json").exists():
            return read(target / "result.json")
        if experiment_id in failures:
            return {"experiment_id": experiment_id, "status": "failed", "error": failures[experiment_id]}
        if experiment_id in jobs:
            return {"experiment_id": experiment_id, "status": "running"}
        if (target / "manifest.json").exists():
            return {"experiment_id": experiment_id, "status": "unclosed"}
        raise HTTPException(404, "Experimento não encontrado.")

    @app.get("/api/experiments/{experiment_id}/manifest")
    def manifest(experiment_id: str):
        return read(directory(experiment_id) / "manifest.json")

    @app.get("/api/experiments/{experiment_id}/observe")
    def observe(experiment_id: str):
        directory(experiment_id)
        try:
            return snapshot(root, experiment_id, experiment(experiment_id)["status"])
        except FileNotFoundError as exc:
            if experiment_id in failures:
                raise HTTPException(409, "Coleta não iniciada: " + failures[experiment_id]) from exc
            raise HTTPException(404, "Experimento ainda não disponível.") from exc
        except (ValueError, KeyError) as exc:
            raise HTTPException(409, "Registro inconsistente; confira os arquivos originais.") from exc

    @app.get("/api/notes")
    def notes():
        return notebook.list()

    @app.post("/api/notes", status_code=201)
    def create_note(payload: dict):
        try:
            return notebook.save(payload)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.put("/api/notes/{note_id}")
    def save_note(note_id: str, payload: dict):
        try:
            return notebook.save(payload, note_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Nota não encontrada.") from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.delete("/api/notes/{note_id}", status_code=204)
    def delete_note(note_id: str):
        try:
            notebook.delete(note_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Nota não encontrada.") from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/experiments/{experiment_id}/verify")
    def verify(experiment_id: str):
        directory(experiment_id)
        try:
            return verify_experiment(root, experiment_id)
        except (OSError, ValueError) as exc:
            raise HTTPException(409, "Experimento sem fechamento verificável.") from exc

    def workbook_action(action):
        try:
            return action()
        except RevisionConflict as exc:
            raise HTTPException(409, str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(404, "Caderno ou nota não encontrado.") from exc
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/workbooks")
    def list_workbooks():
        return workbooks.list()

    @app.post("/api/workbooks", status_code=201)
    def create_workbook(payload: dict):
        return workbook_action(lambda: workbooks.save(payload))

    @app.get("/api/workbooks/{book_id}")
    def get_workbook(book_id: str):
        return workbook_action(lambda: workbooks.get(book_id))

    @app.put("/api/workbooks/{book_id}")
    def save_workbook(book_id: str, payload: dict):
        return workbook_action(lambda: workbooks.save(payload, book_id))

    @app.post("/api/workbooks/{book_id}/capture-note")
    def capture_note(book_id: str, payload: dict):
        return workbook_action(lambda: workbooks.capture_note(book_id, payload["note_id"], payload["revision"]))

    @app.post("/api/workbooks/{book_id}/corpus")
    def workbook_corpus(book_id: str, payload: dict):
        return workbook_action(lambda: workbooks.corpus(book_id, payload["revision"], payload.get("block_ids")))

    @app.get("/api/experiments/{experiment_id}/raw")
    def raw(experiment_id: str):
        target = directory(experiment_id)
        check = verify(experiment_id)
        if not check["valid"]:
            raise HTTPException(409, check)
        return [json.loads(line) for path in sorted((target / "raw").rglob("*.jsonl")) for line in path.read_text().splitlines() if line.strip()]

    web = Path(__file__).parent / "web"
    if (web / "assets").exists():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def index():
        if not (web / "index.html").exists():
            raise HTTPException(503, "Inicie ./scripts/start.sh para preparar e abrir a interface.")
        return FileResponse(web / "index.html")

    return app
