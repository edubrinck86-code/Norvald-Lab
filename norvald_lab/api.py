"""API local sem UI. A execução usa exatamente o mesmo serviço da CLI."""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from norvald_lab.config import identifier
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment


def create_app(root: str | Path | None = None, *, allow_live=False) -> FastAPI:
    root = Path(root).expanduser() if root is not None else arof_data_root()
    runner = ExperimentRunner(root)
    jobs = {}
    failures = {}

    @asynccontextmanager
    async def lifespan(app):
        yield
        tasks = list(jobs.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="Norvald Lab", version="0.1.0", lifespan=lifespan)
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
            result.append({"experiment_id": path.parent.name, "status": read(final)["status"] if final.exists() else "running" if path.parent.name in jobs else "unclosed"})
        return result

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

    @app.get("/api/experiments/{experiment_id}/verify")
    def verify(experiment_id: str):
        directory(experiment_id)
        try:
            return verify_experiment(root, experiment_id)
        except (OSError, ValueError) as exc:
            raise HTTPException(409, "Experimento sem fechamento verificável.") from exc

    @app.get("/api/experiments/{experiment_id}/raw")
    def raw(experiment_id: str):
        target = directory(experiment_id)
        check = verify(experiment_id)
        if not check["valid"]:
            raise HTTPException(409, check)
        return [json.loads(line) for path in sorted((target / "raw").rglob("*.jsonl")) for line in path.read_text().splitlines() if line.strip()]

    return app
