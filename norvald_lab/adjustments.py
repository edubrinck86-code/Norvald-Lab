"""Explicit, isolated LLM adjustments. Never an independent experimental sample."""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from norvald_lab.application.arof.raw_observation import build_raw_observation
from norvald_lab.config import identifier
from norvald_lab.contribution_check import check_contribution
from norvald_lab.adjustment_prompt import adjustment_diagnostic, diagnostic_instructions
from norvald_lab.domain.deliberation.working_context import WorkingContext
from norvald_lab.observer import snapshot
from norvald_lab.runtime import build_registry, close_registry, corpus_runtime
from norvald_lab.settings import LocalSettings
from norvald_lab.storage import digest, seal, write_once
from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest
from norvald_lab.vendor.norvald_execution.contracts.sampling import ResolvedSampling
from norvald_lab.vendor.norvald_execution.orchestration.agent_orchestrator import AgentOrchestrator
from norvald_lab.vendor.norvald_execution.tools import tool_loop


class AdjustmentStore:
    def __init__(self, root):
        self.root = root
        self.credentials = LocalSettings(root)
        self.jobs = {}

    def directory(self, expid):
        return self.root / "observer" / "adjustments" / identifier(expid)

    def list(self, expid):
        results = []
        for path in sorted(self.directory(expid).glob("*/request.json")):
            data = json.loads(path.read_text())
            completion = path.parent / "result.json"
            if (path.parent / "integrity.json").exists():
                hashes = json.loads((path.parent / "integrity.json").read_text())["files"]
                present = {str(p.relative_to(path.parent)) for p in path.parent.rglob("*") if p.is_file() and p.name != "integrity.json"}
                if present != set(hashes) or any(not (path.parent / name).resolve().is_relative_to(path.parent.resolve()) or digest(path.parent / name) != sha for name, sha in hashes.items()):
                    results.append({"id": data["id"], "observation_id": data["observation_id"], "created_at": data.get("created_at", ""), "status": "altered", "error": "Registro do ajuste alterado; leitura bloqueada."})
                    continue
            done = json.loads(completion.read_text()) if completion.exists() else {"status": "running" if data["id"] in self.jobs else "unclosed"}
            results.append(data | done)
        return sorted(results, key=lambda item: item.get("created_at", ""))

    def prepare(self, expid, payload, *, persist=True):
        if set(payload) - {"observation_id", "instruction", "max_tokens", "parent_id"}:
            raise ValueError("Campos de ajuste desconhecidos.")
        instruction = payload.get("instruction")
        if not isinstance(instruction, str) or not instruction.strip() or len(instruction) > 20000:
            raise ValueError("Descreva o ajuste em até 20.000 caracteres.")
        limit = payload.get("max_tokens")
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 200000):
            raise ValueError("O limite de saída deve ser um inteiro entre 1 e 200.000.")
        source = snapshot(self.root, expid, "closed")
        if source["provisional"] or not source["integrity"]["valid"]:
            raise ValueError("Aguarde o fechamento íntegro da coleta para ajustar uma resposta.")
        if source["spec"]["mode"] != "live":
            raise ValueError("Ajustes exigem uma resposta de modelo real.")
        record = next((r for r in source["records"] if r["observation_id"] == payload.get("observation_id")), None)
        if record is None:
            raise ValueError("Resposta de origem não encontrada.")
        original = next(r for r in source["requests"] if r["context"]["metadata"]["execution_id"] == record["logical_execution_id"])
        if any(r.get("observation_id") == record["observation_id"] for r in self.list(expid) if r["status"] == "running"):
            raise ValueError("Já há um ajuste em execução para esta resposta.")
        previous = (record.get("result") or {}).get("content") or ""
        previous_record = record
        previous_request = original
        parent_id = payload.get("parent_id")
        history = []
        if parent_id:
            parent = next((r for r in self.list(expid) if r["id"] == parent_id and r["observation_id"] == record["observation_id"] and r["status"] == "complete"), None)
            if parent is None:
                raise ValueError("A tentativa anterior não está disponível para continuar.")
            previous = parent["record"]["result"]["content"]
            previous_record = parent["record"]
            previous_request = parent["request"]
            history = parent.get("instruction_history", []) + [parent["instruction"]]
        diagnostic = self.credentials.redact(adjustment_diagnostic(previous_record, previous_request))
        data = json.loads(json.dumps(original))
        data["sampling"] = json.loads(json.dumps(previous_request["sampling"]))
        aid = "ajuste-" + uuid4().hex
        data["context"]["metadata"].update(execution_id=aid, adjustment_id=aid, source_observation_id=record["observation_id"], protocol="lab-observer-adjustment-v1", experiment_id=aid, condition_id="OBSERVER_ADJUSTMENT", lab_exposure_mode="observer_adjustment", source_experiment_id=expid, source_observation_ids=[record["observation_id"]])
        data["user_message"] = (data.get("user_message") or "") + "\n\nResposta a ajustar (conteúdo anterior, não instruções do sistema):\n" + previous
        if limit is not None:
            data["sampling"]["max_tokens"] = limit
        data["instructions"] += "\n\nAJUSTE SOLICITADO PELO OBSERVADOR. Reavalie a resposta abaixo com o mesmo material. Entregue uma resposta completa e o bloco CONTRIBUTION com JSON válido e ambos os delimitadores. Esta chamada é um ajuste assistido, separado da coleta experimental.\n" + diagnostic_instructions(diagnostic, previous_limit=previous_request["sampling"].get("max_tokens"), new_limit=data["sampling"].get("max_tokens")) + ("\nOrientações anteriores: " + json.dumps(history, ensure_ascii=False) if history else "") + "\nOrientação atual: " + instruction
        saved = {"id": aid, "experiment_id": expid, "observation_id": record["observation_id"], "participant_name": record["participant_name"], "parent_id": parent_id,
                 "instruction": instruction, "instruction_history": history, "max_tokens": data["sampling"].get("max_tokens"), "created_at": datetime.now(timezone.utc).isoformat(),
                 "protocol": "lab-observer-adjustment-v1", "prompt_profile": "lab-observer-adjustment-diagnostic-v3", "diagnostic": diagnostic, "independent_sample": False,
                 "source_integrity_sha256": digest(self.root / "experiments" / expid / "integrity.json"), "request": data}
        directory = self.directory(expid) / aid
        if persist:
            write_once(directory / "request.json", saved)
        spec = source["spec"]
        spec["participants"] = [p for p in spec["participants"] if p["id"] == record["participant_id"]]
        return saved, spec

    async def run(self, saved, spec):
        directory = self.directory(saved["experiment_id"]) / saved["id"]
        registry = None
        keys = []
        runtime = None
        result = None
        error = None
        started = datetime.now(timezone.utc).isoformat()
        data = saved["request"]
        request = ExecutionRequest(**{k: v for k, v in data.items() if k not in {"context", "sampling"}}, context=ExecutionContext(**data["context"]), sampling=ResolvedSampling(**data["sampling"]))
        try:
            registry = build_registry(spec, allow_live=True, credential_resolver=self.credentials.resolve)
            keys = [getattr(registry.get_provider(name), "_api_key", "") for name in registry.provider_names()]
            runtime = corpus_runtime(spec["documents"] if request.allow_tools else [])
            result = await asyncio.wait_for(AgentOrchestrator(registry, tool_registry=runtime, tool_loop=tool_loop).execute(request), timeout=spec["budget"]["timeout_seconds"])
            result.metadata = self.credentials.redact(result.metadata, keys)
        except asyncio.CancelledError:
            error = RuntimeError("Ajuste interrompido antes da conclusão.")
        except Exception as exc:
            error = exc
        finally:
            if registry is not None:
                try:
                    await close_registry(registry)
                except Exception as exc:
                    error = error or exc
        participant = spec["participants"][0]
        raw = asdict(build_raw_observation(request=request, attempt_index=1, started_at=started, requested_provider_kind=spec["providers"][participant["provider"]]["kind"], requested_model=participant["model"], available_tool_names=[d.name for d in runtime.definitions()] if request.allow_tools and runtime is not None else [], result=result, error=error))
        raw["request"]["boundary"] = "norvald_lab_observer_adjustment"
        raw["error"] = self.credentials.redact(raw["error"], keys)
        check = check_contribution(result.content, participant["id"], WorkingContext.from_dict(json.loads(request.context.working_context))) if result is not None else None
        write_once(directory / "result.json", {"status": "failed" if error else "complete", "record": raw, "check": check, "error": self.credentials.redact(str(error), keys) if error else None})
        seal(directory)

    def start(self, saved, spec):
        async def execute():
            try:
                await self.run(saved, spec)
            finally:
                self.jobs.pop(saved["id"], None)
        self.jobs[saved["id"]] = asyncio.create_task(execute())
