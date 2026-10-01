from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ExecutionEvent:
    """Um evento de execução, com o recorte a que ele pertence.

    `scope` guarda as partes **nomeadas** que o domínio declarou —
    sessão e rodada no Studio, build e tentativa no Builder. Nomeadas,
    e não concatenadas, porque auditoria pergunta por parte: "tudo da
    rodada 3" é impossível de responder a partir de `s1:3:p2`.

    `execution_id` é derivado do scope e serve só para correlacionar as
    linhas de uma mesma execução. Quem audita usa o scope; quem
    correlaciona usa o id.
    """

    event_id: str
    event_type: str
    agent_id: str
    provider: str
    model: str
    status: str
    latency_ms: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None
    scope: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class ExecutionObserver(Protocol):
    """Observador opcional da execução; não conhece Dashboard ou armazenamento."""

    def record(self, event: ExecutionEvent) -> None:
        ...


class NullExecutionObserver:
    def record(self, event: ExecutionEvent) -> None:
        return None

