from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

# As fases medidas. Nomes fixos porque a comparação entre rodadas só faz
# sentido se a mesma etapa se chamar sempre igual.
PHASE_CONTRIBUTION_PARSE = "contribution_parse"
PHASE_CONTRIBUTION_VALIDATION = "contribution_validation"
PHASE_WC_UPDATE = "wc_update"
PHASE_WC_DIFF = "wc_diff"
PHASE_SUMMARY = "summary_generation"
PHASE_CONFORMANCE = "conformance"
# A projeção do documento. Roda a cada leitura do CDD, não uma vez por
# rodada: é o caminho em que um custo por item vira custo por abertura
# de aba, e o único que o usuário sente diretamente.
PHASE_CDD_PROJECTION = "cdd_projection"


@dataclass(frozen=True)
class TelemetryEvent:
    """Quando algo rodou e quanto demorou.

    Separado de `WCEvidence` de propósito:

        WCEvidence     = o que aconteceu com o conhecimento
        TelemetryEvent = quando, onde e quanto custou processá-lo

    Misturar os dois faria a evidência do Working Context carregar
    milissegundos, e faria a duração de uma etapa parecer parte do
    conhecimento deliberativo. São ciclos de vida distintos: a evidência
    é sobre o WC e envelhece com ele; a telemetria é sobre a execução e
    interessa por janela de tempo.
    """

    phase: str
    duration_seconds: float
    started_at: Optional[str] = None
    session_id: Optional[str] = None
    round_number: Optional[int] = None
    participant_id: Optional[str] = None
    contribution_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at,
            "session_id": self.session_id,
            "round_number": self.round_number,
            "participant_id": self.participant_id,
            "contribution_id": self.contribution_id,
            "metadata": dict(self.metadata),
        }


class PhaseTimer:
    """Coletor de durações de um turno.

    Acumula em memória durante a execução e devolve eventos ao final. Não
    escreve em lugar nenhum sozinho: quem decide persistir é a fronteira
    que já conhece sessão e rodada.
    """

    def __init__(
        self,
        *,
        session_id: str | None = None,
        round_number: int | None = None,
        participant_id: str | None = None,
    ) -> None:
        self._session_id = session_id
        self._round_number = round_number
        self._participant_id = participant_id
        self._events: list[TelemetryEvent] = []

    @contextmanager
    def measure(self, phase: str, **metadata: Any) -> Iterator[None]:
        started_at = datetime.now(timezone.utc).isoformat()
        # Monotônico: relógio de parede pode andar para trás com NTP e
        # produzir duração negativa, que envenenaria qualquer média.
        start = time.monotonic()
        try:
            yield
        finally:
            self._events.append(
                TelemetryEvent(
                    phase=phase,
                    duration_seconds=round(time.monotonic() - start, 6),
                    started_at=started_at,
                    session_id=self._session_id,
                    round_number=self._round_number,
                    participant_id=self._participant_id,
                    metadata=dict(metadata),
                )
            )

    def with_contribution(self, contribution_id: str | None) -> list[TelemetryEvent]:
        """Carimba a contribuição, conhecida só depois da validação."""
        if contribution_id is None:
            return list(self._events)
        return [
            TelemetryEvent(**{**event.as_dict(), "contribution_id": contribution_id})
            for event in self._events
        ]

    @property
    def events(self) -> list[TelemetryEvent]:
        return list(self._events)

