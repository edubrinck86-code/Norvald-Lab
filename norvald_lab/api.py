"""API e bancada local. A execução usa exatamente o mesmo serviço da CLI."""
from __future__ import annotations

import asyncio
import json
import logging
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
from norvald_lab.criterion_incidents import CriterionIncidents
from norvald_lab.criterion_recovery import recovery_plan
from norvald_lab.lab_assistant import LabAssistant
from norvald_lab.assistant_design import draft_spec
from norvald_lab.assistant_comparison import compare_experiments
from norvald_lab.assistant_reports import experiment_report
from norvald_lab.assistant_plans import AssistantPlans, EmergencyStop
from norvald_lab.assistant_plan_routes import plan_router
from norvald_lab.assistant_automation import LabAutomation
from norvald_lab.assistant_destructive import DestructiveRequests
from norvald_lab.storage import digest
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
    incidents = CriterionIncidents(root)
    assistant = LabAssistant(root, local_settings)
    assistant_plans = AssistantPlans(root)
    automation = LabAutomation(root)
    destructive = DestructiveRequests(root, management)
    logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def lifespan(app):
        # Ambiguous actions from a prior process must be inspected, never replayed.
        assistant_plans.recover_interrupted()
        automation.recover_interrupted()
        async def observe_loop():
            # Local-only periodic reconciliation; outages never invalidate RAW.
            while True:
                await asyncio.sleep(10)
                try:
                    await app.state.automation_tick()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Falha no ciclo de observação automática do Lab")
        watcher = asyncio.create_task(observe_loop())
        yield
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
        tasks = list(jobs.values()) + list(adjustments.jobs.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="Norvald Lab", version="0.2.0", lifespan=lifespan)
    app.state.jobs = jobs
    app.state.adjustment_jobs = adjustments.jobs
    app.state.criterion_incidents = incidents
    app.state.lab_assistant = assistant
    app.state.assistant_plans = assistant_plans
    app.state.assistant_automation = automation
    from norvald_lab.google_account import GoogleAccount, account_router
    account = GoogleAccount(root, port=oauth_port)
    app.include_router(account_router(account))
    app.state.google_account = account

    @app.middleware("http")
    async def settings_origin(request: Request, call_next):
        protected = request.url.path.startswith(("/api/settings", "/api/models", "/api/adjustments", "/api/account/google", "/api/criteria", "/api/assistant")) or (
            request.url.path.startswith("/api/experiments/") and (
                request.url.path.endswith("/criteria") or request.url.path.endswith("/criteria/reconcile")))
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
                result = await runner.run(prepared, allow_live=authorized_live)
                # A failure in the auxiliary observer ledger never changes the
                # sealed experimental result or the success of the collection.
                try:
                    incidents.reconcile(expid, evaluate_snapshot(snapshot(root, expid, result["status"])))
                except Exception:
                    logger.exception("Falha ao registrar incidentes da coleta %s", expid)
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

    @app.post("/api/experiments/{experiment_id}/criteria/reconcile")
    def reconcile_experiment_criteria(experiment_id: str):
        """Explicit, idempotent persistence of violations; no LLM or RAW writes."""
        report = experiment_criteria(experiment_id)
        return incidents.reconcile(experiment_id, report)

    @app.get("/api/criteria/incidents")
    def list_criterion_incidents(experiment_id: str | None = None,
                                 status: str | None = None, limit: int = 100):
        try:
            return incidents.list(experiment_id=experiment_id, status=status, limit=limit)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    def incident_detail(incident_id: str):
        try:
            incident = incidents.get(incident_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        report = experiment_criteria(incident["experiment_id"])
        # If the source is not currently verified, a recovery plan is blocked.
        state = observe(incident["experiment_id"])
        mode = (state.get("spec") or {}).get("mode") if (
            (state.get("integrity") or {}).get("valid") and not state.get("provisional")) else None
        return incident | {"recovery": recovery_plan(incident, report, adjustments, root, mode=mode)}

    @app.get("/api/criteria/incidents/{incident_id}")
    def get_criterion_incident(incident_id: str):
        return incident_detail(incident_id)

    def record_owner_decision(incident_id: str, payload: dict, state: str):
        if not isinstance(payload, dict) or set(payload) != {"note"}:
            raise HTTPException(422, "Informe somente a justificativa da decisão.")
        try:
            incidents.mark(incident_id, status=state, note=payload["note"])
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return incident_detail(incident_id)

    @app.post("/api/criteria/incidents/{incident_id}/acknowledge")
    def acknowledge_criterion_incident(incident_id: str, payload: dict):
        return record_owner_decision(incident_id, payload, "acknowledged")

    @app.post("/api/criteria/incidents/{incident_id}/escalate")
    def escalate_criterion_incident(incident_id: str, payload: dict):
        return record_owner_decision(incident_id, payload, "escalated")

    @app.post("/api/assistant/spec/draft")
    async def assistant_draft_spec(payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"goal"}:
            raise HTTPException(422, "Informe somente goal.")
        if not execution_live:
            raise HTTPException(403, "Habilite o modelo operador para propor um Spec.")
        try:
            return await draft_spec(assistant=assistant, runner=runner,
                                    goal=payload["goal"], template=experiment_template(),
                                    emergency=assistant_plans)
        except PermissionError as exc:
            raise HTTPException(423, str(exc)) from exc
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc
        except Exception as exc:
            logger.exception("Falha na proposta de Spec pelo Assistant")
            raise HTTPException(502, "O modelo operador não conseguiu gerar a proposta.") from exc

    @app.get("/api/assistant/reports/{experiment_id}")
    def assistant_experiment_report(experiment_id: str):
        try:
            return experiment_report(root, experiment_id, incidents=incidents)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Experimento não encontrado.") from exc
        except (ValueError, KeyError, OSError, TypeError) as exc:
            raise HTTPException(409, local_settings.redact(str(exc))) from exc

    @app.get("/api/assistant/compare")
    def assistant_compare(left: str, right: str):
        try:
            return compare_experiments(root, left, right)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Um dos experimentos não está disponível.") from exc
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(409, local_settings.redact(str(exc))) from exc

    @app.get("/api/assistant/settings")
    def assistant_settings():
        return assistant.read_settings()

    @app.put("/api/assistant/settings")
    def save_assistant_settings(payload: dict):
        try:
            return assistant.save_settings(payload)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/assistant/conversation")
    def assistant_general_conversation():
        return {"messages": assistant.conversations.history("assistant-general",
                                                             limit=100000000)}

    @app.post("/api/assistant/chat")
    async def assistant_general_chat(payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"text"}:
            raise HTTPException(422, "Informe somente text.")
        try:
            return await assistant.general_reply(
                payload["text"], live_enabled=execution_live,
                catalogue=app.state.lab_operations, emergency=assistant_plans)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except EmergencyStop as exc:
            raise HTTPException(423, str(exc)) from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc
        except Exception as exc:
            logger.exception("Falha na conversa geral do Assistant")
            raise HTTPException(502, "O modelo operador falhou na conversa geral.") from exc

    @app.get("/api/assistant/incidents/{incident_id}/conversation")
    def assistant_conversation(incident_id: str):
        incident_detail(incident_id)  # Existing and accessible?
        return {"incident_id": incident_id,
                "messages": assistant.conversations.history(incident_id)}

    @app.post("/api/assistant/incidents/{incident_id}/message")
    async def assistant_message(incident_id: str, payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"text"}:
            raise HTTPException(422, "Informe somente text.")
        detail = incident_detail(incident_id)
        try:
            return await assistant.reply(
                detail, payload["text"], live_enabled=execution_live,
                catalogue=app.state.lab_operations, emergency=assistant_plans)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except EmergencyStop as exc:
            raise HTTPException(423, str(exc)) from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(422, local_settings.redact(str(exc))) from exc
        except Exception as exc:
            logger.exception("Não foi possível responder na conversa do Lab Assistant")
            raise HTTPException(502, "A resposta do modelo operador falhou. A pergunta não foi registrada.") from exc

    automation_router = plan_router(
        root, runner, adjustments, incidents, local_settings, incident_detail,
        execute, lambda: execution_live, logger, assistant_plans, automation, destructive)
    app.state.automation_tick = automation_router.tick
    app.include_router(automation_router)

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
        runner, experiment_template, experiment_criteria,
        list_incidents=incidents.list, get_incident=incident_detail,
        list_experiments=experiments, get_experiment_status=experiment,
        plan_experiment=lambda spec: automation_router.plan_experiment({"spec": spec}),
        plan_adjustment=lambda incident_id: automation_router.plan_adjustment(incident_id, {}),
        derive=lambda source_id, new_id, exposure: derive_spec(
            root, source_id, new_id, exposure),
        compare=lambda left, right: compare_experiments(root, left, right),
        execute_plan=lambda plan_id: automation_router.execute_plan(plan_id, {}),
        presented=assistant_plans.was_presented,
        report=lambda experiment_id: experiment_report(root, experiment_id, incidents=incidents))

    if not enable_demo:
        app.router.routes = [route for route in app.router.routes if getattr(route, "path", "") not in {"/api/demo", "/api/demo-template"}]
    return app
