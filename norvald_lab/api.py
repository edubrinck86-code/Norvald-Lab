"""API e bancada local. A execução usa exatamente o mesmo serviço da CLI."""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from norvald_lab.config import identifier
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from norvald_lab.observer import NotebookStore, snapshot
from norvald_lab.workbook import WorkbookStore, RevisionConflict
from norvald_lab.settings import LocalSettings
from norvald_lab.models import ModelCatalog
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.experiment_management import ExperimentManagement, experiment_template
from norvald_lab.adjustments import AdjustmentStore
from norvald_lab.criteria import evaluate_spec, evaluate_snapshot
from norvald_lab.lab_operations import build_read_catalogue
from uuid import uuid4


def create_app(root: str | Path | None = None, *, allow_live=False, enable_demo=False, oauth_port=8766) -> FastAPI:
    root = Path(root).expanduser() if root is not None else arof_data_root()
    runner = ExperimentRunner(root)
    local_settings = LocalSettings(root)
    catalog = ModelCatalog(local_settings)
    execution_live = bool(allow_live or local_settings.read()["live_enabled"])
    jobs = {}
    failures = {}
    notebook = NotebookStore(root)
    workbooks = WorkbookStore(root)
    management = ExperimentManagement(root)
    adjustments = AdjustmentStore(root)

    @asynccontextmanager
    async def lifespan(app):
        yield
        tasks = list(jobs.values()) + list(adjustments.jobs.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="Norvald Lab", version="0.2.0", lifespan=lifespan)
    app.state.jobs = jobs
    app.state.adjustment_jobs = adjustments.jobs
    from norvald_lab.google_account import GoogleAccount, account_router
    account = GoogleAccount(root, port=oauth_port)
    app.include_router(account_router(account))
    app.state.google_account = account

    @app.middleware("http")
    async def settings_origin(request: Request, call_next):
        protected = request.url.path.startswith(("/api/settings", "/api/models", "/api/adjustments", "/api/account/google", "/api/criteria")) or (
            request.url.path.startswith("/api/experiments/") and request.url.path.endswith("/criteria"))
        if protected and not request.url.path.endswith('/callback'):
            origin = request.headers.get("origin")
            if (origin and origin.rstrip("/") != str(request.base_url).rstrip("/")) or request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({"detail": "Configurações só aceitam pedidos da própria interface local."}, status_code=403)
        response = await call_next(request)
        if protected:
            response.headers["Cache-Control"] = "no-store"
        return response

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
        return {"status": "ok", "studio_required": False, "live_enabled": execution_live}

    @app.get("/api/experiments")
    def experiments(include_deleted: bool = False):
        result = []
        for path in sorted((root / "experiments").glob("*/manifest.json")):
            excluded = management.is_deleted(path.parent.name)
            if excluded and not include_deleted:
                continue
            final = path.parent / "result.json"
            spec = read(path.parent / "spec.json")
            if spec["mode"] == "demo" and not enable_demo:
                continue
            result.append({"deleted": excluded, "experiment_id": path.parent.name, "status": read(final)["status"] if final.exists() else "running" if path.parent.name in jobs else "unclosed", "task": spec["task"]["objective"], "exposure": spec["condition"]["exposure"], "source_experiment_id": spec["condition"].get("prior_experiment"), "synthetic": spec["mode"] == "demo"})
        return result

    @app.post("/api/prepare")
    def prepare(spec: dict):
        if spec.get("mode", "demo") != "live" and not enable_demo:
            raise HTTPException(422, "O laboratório aceita somente modelos reais.")
        try:
            prepared = runner.prepare(spec)
            return {"spec": prepared.spec, "requests": [json.loads(r) for r in prepared.requests_json], "fingerprint": prepared.condition_fingerprint, "live_enabled": execution_live}
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/criteria/spec")
    def inspect_spec_criteria(spec: dict):
        """Read-only preflight: a rejected criterion is a result, not a write."""
        return evaluate_spec(runner, spec)

    @app.get("/api/experiment-template")
    def empty_template():
        return experiment_template()

    @app.get("/api/demo-template")
    def template():
        if not enable_demo:
            raise HTTPException(404, "Demonstração removida do ambiente de uso.")
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
        if not enable_demo:
            raise HTTPException(404, "Demonstração removida do ambiente de uso.")
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
            if normalized["mode"] != "live" and not enable_demo:
                raise HTTPException(422, "O laboratório aceita somente modelos reais.")
            if normalized["mode"] == "live" and not execution_live:
                raise HTTPException(403, "Habilite chamadas reais em Configurações antes de iniciar.")
            expid = normalized["experiment_id"]
            if expid in jobs or directory(expid).exists():
                raise HTTPException(409, "ID de experimento já utilizado.")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        authorized_live = execution_live
        async def run():
            try:
                await runner.run(prepared, allow_live=authorized_live)
            except Exception as exc:
                failures[expid] = local_settings.redact(str(exc))
            finally:
                jobs.pop(expid, None)
        jobs[expid] = asyncio.create_task(run())
        return {"experiment_id": expid, "status": "accepted"}

    @app.get("/api/experiments/{experiment_id}/editable-copy")
    def editable_copy(experiment_id: str):
        directory(experiment_id)
        try:
            return management.editable_copy(experiment_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Experimento não encontrado.") from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.delete("/api/experiments/{experiment_id}", status_code=204)
    def exclude_experiment(experiment_id: str):
        directory(experiment_id)
        if experiment_id in jobs:
            raise HTTPException(409, "Aguarde o término da execução para excluir da lista.")
        try:
            management.exclude(experiment_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Experimento não encontrado.") from exc

    @app.post("/api/experiments/{experiment_id}/restore", status_code=204)
    def restore_experiment(experiment_id: str):
        directory(experiment_id)
        management.restore(experiment_id)

    @app.get("/api/adjustments/{experiment_id}")
    def list_adjustments(experiment_id: str):
        directory(experiment_id)
        try:
            return adjustments.list(experiment_id)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            raise HTTPException(409, "Histórico de ajustes inconsistente; confira os registros salvos.") from exc

    @app.post("/api/adjustments/{experiment_id}/preview")
    def preview_adjustment(experiment_id: str, payload: dict):
        directory(experiment_id)
        try:
            saved, _ = adjustments.prepare(experiment_id, payload, persist=False)
            return saved
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc

    @app.post("/api/adjustments/{experiment_id}", status_code=202)
    async def adjust_response(experiment_id: str, payload: dict):
        directory(experiment_id)
        if not execution_live:
            raise HTTPException(403, "Habilite chamadas reais em Configurações antes de pedir um ajuste.")
        try:
            saved, spec = adjustments.prepare(experiment_id, payload)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc
        adjustments.start(saved, spec)
        return {"id": saved["id"], "status": "accepted"}

    @app.get("/api/settings")
    def settings():
        return local_settings.public(live_enabled=execution_live)

    @app.put("/api/settings/connections/{kind}")
    def save_connection(kind: str, payload: dict):
        try:
            local_settings.save_connection(kind, payload)
            return local_settings.public(live_enabled=execution_live)
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, "Não foi possível salvar: " + str(exc)) from exc

    @app.delete("/api/settings/connections/{kind}/key")
    def delete_key(kind: str):
        try:
            local_settings.delete_key(kind)
            return local_settings.public(live_enabled=execution_live)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.put("/api/settings/execution")
    def set_execution(payload: dict):
        nonlocal execution_live
        try:
            local_settings.set_execution(payload["live_enabled"])
            execution_live = payload["live_enabled"]
            return local_settings.public(live_enabled=execution_live)
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, "Informe live_enabled como booleano.") from exc

    @app.post("/api/models")
    async def models(payload: dict):
        try:
            return await catalog.get(payload)
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc
        except Exception as exc:
            raise HTTPException(502, "Não foi possível consultar o catálogo. Confira a conexão, a chave e o endereço nas Configurações.") from exc

    @app.post("/api/settings/connections/{kind}/test")
    async def test_connection(kind: str):
        try:
            return await catalog.test(kind)
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc
        except Exception as exc:
            raise HTTPException(502, "Não foi possível verificar a conexão. Confira a chave, o endereço e tente novamente.") from exc

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

    @app.get("/api/experiments/{experiment_id}/criteria")
    def experiment_criteria(experiment_id: str):
        """Evaluate stored original observations without altering sealed data."""
        return evaluate_snapshot(observe(experiment_id))

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

    # Internal tool catalogue. Do not expose generic call_operation over HTTP
    # before an authenticated, authorized Assistant interface exists.
    app.state.lab_operations = build_read_catalogue(
        runner, experiment_template, experiment_criteria)

    if not enable_demo:
        app.router.routes = [route for route in app.router.routes if getattr(route, "path", "") not in {"/api/demo", "/api/demo-template"}]
    return app
