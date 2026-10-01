from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence
from uuid import uuid4

from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult

AROF_RAW_SCHEMA_VERSION = "arof.raw.v4"

# Metadados internos que identificam/reproduzem a unidade experimental sem
# duplicar blocos grandes já presentes no prompt (repository_material,
# contributions_by_item, task_context etc.).
_STUDIO_METADATA_KEYS = (
    "session_id",
    "source_session_id",
    "execution_id",
    "round",
    "participant_id",
    "participant_name",
    "participant_role",
    "working_context_id",
    "proposal_type",
    "task_id",
    "can_modify_deliberation_artifacts",
    "experiment_id",
    "condition_id",
    "condition_fingerprint",
    "run_id",
    "task_label",
    "peer_exposure_mode",
    "reasoning_exposure_mode",
    "assistant_reference_enabled",
    "research_anchor_ids",
    "attached_evidence_mode",
    "tool_phase",
    "library_corpus_fingerprint",
    "library_corpus_item_count",
    "library_corpus_algorithm",
    "tool_limits_explicit",
)


def json_safe(value: Any) -> Any:
    """Converte valores do runtime para uma representação JSON estável.

    O RAW não deve falhar porque um provider colocou Enum, dataclass ou
    outro objeto simples em metadata. Objetos desconhecidos degradam para
    string; o dado bruto textual (prompt/reasoning/response) permanece
    preservado nos campos próprios e não depende desta conversão.
    """

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(item) for item in value]

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return json_safe(to_dict())
        except Exception:
            pass
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        try:
            return json_safe(as_dict())
        except Exception:
            pass

    values = getattr(value, "__dict__", None)
    if isinstance(values, dict):
        return json_safe(values)
    return str(value)


def _selected_studio_metadata(request: ExecutionRequest) -> dict[str, Any]:
    metadata = request.context.metadata if request.context else {}
    if not isinstance(metadata, dict):
        return {}
    return {
        key: json_safe(metadata.get(key))
        for key in _STUDIO_METADATA_KEYS
        if key in metadata
    }


def _logical_execution_id(
    request: ExecutionRequest,
    *,
    session_id: str,
    round_number: int,
    participant_id: str,
) -> str:
    metadata = request.context.metadata if request.context else {}
    if isinstance(metadata, dict) and metadata.get("execution_id"):
        return str(metadata["execution_id"])
    if session_id or participant_id:
        return f"{session_id or 'execution'}:{round_number}:{participant_id or request.agent_id}"
    return f"execution:{round_number}:{request.agent_id}"


@dataclass(frozen=True)
class RawObservationRecord:
    """L0 do AROF: uma tentativa observada na fronteira de execução.

    Uma execução lógica pode ter mais de uma tentativa, por exemplo um
    replanejamento. logical_execution_id identifica a unidade; attempt_index
    impede que tentativas sejam contadas como especialistas independentes.
    Esse índice conta tentativas na fronteira do agente, não retries HTTP
    internos do provider, que pertencem à telemetria de transporte.

    O request registrado é o contrato na fronteira SpecialistExecutionAgent.
    Providers ainda podem traduzi-lo para seus payloads próprios. Na fase
    inicial, essa fronteira preserva o conteúdo textual e o contrato de
    ferramentas que determinam o turno sem acoplar o AROF a cada adapter
    de provider. tools_off é intervenção experimental explícita.
    """

    schema_version: str
    observation_id: str
    started_at: str
    captured_at: str
    logical_execution_id: str
    attempt_index: int
    attempt_outcome: str

    session_id: str
    round_number: int
    participant_id: str
    participant_name: str
    participant_role: str
    agent_id: str
    task_id: str

    experiment_id: str | None
    condition_id: str | None
    run_id: str | None
    task_label: str | None
    # Exposição entre agentes: blind/exposed. Não confundir com o modo
    # de exposição do reasoning pelo provider.
    peer_exposure_mode: str | None
    # Como o provider expõe reasoning: raw/summarized/filtered/redacted/unknown.
    reasoning_exposure_mode: str

    research_anchor_ids: tuple[str, ...]
    attached_evidence_mode: str
    tool_phase: str

    library_corpus_fingerprint: str | None
    library_corpus_item_count: int | None
    library_corpus_algorithm: str | None

    tool_limits_explicit: bool
    termination_reason: str | None
    tool_loop_truncated: bool | None
    runtime_available_tool_names: tuple[str, ...]
    provider_advertised_tool_names: tuple[str, ...]

    requested_provider_kind: str
    requested_model: str

    request: dict[str, Any]
    result: dict[str, Any] | None
    error: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


class RawObservationSink(Protocol):
    """Porta passiva de L0. Nunca participa da decisão de execução."""

    @property
    def enabled(self) -> bool:
        ...

    def record(self, observation: RawObservationRecord) -> None:
        ...


class NullRawObservationSink:
    @property
    def enabled(self) -> bool:
        return False

    def record(self, observation: RawObservationRecord) -> None:
        return None


