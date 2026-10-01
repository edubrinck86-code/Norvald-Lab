from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _opt_int(value: Any) -> Optional[int]:
    """Converte preservando a ausência.

    Provider que não informa a métrica devolve `None`, e `None` nunca
    vira zero: zero é uma medição válida (uma chamada que não usou
    cache) e é diferente de "este provider não reporta cache".
    """
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class ProviderUsage:
    """Consumo real de uma chamada, como o provider reportou.

    Nada aqui é estimado pelo Studio. Cada campo ou veio da resposta da
    API ou permanece `None`. `raw_usage` guarda o bloco original porque
    os providers reportam dimensões que o modelo normalizado ainda não
    prevê, e descartá-las tornaria o histórico irrecuperável.
    """

    provider: str = ""
    model: str = ""
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    cache_write_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    tool_tokens: Optional[int] = None
    modality_tokens: Optional[int] = None
    # Custo das ferramentas neste turno. Não vem do provider: é o que o
    # Studio ofereceu e quantos round-trips isso provocou.
    tools_available: Optional[int] = None
    tool_schema_bytes: Optional[int] = None
    llm_followups: Optional[int] = None
    raw_usage: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> Optional[int]:
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    @property
    def measured(self) -> bool:
        return self.total_tokens is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "tool_tokens": self.tool_tokens,
            "modality_tokens": self.modality_tokens,
            "tools_available": self.tools_available,
            "tool_schema_bytes": self.tool_schema_bytes,
            "llm_followups": self.llm_followups,
            "raw_usage": dict(self.raw_usage),
        }


def normalize_usage(raw: Dict[str, Any] | None, *, provider_kind: str, model: str,
                    request_id: Optional[str] = None, timestamp: Optional[str] = None) -> ProviderUsage:
    """Traduz o bloco de usage de cada API para o modelo comum.

    Os nomes divergem por provider — `input_tokens` na Anthropic,
    `prompt_tokens` na OpenAI, `promptTokenCount` no Gemini — e o
    mapeamento fica aqui, num lugar só, em vez de espalhado por cada
    adapter.
    """
    raw = raw or {}
    kind = (provider_kind or "").lower()

    if kind == "anthropic":
        usage = ProviderUsage(
            provider=provider_kind, model=model, request_id=request_id, timestamp=timestamp,
            input_tokens=_opt_int(raw.get("input_tokens")),
            output_tokens=_opt_int(raw.get("output_tokens")),
            cached_input_tokens=_opt_int(raw.get("cache_read_input_tokens")),
            cache_write_tokens=_opt_int(raw.get("cache_creation_input_tokens")),
            raw_usage=dict(raw),
        )
        return usage

    if kind == "gemini":
        details = raw.get("promptTokensDetails") or []
        modality = sum(_opt_int(d.get("tokenCount")) or 0 for d in details if d.get("modality") not in (None, "TEXT"))
        return ProviderUsage(
            provider=provider_kind, model=model, request_id=request_id, timestamp=timestamp,
            input_tokens=_opt_int(raw.get("promptTokenCount")),
            output_tokens=_opt_int(raw.get("candidatesTokenCount")),
            cached_input_tokens=_opt_int(raw.get("cachedContentTokenCount")),
            reasoning_tokens=_opt_int(raw.get("thoughtsTokenCount")),
            modality_tokens=modality or None,
            raw_usage=dict(raw),
        )

    # OpenAI-compatível (OpenAI, OpenRouter) e Ollama seguem o mesmo
    # formato de `usage`, com detalhes opcionais aninhados.
    prompt_details = raw.get("prompt_tokens_details") or {}
    completion_details = raw.get("completion_tokens_details") or {}
    return ProviderUsage(
        provider=provider_kind, model=model, request_id=request_id, timestamp=timestamp,
        input_tokens=_opt_int(raw.get("prompt_tokens", raw.get("prompt_eval_count"))),
        output_tokens=_opt_int(raw.get("completion_tokens", raw.get("eval_count"))),
        cached_input_tokens=_opt_int(prompt_details.get("cached_tokens")),
        reasoning_tokens=_opt_int(completion_details.get("reasoning_tokens")),
        raw_usage=dict(raw),
    )

