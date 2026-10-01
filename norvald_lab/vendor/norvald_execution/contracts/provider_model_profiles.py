"""Perfis de contrato para catálogos de modelos.

Esta camada não inventa metadata "recebida pela chave". Ela complementa o
catálogo com fatos do contrato HTTP do provider e marca a origem como
`provider_contract`. Dados devolvidos por /models continuam com precedência e
origem `provider_api`.

O objetivo é separar três coisas que antes estavam misturadas:
- catálogo específico daquela chave/conexão;
- contrato do endpoint/protocolo;
- inferência/heurística (que não entra aqui).
"""
from __future__ import annotations

import re
from typing import Any, Dict


_PROVIDER_ALIASES = {
    "z.ai": "zai",
    "z-ai": "zai",
    "z_ai": "zai",
    "zai-coding": "zai",
    "zai_coding": "zai",
    "zhipu": "zai",
    "zhipuai": "zai",
    "bigmodel": "zai",
    "mistralai": "mistral",
    "cohere-ai": "cohere",
}


def canonical_provider_kind(value: str) -> str:
    raw = (value or "").strip().lower()
    return _PROVIDER_ALIASES.get(raw, raw)


def _param(
    *,
    supported: bool | None = True,
    default: Any = None,
    minimum: float | int | None = None,
    maximum: float | int | None = None,
    values: list[str] | None = None,
    scope: str = "provider",
) -> dict:
    item: dict = {
        "source": "provider_contract",
        "scope": scope,
    }
    if supported is not None:
        item["supported"] = supported
    if default is not None:
        item["default"] = default
    if minimum is not None:
        item["min"] = minimum
    if maximum is not None:
        item["max"] = maximum
    if values:
        item["values"] = values
    return item


def _mistral_adjustable_reasoning(model_id: str) -> bool:
    model = (model_id or "").strip().lower()
    return (
        model == "mistral-small-latest"
        or model.startswith("mistral-small-")
        or model == "mistral-medium-3-5"
        or model.startswith("mistral-medium-3-5-")
    )


def _zai_max_tokens(model_id: str) -> tuple[int | None, int | None]:
    model = model_id.lower()
    if re.match(r"^glm-(?:5\.3|5\.2|5\.1|5|4\.7|4\.6)(?:$|-)", model):
        return 65536, 131072
    if model.startswith("glm-4.6v"):
        return 16384, 32768
    if re.match(r"^glm-4\.5(?:$|-)", model):
        return 65536, 98304
    if model.startswith("glm-4.5v"):
        return 16384, 16384
    if model == "glm-4-32b-0414-128k":
        return 16384, 16384
    return None, None


def _zai_reasoning_values(model_id: str) -> list[str] | None:
    model = model_id.lower()
    if model.startswith("glm-5.3"):
        return ["low", "high", "max"]
    if model.startswith("glm-5.2"):
        return ["none", "minimal", "low", "medium", "high", "xhigh", "max"]
    return None


