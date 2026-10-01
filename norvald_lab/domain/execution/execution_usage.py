from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from norvald_lab.domain.telemetry.pricing import price_usage
from norvald_lab.domain.telemetry.provider_usage import normalize_usage


@dataclass(frozen=True)
class ExecutionUsage:
    """O que custou produzir uma contribuição.

    Vive no domínio pelo mesmo motivo que `raw_text` e `reasoning`: é
    procedência do turno, não mecânica de orquestração. Sem isso não há
    como acompanhar consumo — e o dado é irrecuperável depois, porque
    só o Provider sabe reportá-lo no momento da resposta.

    Todo campo é opcional de propósito. Provider que não reporta tokens
    devolve `None`, e `None` significa "não reportado" — nunca zero.
    Zero é uma medição válida (uma chamada que não gastou nada) e não
    pode ser confundido com ausência de medição, que foi exatamente o
    defeito da rota de auditoria anterior.
    """

    provider: str = ""
    model: str = ""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    duration_seconds: Optional[float] = None
    cost: Optional[float] = None
    # Consumo normalizado e custo calculado. Ficam ao lado do resumo
    # antigo em vez de substituí-lo para não quebrar quem já lê `cost`.
    provider_usage: Optional[Dict[str, Any]] = None
    provider_cost: Optional[Dict[str, Any]] = None
    context_size: Optional[Dict[str, Any]] = None
    # Segundos até o primeiro token. `None` quando não houve streaming.
    time_to_first_token: Optional[float] = None

    @property
    def total_tokens(self) -> Optional[int]:
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "duration_seconds": self.duration_seconds,
            "cost": self.cost,
            "provider_usage": self.provider_usage,
            "provider_cost": self.provider_cost,
            "context_size": self.context_size,
            "time_to_first_token": self.time_to_first_token,
        }

    @classmethod
    def from_result(cls, result: Any) -> "ExecutionUsage":
        """Lê um ExecutionResult sem acoplar o domínio ao contrato dele.

        Um Provider que não informa tokens devolve 0 no ExecutionResult
        (o dataclass tem default 0), e aqui isso vira `None` só quando o
        turno inteiro veio zerado — caso em que nada foi medido de fato.
        """
        input_tokens = getattr(result, "input_tokens", 0) or 0
        output_tokens = getattr(result, "output_tokens", 0) or 0
        measured = bool(input_tokens or output_tokens)
        metadata = getattr(result, "metadata", None) or {}
        provider = getattr(result, "provider", "") or ""
        model = getattr(result, "model", "") or ""

        # O custo é calculado agora, com a tabela vigente, e gravado.
        # Recalcular depois com preços novos reescreveria a história.
        usage = normalize_usage(
            metadata.get("raw_usage"),
            provider_kind=provider,
            model=model,
            request_id=metadata.get("request_id"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        # Métricas de ferramenta são do Studio, não do provider; entram
        # aqui para viajar junto do resto do consumo do turno.
        usage = replace(
            usage,
            tools_available=metadata.get("tools_available"),
            tool_schema_bytes=metadata.get("tool_schema_bytes"),
            llm_followups=metadata.get("llm_followups"),
        )
        cost = price_usage(usage)

        return cls(
            provider=getattr(result, "provider", "") or "",
            model=getattr(result, "model", "") or "",
            input_tokens=input_tokens if measured else None,
            output_tokens=output_tokens if measured else None,
            duration_seconds=getattr(result, "duration_seconds", None),
            cost=cost.total_cost if cost.priced else metadata.get("cost"),
            provider_usage=usage.to_dict(),
            provider_cost=cost.to_dict(),
            context_size=metadata.get("context_size"),
            time_to_first_token=metadata.get("time_to_first_token"),
        )

