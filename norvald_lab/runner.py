"""Adaptação independente do ExperimentRunner do Studio.

Preserva os contratos AROF e o motor Execution. Recebe um snapshot portátil,
não SessionStore, credenciais do Studio, factories globais ou conexão à UI.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from norvald_lab.application.arof.capacity import CapacityMonitor
from norvald_lab.application.arof.corpus import fingerprint_payload
from norvald_lab.application.arof.dataset import ExperimentManifest
from norvald_lab.application.arof.exposed_context import seed_peer_contributions
from norvald_lab.application.arof.outcome_extract import rows_from_raw, write_csv
from norvald_lab.application.arof.peer_order import PEER_ORDER_METHOD, draw_peer_order, reorder_by_author
from norvald_lab.application.arof.prior_contribution import PriorContribution
from norvald_lab.application.arof.raw_observation import build_raw_observation
from norvald_lab.application.deliberation.round_prompt import render_shared_instructions
from norvald_lab.config import validate_spec
from norvald_lab.contribution_check import check_contribution
from norvald_lab.domain.deliberation.context_item import ContextItem
from norvald_lab.domain.deliberation.working_context import WorkingContext
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root, close_experiment, write_capacity_report, write_manifest
from norvald_lab.infrastructure.arof.raw_observation_store import JsonlRawObservationStore
from norvald_lab.runtime import build_registry, close_registry, corpus_runtime
from norvald_lab.settings import LocalSettings
from norvald_lab.storage import read_verified_records, seal, write_once
from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest
from norvald_lab.vendor.norvald_execution.contracts.sampling import ResolvedSampling, SamplingParams, resolve_sampling
from norvald_lab.vendor.norvald_execution.orchestration.agent_orchestrator import AgentOrchestrator
from norvald_lab.vendor.norvald_execution.tools import tool_loop

# v2 (2026-10-04): parser com recusa por parte e colunas do validador em
# outcomes.csv — divergências intencionais do Studio, docs/MIGRACAO.md.
# O valor entra no manifesto e no fingerprint da condição: coleta v1 e
# coleta v2 ficam distinguíveis pelo registro, não pela memória.
RUNNER_VERSION = "norvald.lab.runner.v2"
# Campos do Lab copiados para o registro bruto de cada execução.
# peer_order e peer_order_method entraram em 11/11/2026: o teste de fumaça
# fumaca-2 mostrou que a ordem sorteada dos pares (TESE-002 §4.1) ficava só no
# requests.json, fora do registro bruto que alimenta as medidas.
LAB_RAW_METADATA_KEYS = ("repetition_index", "lab_exposure_mode", "source_experiment_id", "source_observation_ids", "peer_order", "peer_order_method")
PROMPT_PROFILE = "lab-controlled-structured-v1"
EXECUTION_REVISION = "c903aa42af8a959c7868c6d8be3b744c9677ac16"
STUDIO_REVISION = "f0d640779324bdde8c1f76e83b1a1869602af089"


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utc():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PreparedExperiment:
    """Strings imutáveis impedem alterações indiretas depois de preparar."""
    snapshot_json: str
    requests_json: tuple[str, ...]
    seed_audits_json: str
    condition_fingerprint: str

    @property
    def spec(self):
        return json.loads(self.snapshot_json)


def _comparison_base(spec):
    return {k: spec[k] for k in ("task", "participants", "providers", "documents", "working_context", "repetitions", "mode")} | {"tools": {k: spec["condition"].get(k) for k in ("tools", "max_tool_calls", "max_tool_iterations")}, "prompt_profile": PROMPT_PROFILE}


class ExperimentRunner:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root).expanduser() if root is not None else arof_data_root()
        self.credentials = LocalSettings(self.root)

    def prepare(self, payload: dict) -> PreparedExperiment:
        spec = validate_spec(payload)
        condition = spec["condition"]
        exposure = condition["exposure"]
        base = WorkingContext.from_dict(spec["working_context"] | {"question": spec["task"]["objective"]})
        if any(item.author_id or item.source_type == "specialist" for item in base.active_items()):
            raise ValueError("O contexto inicial deve estar limpo de contribuições de especialistas.")
        for doc in spec["documents"]:
            anchor = "evidence-" + doc["id"]
            if base.get(anchor) is not None:
                raise ValueError(f"Âncora documental duplicada no contexto: {anchor}")
            base.add(ContextItem(id=anchor, type="evidence", content=doc["title"], source_type="document", source_id=doc["id"], source_location=doc["source"]))
        prior_by_run = {}
        if exposure != "blind":
            source_id = condition["prior_experiment"]
            records = read_verified_records(self.root, source_id)
            source_spec = json.loads((self.root / "experiments" / source_id / "spec.json").read_text())
            if source_spec["condition"]["exposure"] != "blind":
                raise ValueError("A origem deve ser uma condição cega.")
            if fingerprint_payload(_comparison_base(source_spec)) != fingerprint_payload(_comparison_base(spec)):
                raise ValueError("Tarefa, participantes, corpus, repetições ou ferramentas diferem da origem cega.")
            for record in records:
                raw = record.payload
                metadata = raw["request"]["studio_metadata"]
                index = metadata["repetition_index"]
                key = (index, raw["participant_id"])
                previous = prior_by_run.get(key)
                if previous is None or raw["attempt_index"] > previous["attempt_index"]:
                    prior_by_run[key] = raw
            expected = {(i, p["id"]) for i in range(1, spec["repetitions"] + 1) for p in spec["participants"]}
            if set(prior_by_run) != expected or any(raw.get("error") or not (raw.get("result") or {}).get("content") for raw in prior_by_run.values()):
                raise ValueError("A origem não possui resposta válida de todos os participantes em cada repetição.")
        corpus_hash = fingerprint_payload(spec["documents"])
        prepared_requests = []
        seed_audits = []
        frozen_contexts = {}
        for index in range(1, spec["repetitions"] + 1):
            for participant in spec["participants"]:
                visible = [prior_by_run[(index, p["id"])] for p in spec["participants"] if exposure == "exposed" or (exposure == "self" and p["id"] == participant["id"])] if exposure != "blind" else []
                # TESE-002 §4.1: em E, a ordem dos pares é sorteada por execução e gravada (ver peer_order.py).
                peer_order = draw_peer_order([raw["participant_id"] for raw in visible], experiment_id=spec["experiment_id"], repetition_index=index, participant_id=participant["id"]) if exposure == "exposed" else []
                wc = WorkingContext.from_dict(base.to_dict())
                if visible:
                    visibility_key = (index, tuple(raw["observation_id"] for raw in visible))
                    if visibility_key not in frozen_contexts:
                        seeded, authors, audit = seed_peer_contributions(wc, [PriorContribution(raw["participant_id"], raw["result"]["content"]) for raw in visible])
                        if set(authors) != {raw["participant_id"] for raw in visible}:
                            missing = [raw for raw in visible if raw["participant_id"] not in authors]
                            details = [f"{raw['participant_name']} ({raw['participant_id']}, {raw['requested_model']}), repetição {index}: " + check_contribution(raw["result"]["content"], raw["participant_id"], wc)["message"] for raw in missing]
                            raise ValueError("Exposição incompleta recusada. " + " | ".join(details) + " A coleta original permanece salva. Confira o diagnóstico e a resposta original na bancada.")
                        frozen_contexts[visibility_key] = (seeded.to_dict(), audit)
                    context_snapshot, audit = frozen_contexts[visibility_key]
                    if peer_order:
                        context_snapshot = reorder_by_author(context_snapshot, peer_order)
                    wc = WorkingContext.from_dict(context_snapshot)
                    seed_audits.append({"repetition_index": index, "participant_id": participant["id"], "peer_order": peer_order, **asdict(audit)})
                # A projeção é integral, sem seleção semântica ou truncamento silencioso.
                context = _json({"question": wc.question, "items": [item.to_dict() for item in wc.active_items()], "relations": [rel.to_dict() for rel in wc.relations]})
                round_number = 1 if exposure == "blind" else 2
                evidence = "CORPUS CONGELADO DESTE EXPERIMENTO:\n" + _json(spec["documents"])
                shared = render_shared_instructions(evidence_block=evidence, has_library_tools=condition["tools"] == "corpus", round_number=round_number)
                shared += "\n\nPERFIL DO LABORATÓRIO: o corpus e o contexto acima são integrais e congelados. As únicas ferramentas possíveis são list_documents e read_document quando oferecidas. Não há acesso ao Studio, busca web ou outros documentos. Não existe scan_context nesta execução."
                instructions = f"Você é {participant['name']}, atuando como {participant['role']}.\n" + spec["task"]["instructions"]
                if exposure != "blind":
                    instructions += "\nReconsidere a tarefa à luz das contribuições disponíveis no contexto."
                provider_kind = spec["providers"][participant["provider"]]["kind"]
                sampling = resolve_sampling(SamplingParams.from_dict(participant["sampling"]), provider_kind=provider_kind, model=participant["model"], reasoning_effort=participant["reasoning_effort"])
                metadata = {
                    "session_id": "lab:" + spec["experiment_id"], "source_session_id": spec["source"].get("session_id", ""),
                    "execution_id": f"{spec['experiment_id']}:{index}:{participant['id']}",
                    "execution_scope": {"experiment_id": spec["experiment_id"], "repetition_index": index, "participant_id": participant["id"]},
                    "experiment_id": spec["experiment_id"], "condition_id": condition["id"], "run_id": f"r{index:04d}",
                    "round": round_number, "repetition_index": index, "participant_id": participant["id"], "participant_name": participant["name"], "participant_role": participant["role"],
                    "task_id": spec["task"]["id"], "task_label": spec["task"]["id"],
                    "peer_exposure_mode": "exposed" if exposure == "exposed" else "blind", "lab_exposure_mode": exposure,
                    "source_experiment_id": condition.get("prior_experiment"), "source_observation_ids": [raw["observation_id"] for raw in visible],
                    "peer_order": peer_order, "peer_order_method": PEER_ORDER_METHOD if exposure == "exposed" else None,
                    "reasoning_exposure_mode": "unknown", "can_modify_deliberation_artifacts": False,
                    "library_corpus_fingerprint": corpus_hash, "library_corpus_item_count": len(spec["documents"]), "library_corpus_algorithm": "sha256-canonical-json-v1",
                    "research_anchor_ids": ["evidence-" + d["id"] for d in spec["documents"]], "attached_evidence_mode": "lab_inline_full", "tool_phase": "lab_frozen_corpus", "tool_limits_explicit": condition.get("max_tool_calls") is not None or condition.get("max_tool_iterations") is not None,
                }
                prepared_requests.append({"agent_id": participant["id"], "instructions": instructions, "shared_instructions": shared, "wave_instructions": "WORKING CONTEXT INTEGRAL:\n" + context, "user_message": spec["task"]["objective"], "reasoning_effort": participant["reasoning_effort"], "sampling": sampling.as_dict(), "allow_tools": condition["tools"] == "corpus", "max_tool_calls": condition.get("max_tool_calls"), "max_tool_iterations": condition.get("max_tool_iterations"), "context": {"objective": spec["task"]["objective"], "working_context": context, "metadata": metadata}})
        fingerprint = fingerprint_payload({"spec": spec, "requests": prepared_requests, "execution_revision": EXECUTION_REVISION, "studio_revision": STUDIO_REVISION, "runner_version": RUNNER_VERSION})
        for request in prepared_requests:
            request["context"]["metadata"]["condition_fingerprint"] = fingerprint
        return PreparedExperiment(_json(spec), tuple(_json(r) for r in prepared_requests), _json(seed_audits), fingerprint)

    async def run(self, prepared: PreparedExperiment, *, allow_live=False, registry=None, on_event: Callable | None = None, monitor_capacity=True):
        spec = prepared.spec
        own_registry = registry is None
        registry = registry or build_registry(spec, allow_live=allow_live, credential_resolver=self.credentials.resolve)
        if spec["mode"] == "live" and not allow_live:
            raise ValueError("Execução real precisa ser habilitada explicitamente.")
        try:
            for p in spec["participants"]:
                provider, model = registry.resolve(p["id"])
                if model != p["model"] or registry.provider_name_for(p["id"]) != p["provider"]:
                    raise ValueError("Registry difere do snapshot preparado.")
                if spec["condition"]["tools"] == "corpus" and not provider.SUPPORTS_TOOL_USE:
                    raise ValueError(f"{p['id']}: provider não suporta as ferramentas declaradas.")
            return await self._run(prepared, registry, on_event, monitor_capacity)
        finally:
            if own_registry:
                await close_registry(registry)

    async def _run(self, prepared, registry, on_event, monitor_capacity):
        spec = prepared.spec
        # Capture as credenciais efetivamente entregues ao transporte: uma chave
        # pode ser removida/substituída na UI enquanto a coleta está em curso.
        keys = [getattr(registry.get_provider(name), "_api_key", "") for name in registry.provider_names()]
        keys += [self.credentials.resolve(c["kind"], c.get("credential_env", ""), c.get("base_url")) for c in spec["providers"].values() if c["kind"] != "demo"]
        redact = lambda value: self.credentials.redact(value, keys)
        expid = spec["experiment_id"]
        directory = self.root / "experiments" / expid
        # Reserva exclusiva entre processos: nenhuma segunda execução reutiliza o ID.
        directory.mkdir(parents=True, exist_ok=False)
        planned = len(prepared.requests_json)
        budget = spec["budget"]
        manifest = ExperimentManifest(experiment_id=expid, framework_version="AROF-Lab-v1", task=spec["task"], conditions=(spec["condition"] | {"repetitions": spec["repetitions"]},), models=tuple(spec["participants"]), budget=budget | {"planned_logical_executions": planned, "max_attempts": planned}, corpus={"documents": spec["documents"], "fingerprint": fingerprint_payload(spec["documents"])}, metadata={"runner_version": RUNNER_VERSION, "prompt_profile": PROMPT_PROFILE, "condition_fingerprint": prepared.condition_fingerprint, "execution_revision": EXECUTION_REVISION, "studio_revision": STUDIO_REVISION, "synthetic": spec["mode"] == "demo", "agent_attempts_per_execution": 1, "transport_retries": "Norvald-Execution policy; not independent samples"}, notes=("Corpus integral em todas as condições; sem replanejamento automático; não equivale ao perfil nativo de ferramentas do Studio.",))
        write_manifest(manifest, root=self.root)
        write_once(directory / "spec.json", spec)
        write_once(directory / "requests.json", [json.loads(s) for s in prepared.requests_json])
        write_once(directory / "seed_audits.json", json.loads(prepared.seed_audits_json))
        events = directory / "events.jsonl"
        def emit(event, data):
            data = redact(data)
            with events.open("a", encoding="utf-8") as out:
                out.write(_json({"at": _utc(), "event": event, "data": data}) + "\n")
            if on_event:
                try:
                    on_event(event, data)
                except Exception:
                    pass  # A visualização não decide o sucesso da coleta.
        emit("experiment.started", {"experiment_id": expid, "planned": planned, "mode": spec["mode"]})
        sink = JsonlRawObservationStore(self.root)
        slots = asyncio.Semaphore(budget["max_concurrency"])
        provider_slots = {name: asyncio.Semaphore(budget["max_concurrency_per_provider"]) for name in spec["providers"]}
        monitor = CapacityMonitor(disk_path=self.root, dataset_path=directory) if monitor_capacity else None
        if monitor:
            await monitor.start()
        outputs = []
        async def execute(serialized):
            data = json.loads(serialized)
            metadata = data["context"]["metadata"]
            participant = next(p for p in spec["participants"] if p["id"] == data["agent_id"])
            request = ExecutionRequest(**{k: v for k, v in data.items() if k not in {"context", "sampling"}}, context=ExecutionContext(**data["context"]), sampling=ResolvedSampling(**data["sampling"]))
            async with slots, provider_slots[participant["provider"]]:
                started = _utc()
                emit("execution.started", {"participant_id": participant["id"], "run_id": metadata["run_id"]})
                # Mesmo sem ferramentas, o runtime recebe os eventos de transporte.
                runtime = corpus_runtime(spec["documents"] if request.allow_tools else [], on_event=lambda event, details: emit(event, details | {"execution_id": metadata["execution_id"]}))
                orchestrator = AgentOrchestrator(registry, tool_registry=runtime, tool_loop=tool_loop)
                result = None
                error = None
                cancelled = False
                try:
                    result = await asyncio.wait_for(orchestrator.execute(request), timeout=budget["timeout_seconds"])
                except asyncio.CancelledError:
                    error = RuntimeError("Execução interrompida antes da conclusão.")
                    cancelled = True
                except Exception as exc:
                    error = exc
                if result is not None:
                    result.metadata = redact(result.metadata)
                observation = build_raw_observation(request=request, attempt_index=1, started_at=started, requested_provider_kind=spec["providers"][participant["provider"]]["kind"], requested_model=participant["model"], available_tool_names=[d.name for d in runtime.definitions()] if request.allow_tools else [], result=result, error=error)
                observation = replace(observation, error=redact(observation.error), request=observation.request | {"boundary": "norvald_lab_execution", "studio_metadata": observation.request["studio_metadata"] | {k: metadata[k] for k in LAB_RAW_METADATA_KEYS}})
                sink.record(observation)
                output = {"participant_id": participant["id"], "run_id": metadata["run_id"], "ok": error is None, "error": redact(str(error)) if error else None, "provider": participant["provider"], "model": participant["model"], "reasoning_captured": bool(result and result.reasoning), "input_tokens": result.input_tokens if result else None, "output_tokens": result.output_tokens if result else None}
                outputs.append(output)
                emit("execution.completed" if error is None else "execution.failed", output)
                if cancelled:
                    raise asyncio.CancelledError
        tasks = [asyncio.create_task(execute(s)) for s in prepared.requests_json]
        aborted = False
        infrastructure_error = None
        try:
            await asyncio.gather(*tasks)
        except BaseException as exc:
            aborted = True
            infrastructure_error = exc
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            capacity = await monitor.stop(logical_executions=len(outputs), attempts=len(outputs), failures=sum(not x["ok"] for x in outputs)) if monitor else None
        if capacity:
            write_capacity_report(expid, capacity, root=self.root)
        status = "aborted" if aborted else "incomplete" if any(not x["ok"] for x in outputs) else "complete"
        raw_files = sorted((directory / "raw").rglob("*.jsonl"))
        close_experiment(expid, raw_files, status=status, root=self.root)
        rows = rows_from_raw(raw_files, experiment_id=expid)
        write_csv(rows, directory / "outcomes.csv")
        result_view = {"experiment_id": expid, "condition_id": spec["condition"]["id"], "status": status, "synthetic": spec["mode"] == "demo", "planned": planned, "executed": len(outputs), "failures": sum(not x["ok"] for x in outputs), "executions": sorted(outputs, key=lambda x: (x["run_id"], x["participant_id"])), "condition_fingerprint": prepared.condition_fingerprint, "completed_at": _utc(), "capacity": capacity.to_dict() if capacity else None}
        write_once(directory / "result.json", result_view)
        emit("experiment.completed", {"experiment_id": expid, "status": status})
        seal(directory)
        if infrastructure_error:
            raise infrastructure_error
        return result_view