def contract_parameters(provider_kind: str, model_id: str, raw_metadata: dict) -> Dict[str, dict]:
    """Parâmetros documentados no contrato do provider.

    Eles são fallback informativo. Quando /models traz defaults/limites por
    modelo, `model_taxonomy` mantém esses valores como `provider_api` e faz
    merge por cima deste contrato.
    """
    kind = canonical_provider_kind(provider_kind)
    model = (model_id or "").strip()

    if kind == "mistral":
        return {
            "temperature": _param(),
            "top_p": _param(),
            "max_tokens": _param(),
            "frequency_penalty": _param(),
            "presence_penalty": _param(),
            "random_seed": _param(),
            "stop": _param(),
            "response_format": _param(values=["text", "json_object", "json_schema"]),
            "tool_choice": _param(values=["auto", "none", "any", "required"]),
            "parallel_tool_calls": _param(default=True),
            "reasoning_effort": _param(
                supported=True if _mistral_adjustable_reasoning(model) else None,
                values=["none", "minimal", "low", "medium", "high", "xhigh"],
                scope="model" if _mistral_adjustable_reasoning(model) else "provider",
            ),
        }

    if kind == "cohere":
        sampling = raw_metadata.get("sampling_defaults")
        sampling = sampling if isinstance(sampling, dict) else {}
        params = {
            "temperature": _param(default=sampling.get("temperature")),
            "top_p": _param(default=sampling.get("p")),
            "top_k": _param(default=sampling.get("k")),
            "max_tokens": _param(),
            "frequency_penalty": _param(default=sampling.get("frequency_penalty")),
            "presence_penalty": _param(default=sampling.get("presence_penalty")),
            "stop": _param(),
            "seed": _param(),
            "response_format": _param(),
            "tools": _param(),
            "reasoning_effort": _param(values=["none", "high"]),
        }
        return params

    if kind == "zai":
        default_max_tokens, maximum_max_tokens = _zai_max_tokens(model)
        reasoning_values = _zai_reasoning_values(model)
        temperature_default = 0.6 if model.lower().startswith("glm-4.5") else 1.0
        top_p_default = 0.9 if model.lower() == "glm-4-32b-0414-128k" else 0.95
        params = {
            "do_sample": _param(default=True, values=["true", "false"]),
            "temperature": _param(default=temperature_default, minimum=0.0, maximum=1.0),
            "top_p": _param(default=top_p_default, minimum=0.01, maximum=1.0),
            "max_tokens": _param(default=default_max_tokens, minimum=1, maximum=maximum_max_tokens),
            "stream": _param(default=False, values=["true", "false"]),
            "tools": _param(),
            "tool_stream": _param(default=False),
            "thinking": _param(
                supported=model.lower().startswith(("glm-4.5", "glm-4.6", "glm-4.7", "glm-5")),
                values=["enabled", "disabled"],
            ),
        }
        if reasoning_values:
            params["reasoning_effort"] = _param(default="max", values=reasoning_values)
        return params

    return {}


def contract_capabilities(provider_kind: str, model_id: str, raw_metadata: dict) -> Dict[str, str]:
    """Capabilities que pertencem ao contrato, não ao payload de /models.

    Mantemos esta lista conservadora. Capabilities model-specific recebidas
    pelo catálogo continuam sendo a fonte preferida.
    """
    kind = canonical_provider_kind(provider_kind)
    caps: Dict[str, str] = {}

    if kind == "mistral" and _mistral_adjustable_reasoning(model_id):
        caps["reasoning"] = "provider_contract"

    if kind == "cohere":
        endpoints = {
            str(value).strip().lower()
            for value in (raw_metadata.get("endpoints") or [])
            if str(value).strip()
        }
        features = {
            str(value).strip().lower()
            for value in (raw_metadata.get("features") or [])
            if str(value).strip()
        }
        if "chat" in endpoints:
            caps["chat"] = "provider_api"
            caps["streaming"] = "provider_contract"
            # A Compatibility API da Cohere documenta function calling,
            # structured outputs e reasoning_effort (none/high).
            caps["tools"] = "provider_contract"
            caps["json"] = "provider_contract"
            caps["reasoning"] = "provider_contract"
        if any("tool" in value or "function" in value for value in features):
            caps["tools"] = "provider_api"
        if any("vision" in value or "image" in value for value in features):
            caps["vision"] = "provider_api"
        if any("reason" in value or "thinking" in value for value in features):
            caps["reasoning"] = "provider_api"
        if any("json" in value or "structured" in value for value in features):
            caps["json"] = "provider_api"

    if kind == "zai":
        model = (model_id or "").lower()
        if model.startswith("glm-"):
            caps["chat"] = "provider_contract"
            caps["streaming"] = "provider_contract"
            caps["tools"] = "provider_contract"
        if model.startswith(("glm-4.5", "glm-4.6", "glm-4.7", "glm-5")):
            caps["reasoning"] = "provider_contract"

    return caps


def provider_details(provider_kind: str, raw_metadata: dict) -> Dict[str, Any]:
    """Campos úteis específicos do provider, fora do contrato canônico."""
    kind = canonical_provider_kind(provider_kind)
    details: Dict[str, Any] = {}

    if kind == "mistral":
        for key in ("root", "root_version", "TYPE", "job", "owned_by", "archived"):
            value = raw_metadata.get(key)
            if value not in (None, "", [], {}):
                details[key] = value

    elif kind == "cohere":
        for key in (
            "endpoints",
            "default_endpoints",
            "features",
            "finetuned",
            "is_deprecated",
            "tokenizer_url",
        ):
            value = raw_metadata.get(key)
            if value not in (None, "", [], {}):
                details[key] = value

    elif kind == "zai":
        for key in ("owned_by", "object"):
            value = raw_metadata.get(key)
            if value not in (None, "", [], {}):
                details[key] = value

    return details

