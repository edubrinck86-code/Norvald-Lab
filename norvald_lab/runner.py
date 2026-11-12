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

from norvald_lab.own_text import render_own_text
from norvald_lab.application.arof.capacity import CapacityMonitor
from norvald_lab.application.arof.corpus import fingerprint_payload
from norvald_lab.application.arof.dataset import ExperimentManifest
from norvald_lab.application.arof.exposed_context import seed_peer_contributions
from norvald_lab.application.arof.outcome_extract import rows_from_raw, write_csv
from norvald_lab.application.arof.outcome_extract import RELACOES_DE_FUNDAMENTO
from norvald_lab.application.arof.outcome_validation import validation_from_payload
from norvald_lab.application.arof.peer_order import PEER_ORDER_METHOD, draw_peer_order, reorder_by_author
from norvald_lab.application.arof.prior_contribution import PriorContribution
from norvald_lab.application.arof.raw_observation import build_raw_observation
from norvald_lab.application.deliberation.round_prompt import render_shared_instructions, texts_for
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


def _has_valid_contribution(observation, require_grounds: bool = False) -> bool:
    """Se a execução trouxe uma contribuição com opção selecionada aceita pelo validador.

    Reaproveita as leituras que o Lab já usa para recusar uma origem incompleta
    (prepare: falha ou resposta vazia; seed: autor sem unidade aceita) e a coluna
    option_accepted de outcomes.csv (validation_from_payload, sobre o contexto gravado no
    próprio registro). Aceitar uma opção implica as duas primeiras.
    """
    payload = observation.to_dict()
    if payload.get("error"):
        return False
    content = (payload.get("result") or {}).get("content") or ""
    if not content.strip():
        return False
    # 12/11/2026 (achado do PR #16): contribuição com ZERO fundamentos (derived_from,
    # evidenced_by, documents) passava como válida. A regra mora só neste portão da coleta
    # (nova tentativa), nunca no validador compartilhado nem nas medidas: as coletas conf2-*
    # foram validadas e analisadas com a regra antiga e seguem assim. Opt-in por spec
    # (budget.require_grounds), então spec e fingerprint antigos não mudam.
    outcome = validation_from_payload(payload, response=content, grounding_relations=RELACOES_DE_FUNDAMENTO if require_grounds else ())
    if require_grounds and not outcome.grounding_targets_accepted:
        return False
    return bool(outcome.option_accepted)


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
    # O idioma só entra quando não é o padrão: specs em pt-BR (com ou sem o campo) mantêm a base de sempre.
    language = {"language": spec["language"]} if spec.get("language", "pt-BR") != "pt-BR" else {}
    return {k: spec[k] for k in ("task", "participants", "providers", "documents", "working_context", "repetitions", "mode")} | language | {"tools": {k: spec["condition"].get(k) for k in ("tools", "max_tool_calls", "max_tool_iterations")}, "prompt_profile": PROMPT_PROFILE}


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
        excluded = {}  # repetição -> participantes fora da exposição (344-79, item 2)
        if exposure != "blind":
            source_id = condition["prior_experiment"]
            records = read_verified_records(self.root, source_id, allow_incomplete=True)
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
            # Registro aw9vf (344-79, item 2), corrigido em 12/11/2026: na coleta conf2 o Lab recusava a
            # pergunta inteira quando um participante não tinha contribuição em B1, e perdeu ~28 perguntas.
            # O registro diz que esse participante não entra no WC, ninguém o vê, e só ele sai da análise
            # de exposição daquela pergunta; os demais seguem. A exclusão fica gravada por pergunta.
            for index in range(1, spec["repetitions"] + 1):
                for participant in spec["participants"]:
                    raw = prior_by_run.get((index, participant["id"]))
                    reason = None
                    if raw is None:
                        reason = "sem registro em B1"
                    elif raw.get("error") or not (raw.get("result") or {}).get("content"):
                        reason = "falha ou resposta vazia em B1"
                    else:
                        _, authors, _ = seed_peer_contributions(WorkingContext.from_dict(base.to_dict()), [PriorContribution(raw["participant_id"], raw["result"]["content"])])
                        if raw["participant_id"] not in authors:
                            reason = "contribuição de B1 não entrou no WC: " + check_contribution(raw["result"]["content"], raw["participant_id"], base)["message"]
                    if reason:
                        excluded.setdefault(index, []).append({"participant_id": participant["id"], "reason": reason, **({"observation_id": raw["observation_id"]} if raw else {})})
                        prior_by_run.pop((index, participant["id"]), None)
                if not any(key[0] == index for key in prior_by_run):
                    raise ValueError(f"A origem não possui nenhuma contribuição válida na repetição {index}.")
        corpus_hash = fingerprint_payload(spec["documents"])
        language = spec.get("language", "pt-BR")
        texts = texts_for(language)
        prepared_requests = []
        seed_audits = []
        frozen_contexts = {}
        option_ids = {item.id for item in base.active_items() if item.type == "option"}

        def seed(raws, index):
            """Semeia o contexto com as respostas cegas dadas; um único congelamento por conjunto visível."""
            visibility_key = (index, tuple(raw["observation_id"] for raw in raws))
            if visibility_key not in frozen_contexts:
                seeded, authors, audit = seed_peer_contributions(WorkingContext.from_dict(base.to_dict()), [PriorContribution(raw["participant_id"], raw["result"]["content"]) for raw in raws])
                if set(authors) != {raw["participant_id"] for raw in raws}:
                    missing = [raw for raw in raws if raw["participant_id"] not in authors]
                    details = [f"{raw['participant_name']} ({raw['participant_id']}, {raw['requested_model']}), repetição {index}: " + check_contribution(raw["result"]["content"], raw["participant_id"], base)["message"] for raw in missing]
                    raise ValueError("Exposição incompleta recusada. " + " | ".join(details) + " A coleta original permanece salva. Confira o diagnóstico e a resposta original na bancada.")
                frozen_contexts[visibility_key] = (seeded.to_dict(), audit)
            return frozen_contexts[visibility_key]

        for index in range(1, spec["repetitions"] + 1):
            out = {item["participant_id"] for item in excluded.get(index, [])}
            for participant in [p for p in spec["participants"] if p["id"] not in out]:
                everyone = [prior_by_run[(index, p["id"])] for p in spec["participants"] if p["id"] not in out] if exposure != "blind" else []
                # Em B3 e EP o participante só vê a própria contribuição inteira; em E, a de todos.
                # Em B3L (self_letter) ele não vê a contribuição: só a opção que escolheu (abaixo).
                visible = [raw for raw in everyone if exposure == "exposed" or (exposure in {"self", "stance"} and raw["participant_id"] == participant["id"])]
                own_raw = [raw for raw in everyone if raw["participant_id"] == participant["id"]] if exposure in {"self_letter", "self_text"} else []
                # TESE-002 §4.1: em E (e em EP, que usa a mesma ordem) a ordem dos pares é sorteada por execução e gravada (ver peer_order.py).
                shows_peers = exposure in {"exposed", "stance"}
                peer_order = draw_peer_order([raw["participant_id"] for raw in everyone], experiment_id=spec["experiment_id"], repetition_index=index, participant_id=participant["id"]) if shows_peers else []
                wc = WorkingContext.from_dict(base.to_dict())
                peer_positions = None
                if visible:
                    context_snapshot, audit = seed(visible, index)
                    if exposure == "exposed" and peer_order:
                        context_snapshot = reorder_by_author(context_snapshot, peer_order)
                    wc = WorkingContext.from_dict(context_snapshot)
                    if exposure == "stance":
                        # Os pares entram pelo mesmo caminho validado de E, mas só as relações `selects` saem dele:
                        # o texto, a confiança e os demais itens dos pares nunca chegam ao prompt.
                        full_snapshot, audit = seed(everyone, index)
                        chosen = {}
                        for rel in full_snapshot["relations"]:
                            if rel["relation_type"] == "selects" and rel["target_id"] in option_ids:
                                chosen.setdefault(rel["author_id"], [])
                                if rel["target_id"] not in chosen[rel["author_id"]]:
                                    chosen[rel["author_id"]].append(rel["target_id"])
                        peer_positions = [{"author_id": author, "selects": chosen.get(author, [])} for author in peer_order if author != participant["id"]]
                    seed_audits.append({"repetition_index": index, "participant_id": participant["id"], "peer_order": peer_order, **asdict(audit)})
                own_previous_answer = None
                if own_raw:
                    # Controle exploratório B3L (12/11/2026): reproduz o de Hao et al. (2026, Tabela 30), que mostra
                    # só a letra da resposta anterior. A opção sai pelo mesmo caminho validado de B3 (seed), e
                    # nenhum texto, fundamento ou confiança da contribuição chega ao prompt.
                    own_snapshot, audit = seed(own_raw, index)
                    own_previous_answer = {"selects": [rel["target_id"] for rel in own_snapshot["relations"] if rel["relation_type"] == "selects" and rel["target_id"] in option_ids and rel["author_id"] == participant["id"]]}
                    if exposure == "self_text":
                        # Estudo do formato (12/11/2026): B3T mostra o mesmo conteúdo de B3, a própria contribuição de B1
                        # inteira, mas em texto corrido e não como itens e relações. Muda só a forma; ver render_own_text.
                        own_previous_answer = {"text": render_own_text(own_snapshot, participant["id"])}
                    seed_audits.append({"repetition_index": index, "participant_id": participant["id"], "peer_order": [], **asdict(audit)})
                # A projeção é integral, sem seleção semântica ou truncamento silencioso.
                projection = {"question": wc.question, "items": [item.to_dict() for item in wc.active_items()], "relations": [rel.to_dict() for rel in wc.relations]}
                if peer_positions is not None:
                    projection["peer_positions"] = peer_positions
                if own_previous_answer is not None:
                    projection["own_previous_answer"] = own_previous_answer
                context = _json(projection)
                round_number = 1 if exposure == "blind" else 2
                evidence = texts["corpus_header"] + "\n" + _json(spec["documents"])
                shared = render_shared_instructions(evidence_block=evidence, has_library_tools=condition["tools"] == "corpus", round_number=round_number, language=language)
                shared += "\n\n" + texts["lab_profile"]
                instructions = texts["identity"].format(name=participant["name"], role=participant["role"]) + "\n" + spec["task"]["instructions"]
                if exposure != "blind":
                    instructions += "\n" + texts["reconsider"]
                provider_kind = spec["providers"][participant["provider"]]["kind"]
                sampling = resolve_sampling(SamplingParams.from_dict(participant["sampling"]), provider_kind=provider_kind, model=participant["model"], reasoning_effort=participant["reasoning_effort"], keep_sampling_with_reasoning=participant.get("sampling_with_reasoning", False))
                metadata = {
                    "session_id": "lab:" + spec["experiment_id"], "source_session_id": spec["source"].get("session_id", ""),
                    "execution_id": f"{spec['experiment_id']}:{index}:{participant['id']}",
                    "execution_scope": {"experiment_id": spec["experiment_id"], "repetition_index": index, "participant_id": participant["id"]},
                    "experiment_id": spec["experiment_id"], "condition_id": condition["id"], "run_id": f"r{index:04d}",
                    "round": round_number, "repetition_index": index, "participant_id": participant["id"], "participant_name": participant["name"], "participant_role": participant["role"],
                    "task_id": spec["task"]["id"], "task_label": spec["task"]["id"],
                    "peer_exposure_mode": exposure if exposure in {"exposed", "stance"} else "blind", "lab_exposure_mode": exposure,
                    "source_experiment_id": condition.get("prior_experiment"), "source_observation_ids": [raw["observation_id"] for raw in (everyone if exposure == "stance" else own_raw if exposure in {"self_letter", "self_text"} else visible)],
                    "peer_order": peer_order, "peer_order_method": PEER_ORDER_METHOD if shows_peers else None,
                    "reasoning_exposure_mode": "unknown", "can_modify_deliberation_artifacts": False,
                    "library_corpus_fingerprint": corpus_hash, "library_corpus_item_count": len(spec["documents"]), "library_corpus_algorithm": "sha256-canonical-json-v1",
                    **({"prompt_language": language} if language != "pt-BR" else {}),
                    # Só aparece quando há exclusão: as derivadas completas mantêm a impressão digital de antes.
                    **({"excluded_from_exposure": excluded[index]} if excluded.get(index) else {}),
                    "research_anchor_ids": ["evidence-" + d["id"] for d in spec["documents"]], "attached_evidence_mode": "lab_inline_full", "tool_phase": "lab_frozen_corpus", "tool_limits_explicit": condition.get("max_tool_calls") is not None or condition.get("max_tool_iterations") is not None,
                }
                prepared_requests.append({"agent_id": participant["id"], "instructions": instructions, "shared_instructions": shared, "wave_instructions": texts["wc_header"] + "\n" + context, "user_message": spec["task"]["objective"], "reasoning_effort": participant["reasoning_effort"], **({"upstream_provider": participant["upstream_provider"]} if participant.get("upstream_provider") else {}), "sampling": sampling.as_dict(), "allow_tools": condition["tools"] == "corpus", "max_tool_calls": condition.get("max_tool_calls"), "max_tool_iterations": condition.get("max_tool_iterations"), "context": {"objective": spec["task"]["objective"], "working_context": context, "metadata": metadata}})
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
        # Uma nova tentativa por participante (piloto-mmlu-1, 11/11/2026): o padrão 1 é a coleta de sempre.
        max_attempts = budget.get("max_agent_attempts", 1)
        manifest = ExperimentManifest(experiment_id=expid, framework_version="AROF-Lab-v1", task=spec["task"], conditions=(spec["condition"] | {"repetitions": spec["repetitions"]},), models=tuple(spec["participants"]), budget=budget | {"planned_logical_executions": planned, "max_attempts": planned * max_attempts}, corpus={"documents": spec["documents"], "fingerprint": fingerprint_payload(spec["documents"])}, metadata={"runner_version": RUNNER_VERSION, "prompt_profile": PROMPT_PROFILE, "condition_fingerprint": prepared.condition_fingerprint, "execution_revision": EXECUTION_REVISION, "studio_revision": STUDIO_REVISION, "synthetic": spec["mode"] == "demo", "agent_attempts_per_execution": max_attempts, "transport_retries": "Norvald-Execution policy; not independent samples"}, notes=("Corpus integral em todas as condições; sem replanejamento automático; não equivale ao perfil nativo de ferramentas do Studio.",))
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
                # Cada tentativa é uma observação própria (attempt_index); a seguinte só existe
                # se a anterior não trouxe contribuição válida e ainda há tentativas no orçamento.
                for attempt in range(1, max_attempts + 1):
                    started = _utc()
                    emit("execution.started", {"participant_id": participant["id"], "run_id": metadata["run_id"]} | ({"attempt_index": attempt} if max_attempts > 1 else {}))
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
                    observation = build_raw_observation(request=request, attempt_index=attempt, started_at=started, requested_provider_kind=spec["providers"][participant["provider"]]["kind"], requested_model=participant["model"], available_tool_names=[d.name for d in runtime.definitions()] if request.allow_tools else [], result=result, error=error)
                    observation = replace(observation, error=redact(observation.error), request=observation.request | {"boundary": "norvald_lab_execution", "studio_metadata": observation.request["studio_metadata"] | {k: metadata[k] for k in LAB_RAW_METADATA_KEYS} | ({"excluded_from_exposure": metadata["excluded_from_exposure"]} if "excluded_from_exposure" in metadata else {})})
                    sink.record(observation)
                    output = {"participant_id": participant["id"], "run_id": metadata["run_id"], "ok": error is None, "error": redact(str(error)) if error else None, "provider": participant["provider"], "model": participant["model"], "reasoning_captured": bool(result and result.reasoning), "input_tokens": result.input_tokens if result else None, "output_tokens": result.output_tokens if result else None}
                    if max_attempts > 1:
                        output["attempt_index"] = attempt
                    outputs.append(output)
                    emit("execution.completed" if error is None else "execution.failed", output)
                    if cancelled:
                        raise asyncio.CancelledError
                    if _has_valid_contribution(observation, budget.get("require_grounds", False)):
                        break
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
            # Execução lógica é o par (repetição, participante); tentativa é cada chamada. Falha conta por tentativa.
            capacity = await monitor.stop(logical_executions=len({(x["run_id"], x["participant_id"]) for x in outputs}), attempts=len(outputs), failures=sum(not x["ok"] for x in outputs)) if monitor else None
        if capacity:
            write_capacity_report(expid, capacity, root=self.root)
        # O estado vale pela última tentativa de cada execução lógica; a falha da 1ª fica nos registros.
        final = {(x["run_id"], x["participant_id"]): x for x in outputs}
        failures = sum(not x["ok"] for x in final.values())
        status = "aborted" if aborted else "incomplete" if failures else "complete"
        raw_files = sorted((directory / "raw").rglob("*.jsonl"))
        close_experiment(expid, raw_files, status=status, root=self.root)
        rows = rows_from_raw(raw_files, experiment_id=expid, all_attempts=True)
        write_csv(rows, directory / "outcomes.csv")
        result_view = {"experiment_id": expid, "condition_id": spec["condition"]["id"], "status": status, "synthetic": spec["mode"] == "demo", "planned": planned, "executed": len(final), "failures": failures, "executions": sorted(outputs, key=lambda x: (x["run_id"], x["participant_id"], x.get("attempt_index", 1))), "condition_fingerprint": prepared.condition_fingerprint, "completed_at": _utc(), "capacity": capacity.to_dict() if capacity else None} | ({"attempts": len(outputs)} if max_attempts > 1 else {})
        write_once(directory / "result.json", result_view)
        emit("experiment.completed", {"experiment_id": expid, "status": status})
        seal(directory)
        if infrastructure_error:
            raise infrastructure_error
        return result_view