def build_raw_observation(
    *,
    request: ExecutionRequest,
    attempt_index: int,
    started_at: str | None = None,
    requested_provider_kind: str,
    requested_model: str,
    available_tool_names: Sequence[str] | None = None,
    result: ExecutionResult | None = None,
    error: BaseException | None = None,
) -> RawObservationRecord:
    metadata = request.context.metadata if request.context else {}
    metadata = metadata if isinstance(metadata, dict) else {}

    session_id = str(metadata.get("session_id") or "")
    participant_id = str(metadata.get("participant_id") or "")
    participant_name = str(metadata.get("participant_name") or "")
    participant_role = str(metadata.get("participant_role") or "")
    task_id = str(metadata.get("task_id") or "")
    try:
        round_number = int(metadata.get("round") or 0)
    except (TypeError, ValueError):
        round_number = 0

    sampling = request.sampling.as_dict() if request.sampling is not None else None
    request_snapshot = {
        "boundary": "specialist_execution_agent",
        "agent_id": request.agent_id,
        "instructions": request.instructions,
        "shared_instructions": request.shared_instructions,
        "wave_instructions": request.wave_instructions,
        "user_message": request.user_message,
        "context": {
            "objective": request.context.objective if request.context else "",
            "working_context": request.context.working_context if request.context else "",
            "working_context_id": request.context.working_context_id if request.context else None,
            "working_context_format": request.context.working_context_format if request.context else None,
        },
        "studio_metadata": _selected_studio_metadata(request),
        "reasoning_effort": request.reasoning_effort,
        "sampling": json_safe(sampling),
        "allow_tools": bool(request.allow_tools),
        "max_tool_calls": request.max_tool_calls,
        "max_tool_iterations": request.max_tool_iterations,
        "runtime_available_tool_names": list(available_tool_names or ()),
        "attachments": json_safe(request.attachments),
        "tool_exchanges_at_boundary": json_safe(request.tool_exchanges),
    }

    result_snapshot = None
    result_metadata: dict[str, Any] = {}
    if result is not None:
        result_metadata = (
            result.metadata if isinstance(result.metadata, dict) else {}
        )
        result_snapshot = {
            "content": result.content,
            "reasoning": result.reasoning,
            "provider": result.provider,
            "model": result.model,
            "tokens": result.tokens,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "duration_seconds": result.duration_seconds,
            "tool_calls": json_safe(result.tool_calls),
            "metadata": json_safe(result_metadata),
        }

    error_snapshot = None
    if error is not None:
        error_snapshot = {
            "type": type(error).__name__,
            "message": str(error),
        }

    captured_at = datetime.now(timezone.utc).isoformat()
    return RawObservationRecord(
        schema_version=AROF_RAW_SCHEMA_VERSION,
        observation_id=str(uuid4()),
        started_at=started_at or captured_at,
        captured_at=captured_at,
        logical_execution_id=_logical_execution_id(
            request,
            session_id=session_id,
            round_number=round_number,
            participant_id=participant_id,
        ),
        attempt_index=max(1, int(attempt_index)),
        # Outcome desta tentativa na fronteira do agente. "returned" não
        # significa que a validação operacional/epistêmica posterior aprovou
        # o conteúdo; apenas que o runtime devolveu um ExecutionResult.
        attempt_outcome="returned" if result is not None and error is None else "raised",
        session_id=session_id,
        round_number=round_number,
        participant_id=participant_id,
        participant_name=participant_name,
        participant_role=participant_role,
        agent_id=request.agent_id,
        task_id=task_id,
        experiment_id=str(metadata["experiment_id"]) if metadata.get("experiment_id") is not None else None,
        condition_id=str(metadata["condition_id"]) if metadata.get("condition_id") is not None else None,
        run_id=str(metadata["run_id"]) if metadata.get("run_id") is not None else None,
        task_label=str(metadata["task_label"]) if metadata.get("task_label") is not None else None,
        peer_exposure_mode=(
            str(metadata["peer_exposure_mode"])
            if metadata.get("peer_exposure_mode") is not None
            else (
                str(metadata["exposure_mode"])
                if metadata.get("exposure_mode") is not None
                else None
            )
        ),
        # O adapter conhece melhor o formato efetivamente devolvido pelo
        # provider do que o request, que normalmente só consegue declarar
        # "unknown" antes da chamada. Isso não transforma o trace: apenas
        # registra sua proveniência (summarized/raw/etc.).
        reasoning_exposure_mode=str(
            result_metadata.get("reasoning_exposure_mode")
            or metadata.get("reasoning_exposure_mode")
            or "unknown"
        ),
        research_anchor_ids=tuple(
            str(item) for item in (metadata.get("research_anchor_ids") or ())
        ),
        attached_evidence_mode=str(
            metadata.get("attached_evidence_mode") or "unknown"
        ),
        tool_phase=str(metadata.get("tool_phase") or "unknown"),
        library_corpus_fingerprint=(
            str(metadata.get("library_corpus_fingerprint"))
            if metadata.get("library_corpus_fingerprint") is not None
            else None
        ),
        library_corpus_item_count=(
            int(metadata.get("library_corpus_item_count"))
            if metadata.get("library_corpus_item_count") is not None
            else None
        ),
        library_corpus_algorithm=(
            str(metadata.get("library_corpus_algorithm"))
            if metadata.get("library_corpus_algorithm") is not None
            else None
        ),
        tool_limits_explicit=bool(
            metadata.get("tool_limits_explicit")
            or request.max_tool_calls is not None
            or request.max_tool_iterations is not None
        ),
        termination_reason=(
            str(result_metadata.get("tool_loop_reason"))
            if result_metadata.get("tool_loop_reason") is not None
            else ("provider_returned" if result is not None else None)
        ),
        tool_loop_truncated=(
            bool(result_metadata.get("tool_loop_truncated"))
            if "tool_loop_truncated" in result_metadata
            else None
        ),
        runtime_available_tool_names=tuple(
            str(item) for item in (available_tool_names or ())
        ),
        provider_advertised_tool_names=tuple(
            str(item)
            for item in (
                result_metadata.get("advertised_tool_names") or ()
            )
        ),
        requested_provider_kind=requested_provider_kind or "",
        requested_model=requested_model or "",
        request=request_snapshot,
        result=result_snapshot,
        error=error_snapshot,
    )

