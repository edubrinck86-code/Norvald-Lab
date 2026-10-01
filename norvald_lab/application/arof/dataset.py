from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from norvald_lab.application.arof.raw_observation import AROF_RAW_SCHEMA_VERSION, json_safe

AROF_MANIFEST_VERSION = "arof.manifest.v1"
AROF_COMPLETION_VERSION = "arof.completion.v1"
AROF_RESULT_VERSION = "arof.result.v1"

_ALLOWED_COMPLETION_STATUS = frozenset({"complete", "incomplete", "aborted"})


@dataclass(frozen=True)
class ExperimentManifest:
    """Especificação imutável de um experimento AROF.

    O manifesto descreve a condição antes da primeira chamada. Resultado,
    contagens e hashes não entram aqui; pertencem ao ExperimentCompletion.
    Assim a execução não reescreve retroativamente o que declarou testar.
    """

    experiment_id: str
    framework_version: str
    task: dict[str, Any]
    conditions: tuple[dict[str, Any], ...]
    models: tuple[dict[str, Any], ...]
    budget: dict[str, Any]
    corpus: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    manifest_version: str = AROF_MANIFEST_VERSION
    raw_schema_version: str = AROF_RAW_SCHEMA_VERSION
    notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id é obrigatório")
        if not self.framework_version.strip():
            raise ValueError("framework_version é obrigatório")
        if not self.conditions:
            raise ValueError("ao menos uma condição experimental é obrigatória")
        if not self.models:
            raise ValueError("ao menos um modelo é obrigatório")

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass(frozen=True)
class DatasetFileIntegrity:
    path: str
    sha256: str
    bytes: int
    lines: int
    valid_records: int
    invalid_records: int

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass(frozen=True)
class ExperimentCompletion:
    """Fechamento imutável produzido depois da coleta.

    Um experimento preparado possui manifest.json. Um experimento fechado
    possui também completion.json. A ausência do segundo arquivo significa
    que a coleta não foi certificada como encerrada.
    """

    experiment_id: str
    status: str
    files: tuple[DatasetFileIntegrity, ...]
    closed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completion_version: str = AROF_COMPLETION_VERSION
    raw_schema_version: str = AROF_RAW_SCHEMA_VERSION
    logical_executions: int = 0
    attempts: int = 0
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_COMPLETION_STATUS:
            raise ValueError(f"status de fechamento inválido: {self.status}")
        if self.logical_executions < 0 or self.attempts < 0:
            raise ValueError("contagens de execução não podem ser negativas")

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass(frozen=True)
class ReplayFilter:
    experiment_id: str | None = None
    run_id: str | None = None
    model: str | None = None
    task_label: str | None = None

    def matches(self, payload: dict[str, Any]) -> bool:
        if self.experiment_id is not None and payload.get("experiment_id") != self.experiment_id:
            return False
        if self.run_id is not None and payload.get("run_id") != self.run_id:
            return False
        if self.task_label is not None and payload.get("task_label") != self.task_label:
            return False
        if self.model is not None:
            observed_model = (
                (payload.get("result") or {}).get("model")
                or payload.get("requested_model")
            )
            if observed_model != self.model:
                return False
        return True


@dataclass(frozen=True)
class ReplayIssue:
    path: str
    line_number: int
    code: str
    message: str


@dataclass(frozen=True)
class ReplayRecord:
    path: str
    line_number: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class ReplayResult:
    records: tuple[ReplayRecord, ...]
    issues: tuple[ReplayIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class ExperimentResultView:
    """Projeção derivada para UI/API.

    Não substitui o RAW, não contém reasoning/resposta integral e pode ser
    reconstruída a partir dos artefatos científicos do experimento.
    """

    experiment_id: str
    condition_id: str
    source_session_id: str
    status: str
    failures: int
    executions: tuple[dict[str, Any], ...]
    condition_fingerprint: str
    library_corpus_fingerprint: str
    completed_at: str
    capacity: dict[str, Any] | None = None
    result_version: str = AROF_RESULT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))

