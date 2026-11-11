from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# Faixas aceitas por cada família de provider. A Anthropic aceita
# temperatura em [0, 1]; OpenAI e Gemini vão até 2. Enviar 1.6 para a
# Anthropic é 400, não "criatividade máxima", então o valor é fixado na
# borda em vez de recusado — a deliberação não deve parar por causa de
# um slider.
_TEMPERATURE_CEILING = {"anthropic": 1.0, "openai": 2.0, "gemini": 2.0, "ollama": 2.0}

# Modelos que rejeitam qualquer amostragem não-padrão. São os de
# raciocínio: a família devolve 400 se `temperature` vier diferente do
# default, e a lista existe porque não há como descobrir isso pela API
# antes de tentar.
_REASONING_MODEL_MARKERS = ("gpt-5", "o1", "o3", "o4", "opus-4-7", "opus-4-8")


@dataclass(frozen=True)
class SamplingParams:
    """O que o usuário pediu. Não necessariamente o que será enviado.

    `None` em qualquer campo significa "não definido pelo usuário" — o
    padrão do provider vale. Isso é diferente de zero: temperatura 0 é
    uma escolha (determinístico), ausência de temperatura é a falta de
    escolha.
    """

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {"temperature": self.temperature, "top_p": self.top_p, "max_tokens": self.max_tokens}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SamplingParams":
        if not data:
            return cls()
        return cls(
            temperature=_as_float(data.get("temperature")),
            top_p=_as_float(data.get("top_p")),
            max_tokens=_as_int(data.get("max_tokens")),
        )


@dataclass(frozen=True)
class ResolvedSampling:
    """O que de fato vai no payload, e o que foi descartado e por quê.

    Descartar em silêncio seria pior que ignorar: o usuário veria um
    slider em 0.2 e receberia respostas de temperatura 1, sem nada na
    tela explicando a diferença.
    """

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "notes": list(self.notes),
        }


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_reasoning_model(model: str) -> bool:
    lowered = (model or "").lower()
    return any(marker in lowered for marker in _REASONING_MODEL_MARKERS)


def resolve_sampling(
    params: SamplingParams,
    *,
    provider_kind: str,
    model: str,
    reasoning_effort: str = "off",
    supported_parameters: Optional[set[str]] = None,
    temperature_max: Optional[float] = None,
) -> ResolvedSampling:
    """Traduz a intenção do usuário no que o provider aceita.

    Regras que vêm da documentação de cada provider, não de suposição:

    - A Anthropic recusa `temperature` e `top_p` juntos no mesmo pedido
      ("cannot both be specified"). Quando os dois vêm preenchidos,
      prevalece a temperatura, que é o controle mais direto.
    - Com raciocínio estendido ligado, a amostragem é fixada pelo
      provider; mandar temperatura junto é erro.
    - Modelos de raciocínio (GPT-5, série o, Opus 4.7+) rejeitam
      qualquer valor não-padrão de amostragem.
    - A faixa da temperatura difere por família: [0, 1] na Anthropic,
      [0, 2] nas demais.
    """
    kind = (provider_kind or "").lower()
    notes: list[str] = []
    temperature = params.temperature
    top_p = params.top_p
    max_tokens = params.max_tokens

    if supported_parameters is not None:
        normalized_supported = {str(value).lower() for value in supported_parameters}
        if temperature is not None and "temperature" not in normalized_supported:
            notes.append("Este modelo não anuncia suporte a temperature; o parâmetro foi omitido.")
            temperature = None
        if top_p is not None and "top_p" not in normalized_supported:
            notes.append("Este modelo não anuncia suporte a top_p; o parâmetro foi omitido.")
            top_p = None
        if max_tokens is not None and not (
            {"max_tokens", "max_completion_tokens"} & normalized_supported
        ):
            notes.append("Este modelo não anuncia suporte a limite de tokens; o parâmetro foi omitido.")
            max_tokens = None

    if is_reasoning_model(model):
        if temperature is not None or top_p is not None:
            notes.append(
                "Modelo de raciocínio: temperatura e top_p são fixados pelo provider e foram omitidos."
            )
        return ResolvedSampling(max_tokens=max_tokens, notes=tuple(notes))

    # "default" (11/11/2026) = não enviar controle de raciocínio; o provider decide.
    # A amostragem pedida segue normalmente, como em "off".
    if reasoning_effort and reasoning_effort not in {"off", "default"}:
        if temperature is not None or top_p is not None:
            notes.append(
                "Raciocínio estendido ativo: o provider fixa a amostragem, então temperatura e top_p foram omitidos."
            )
        return ResolvedSampling(max_tokens=max_tokens, notes=tuple(notes))

    if temperature is not None:
        ceiling = temperature_max if temperature_max is not None else _TEMPERATURE_CEILING.get(kind, 2.0)
        clamped = max(0.0, min(ceiling, temperature))
        if clamped != temperature:
            notes.append(f"Temperatura ajustada de {temperature} para {clamped}: limite deste provider.")
        temperature = clamped

    if top_p is not None:
        clamped_top_p = max(0.0, min(1.0, top_p))
        if clamped_top_p != top_p:
            notes.append(f"top_p ajustado de {top_p} para {clamped_top_p}.")
        top_p = clamped_top_p

    if kind == "anthropic" and temperature is not None and top_p is not None:
        notes.append("A Anthropic aceita apenas um dos dois; top_p foi omitido em favor da temperatura.")
        top_p = None

    return ResolvedSampling(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        notes=tuple(notes),
    )

