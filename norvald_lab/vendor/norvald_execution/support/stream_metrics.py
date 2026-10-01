from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StreamMetrics:
    """Ritmo da geração, não só o total.

    Duração total confunde três situações diferentes: o provider demorou
    a começar, gerou devagar, ou gerou muito. TTFT separa a primeira; a
    taxa e o intervalo entre tokens separam as outras duas.

    `inter_token_p95` existe ao lado da média porque a média esconde
    engasgo: um stream que entrega a 40 tokens/s com uma pausa de dois
    segundos no meio é percebido como travado, e a média não mostra isso.
    """

    started: float = field(default_factory=time.monotonic)
    first_token_at: Optional[float] = None
    last_token_at: Optional[float] = None
    chunks: int = 0
    characters: int = 0
    _gaps: List[float] = field(default_factory=list)

    def record(self, piece: str) -> None:
        now = time.monotonic()
        if self.first_token_at is None:
            self.first_token_at = now
        elif self.last_token_at is not None:
            self._gaps.append(now - self.last_token_at)
        self.last_token_at = now
        self.chunks += 1
        self.characters += len(piece)

    @property
    def ttft(self) -> Optional[float]:
        if self.first_token_at is None:
            return None
        return round(self.first_token_at - self.started, 6)

    @property
    def stream_duration(self) -> Optional[float]:
        """Do primeiro ao último token — só a geração.

        Separado do total, que inclui a espera antes de começar. Somar os
        dois num número só é o que impedia saber se o problema era fila
        ou velocidade.
        """
        if self.first_token_at is None or self.last_token_at is None:
            return None
        return round(self.last_token_at - self.first_token_at, 6)

    def as_dict(self, output_tokens: Optional[int] = None) -> Dict[str, Any]:
        duration = self.stream_duration
        # Tokens por segundo usa a contagem do provider quando existe.
        # Estimar por caracteres daria um número plausível e errado, e a
        # regra vale aqui como no resto da telemetria: não medido é
        # `None`, não uma aproximação disfarçada de medição.
        tokens_per_second = (
            round(output_tokens / duration, 2)
            if output_tokens and duration and duration > 0
            else None
        )
        return {
            "time_to_first_token": self.ttft,
            "stream_duration": duration,
            "chunks": self.chunks,
            "characters": self.characters,
            "tokens_per_second": tokens_per_second,
            "inter_token_avg": round(statistics.fmean(self._gaps), 6) if self._gaps else None,
            # p95 sobre poucas amostras não significa nada; abaixo de 20
            # intervalos o campo fica ausente em vez de enganar.
            "inter_token_p95": (
                round(sorted(self._gaps)[int(0.95 * (len(self._gaps) - 1))], 6)
                if len(self._gaps) >= 20
                else None
            ),
        }

