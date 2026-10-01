"""
Normalização de modelos — ADR-UX-011.

Os Providers devolvem exatamente o que suas APIs fornecem (nome bruto,
às vezes contexto/preço). Esta camada produz, a partir disso, uma
representação canônica usada por toda a plataforma (filtros, ícones,
grupamentos) — sem NUNCA inventar dado que a API não deu.

Regra de honestidade: capability/context/preço só aparecem quando
genuinamente extraídos de `raw_metadata` (ver providers). Sem isso,
ficam listas/valores vazios — nunca um placeholder fabricado.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.contracts.provider_model_profiles import (
    canonical_provider_kind,
    contract_capabilities,
    contract_parameters,
    provider_details as contract_provider_details,
)

# Flags = estado/forma de disponibilização (ADR-UX-011 §8) — não são
# capacidade técnica. Vêm dos sufixos entre parênteses no nome bruto,
# ex: "GPT-5 (Preview) (Free)".
_KNOWN_FLAGS = {
    "free": "free",
    "paid": "paid",
    "batch": "batch",
    "preview": "preview",
    "experimental": "experimental",
    "beta": "beta",
    "legacy": "legacy",
    "deprecated": "deprecated",
}

# Família conhecida por vendor — usada tanto pra extrair `family` do nome
# quanto pra resolução de ícone (§12: Modelo → Família → Vendor → ...).
_VENDOR_FAMILIES = {
    "anthropic": ["claude"],
    "openai": ["gpt", "o1", "o3", "o4"],
    "google": ["gemini", "gemma"],
    "meta": ["llama", "muse"],
    "meta-llama": ["llama", "muse"],
    "mistralai": ["mistral", "mixtral"],
    "mistral": ["mistral", "mixtral"],
    "deepseek": ["deepseek"],
    "qwen": ["qwen"],
    "x-ai": ["grok"],
    "xai": ["grok"],
    "cohere": ["command", "north"],
    "perplexity": ["sonar"],
    "nvidia": ["nemotron"],
    "poolside": ["laguna"],
    "inclusionai": ["ling"],
    "microsoft": ["phi"],
    "amazon": ["nova", "titan"],
    "databricks": ["dbrx"],
    "ai21": ["jamba"],
    "nousresearch": ["hermes"],
    "liquid": ["lfm"],
    "stabilityai": ["stable"],
    "01-ai": ["yi"],
    "moonshotai": ["kimi"],
    "z-ai": ["glm"],
    "z.ai": ["glm"],
    "zai": ["glm"],
    "zhipu": ["glm"],
    "zhipuai": ["glm"],
}

# Vendor canônico (minúsculo) → rótulo de exibição, só pros casos em que o
# provider devolve o vendor em formato não-canônico (ex: "meta-llama").
_VENDOR_ALIASES = {
    "meta-llama": "meta",
    "mistralai": "mistral",
    "x-ai": "xai",
    "google-genai": "google",
    "z-ai": "zai",
    "z.ai": "zai",
    "zhipu": "zai",
    "zhipuai": "zai",
}


@dataclass
class NormalizedModel:
    raw_name: str
    display_name: str
    id: str
    provider: str
    # A API literal sendo chamada (anthropic/openai/gemini/openrouter/
    # ollama) — o `kind` real da conexão configurada em Configurações.
    # Diferente de `provider` (nome que o usuário deu à conexão, livre)
    # e de `vendor` (quem fez o modelo — pode ser "google" mesmo se a
    # chamada real for via OpenRouter, não direto na API do Google).
    api_kind: str
    vendor: str
    family: Optional[str] = None
    variant: Optional[str] = None
    version: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    capability_sources: dict = field(default_factory=dict)
    description: Optional[str] = None
    created_at: Optional[str | int | float] = None
    input_modalities: List[str] = field(default_factory=list)
    output_modalities: List[str] = field(default_factory=list)
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    parameters: dict = field(default_factory=dict)
    provider_details: dict = field(default_factory=dict)
    execution_support: str = "unknown"
    execution_reason: Optional[str] = None
    price_input_per_million: Optional[float] = None
    price_output_per_million: Optional[float] = None
    canonical_id: str = ""
    raw_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "raw_name": self.raw_name,
            "display_name": self.display_name,
            "id": self.id,
            "provider": self.provider,
            "api_kind": self.api_kind,
            "vendor": self.vendor,
            "family": self.family,
            "variant": self.variant,
            "version": self.version,
            "aliases": self.aliases,
            "flags": self.flags,
            "capabilities": self.capabilities,
            "capability_sources": self.capability_sources,
            "description": self.description,
            "created_at": self.created_at,
            "input_modalities": self.input_modalities,
            "output_modalities": self.output_modalities,
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "parameters": self.parameters,
            "provider_details": self.provider_details,
            "execution_support": self.execution_support,
            "execution_reason": self.execution_reason,
            "price_input_per_million": self.price_input_per_million,
            "price_output_per_million": self.price_output_per_million,
            "canonical_id": self.canonical_id,
            "raw_metadata": self.raw_metadata,
        }


_PAREN_SUFFIX_RE = re.compile(r"\s*\(([^)]+)\)\s*$")
_VERSION_RE = re.compile(r"(\d+(?:\.\d+)?)")
_VENDOR_PREFIX_RE = re.compile(r"^([A-Za-z][A-Za-z0-9\- ]{1,20}):\s*")


def _strip_vendor_prefix(clean_name: str, vendor_key: str) -> str:
    """OpenRouter às vezes já prefixa o nome com o vendor ('Meta: Muse
    Spark 1.2') — se bater com o vendor resolvido, tiramos, porque o
    vendor já aparece como coluna/ícone separado (ADR-UX-011 §7 mostra
    display_name sempre sem esse prefixo)."""
    m = _VENDOR_PREFIX_RE.match(clean_name)
    if not m:
        return clean_name
    prefix = m.group(1).strip().lower().replace(" ", "-")
    if prefix == vendor_key or prefix.replace("-", "") == vendor_key.replace("-", ""):
        return clean_name[m.end():].strip()
    return clean_name


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _extract_flags(raw_name: str) -> tuple[str, List[str]]:
    """Remove sufixos entre parênteses do fim do nome e devolve (nome_limpo, flags).
    'GPT-5 (Preview) (Free)' -> ('GPT-5', ['preview', 'free'])."""
    name = raw_name
    flags: List[str] = []
    while True:
        m = _PAREN_SUFFIX_RE.search(name)
        if not m:
            break
        token = m.group(1).strip().lower()
        flag = _KNOWN_FLAGS.get(token)
        if flag:
            flags.insert(0, flag)
            name = name[: m.start()].rstrip()
        else:
            break
    return name.strip(), flags


def _guess_family(clean_name: str, vendor_key: str) -> Optional[str]:
    lower = clean_name.lower()
    for fam in _VENDOR_FAMILIES.get(vendor_key, []):
        if fam in lower:
            return fam
    return None


_FAMILY_VARIANTS = {
    "claude": ["opus", "sonnet", "haiku"],
    "gpt": ["turbo", "mini", "nano", "vision"],
    "gemini": ["flash", "pro", "ultra", "nano"],
    "gemma": ["it"],
    "llama": ["instruct", "chat", "vision"],
    "mistral": ["small", "medium", "large", "nemo"],
    "mixtral": ["instruct"],
    "deepseek": ["chat", "coder", "reasoner"],
    "qwen": ["turbo", "plus", "max", "coder", "vl"],
    "grok": ["mini", "fast"],
    "command": ["r", "r-plus", "light"],
    "nemotron": ["nano", "super", "ultra"],
    "laguna": ["xs", "s", "m", "l"],
    "phi": ["mini", "vision"],
    "nova": ["micro", "lite", "pro", "premier"],
    "hermes": ["pro"],
    "yi": ["large", "vision"],
}


def _guess_variant(clean_name: str, family: Optional[str]) -> Optional[str]:
    if not family:
        return None
    lower = clean_name.lower()
    for variant in _FAMILY_VARIANTS.get(family, []):
        if variant.replace("-", " ") in lower or variant in lower:
            return variant
    return None


def _guess_version(clean_name: str) -> Optional[str]:
    m = _VERSION_RE.search(clean_name)
    return m.group(1) if m else None


def _string_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip().lower() for part in re.split(r"[,+]", value) if part.strip()]
    return []


def _capability_supported(value) -> bool:
    if value is True:
        return True
    if isinstance(value, dict):
        return value.get("supported") is True
    return False


def _parameter_descriptor(raw_metadata: dict) -> dict:
    """Normaliza somente o que a API realmente declarou."""
    result: dict = {}
    supported = raw_metadata.get("supported_parameters")
    if isinstance(supported, list):
        for name in supported:
            key = str(name).strip()
            if key:
                result[key] = {"supported": True, "source": "provider_api", "scope": "model"}

    defaults = raw_metadata.get("default_parameters") or raw_metadata.get("defaultParams")
    if isinstance(defaults, dict):
        for key, value in defaults.items():
            entry = result.setdefault(str(key), {"supported": True, "source": "provider_api", "scope": "model"})
            entry["default"] = value

    mappings = {
        "temperature": ("temperature", "maxTemperature"),
        "top_p": ("topP", None),
        "top_k": ("topK", None),
        "max_tokens": ("max_tokens", None),
        "max_output_tokens": ("outputTokenLimit", None),
    }
    for canonical, (value_key, max_key) in mappings.items():
        if value_key in raw_metadata:
            entry = result.setdefault(canonical, {"supported": True, "source": "provider_api"})
            if canonical in {"temperature", "top_p", "top_k"}:
                entry.setdefault("default", raw_metadata.get(value_key))
            if canonical in {"max_tokens", "max_output_tokens"} and raw_metadata.get(value_key) is not None:
                entry["max"] = raw_metadata.get(value_key)
        if max_key and raw_metadata.get(max_key) is not None:
            entry = result.setdefault(canonical, {"supported": True, "source": "provider_api"})
            entry["max"] = raw_metadata.get(max_key)

    capabilities = raw_metadata.get("capabilities")
    if isinstance(capabilities, dict):
        effort = capabilities.get("effort")
        values: list[str] = []
        if isinstance(effort, dict) and _capability_supported(effort):
            values = [
                key
                for key, value in effort.items()
                if key != "supported" and _capability_supported(value)
            ]
        reasoning_effort = capabilities.get("reasoning_effort")
        if isinstance(reasoning_effort, list):
            values = [str(value) for value in reasoning_effort if str(value).strip()]
        if values:
            result["reasoning_effort"] = {
                "supported": True,
                "values": values,
                "source": "provider_api",
            }
            default_effort = capabilities.get("default_reasoning_effort")
            if default_effort not in (None, ""):
                result["reasoning_effort"]["default"] = default_effort
    sampling_defaults = raw_metadata.get("sampling_defaults")
    if isinstance(sampling_defaults, dict):
        aliases = {
            "temperature": "temperature",
            "p": "top_p",
            "k": "top_k",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "max_tokens_per_doc": "max_tokens_per_doc",
        }
        for raw_name, canonical in aliases.items():
            if raw_name not in sampling_defaults:
                continue
            entry = result.setdefault(
                canonical,
                {"supported": True, "source": "provider_api", "scope": "model"},
            )
            entry["supported"] = True
            entry["source"] = "provider_api"
            entry["scope"] = "model"
            entry["default"] = sampling_defaults[raw_name]

    return result


def _modalities_from_metadata(raw_metadata: dict) -> tuple[List[str], List[str]]:
    architecture = raw_metadata.get("architecture") or {}
    inputs = _string_list(
        raw_metadata.get("input_modalities")
        or raw_metadata.get("inputModalities")
        or architecture.get("input_modalities")
    )
    outputs = _string_list(
        raw_metadata.get("output_modalities")
        or raw_metadata.get("outputModalities")
        or architecture.get("output_modalities")
    )
    modality = str(architecture.get("modality", "") or raw_metadata.get("modality", "")).lower()
    if modality and "->" in modality:
        left, right = modality.split("->", 1)
        inputs = inputs or _string_list(left)
        outputs = outputs or _string_list(right)
    return inputs, outputs


def _execution_support(raw_metadata: dict, provider_kind: str, model_id: str) -> tuple[str, Optional[str]]:
    kind = canonical_provider_kind(provider_kind)
    methods = _string_list(raw_metadata.get("supportedGenerationMethods"))
    if methods:
        if any("generatecontent" in method.lower() for method in methods):
            return "supported", "A API lista generateContent para este modelo."
        return "unsupported", "A API não lista generateContent para este modelo."

    explicit = raw_metadata.get("capabilities")
    if isinstance(explicit, dict) and "completion_chat" in explicit:
        if explicit.get("completion_chat") is True:
            return "supported", "A API declara completion_chat."
        if explicit.get("completion_chat") is False:
            return "unsupported", "A API declara completion_chat=false."

    endpoints = {
        str(value).strip().lower()
        for value in (raw_metadata.get("endpoints") or [])
        if str(value).strip()
    }
    if endpoints:
        if "chat" in endpoints:
            return "supported", "O catálogo da API lista o endpoint chat para este modelo."
        return "unsupported", "O catálogo da API não lista o endpoint chat para este modelo."

    # O endpoint de modelos da Anthropic lista modelos da Messages API.
    if kind == "anthropic":
        return "supported", "Modelo listado pela Models API da Anthropic."

    # A API de Chat Completion da Z.AI documenta a família GLM como
    # conversacional, mas seu catálogo OpenAI-compatible pode retornar só IDs.
    if kind == "zai" and (model_id or "").lower().startswith("glm-"):
        return "supported", "Modelo GLM disponível pelo contrato de Chat Completion da Z.AI."

    return "unknown", None


def _capabilities_from_metadata(raw_metadata: dict) -> List[str]:
    """Deriva apenas capacidades explicitamente observáveis no catálogo."""
    caps: List[str] = []
    input_modalities, output_modalities = _modalities_from_metadata(raw_metadata)
    modality_set = set(input_modalities + output_modalities)
    if "image" in modality_set:
        caps.append("vision")
    if len(set(input_modalities)) > 1:
        caps.append("multimodal")
    if "image" in output_modalities:
        caps.append("images")

    supported = raw_metadata.get("supported_parameters") or []
    if isinstance(supported, list):
        normalized = {str(p).lower() for p in supported}
        if "tools" in normalized or "tool_choice" in normalized:
            caps.append("tools")
        if "response_format" in normalized or "structured_outputs" in normalized:
            caps.append("json")
        if "reasoning" in normalized or "reasoning_effort" in normalized:
            caps.append("reasoning")
        if any("web_search" in p for p in normalized):
            caps.append("web")

    methods = {value.lower() for value in _string_list(raw_metadata.get("supportedGenerationMethods"))}
    if methods:
        if any("generatecontent" in method for method in methods):
            caps.append("chat")
        if any("stream" in method for method in methods):
            caps.append("streaming")

    explicit = raw_metadata.get("capabilities")
    if isinstance(explicit, dict):
        aliases = {
            "completion_chat": "chat",
            "vision": "vision",
            "image_input": "vision",
            "pdf_input": "document",
            "function_calling": "tools",
            "tool_use": "tools",
            "tools": "tools",
            "completion_fim": "fim",
            "reasoning": "reasoning",
            "thinking": "reasoning",
            "effort": "reasoning",
            "structured_outputs": "json",
            "structured_output": "json",
            "citations": "citations",
            "code_execution": "code_execution",
            "batch": "batch",
            "context_management": "context_management",
            "classification": "classification",
            "fine_tuning": "fine_tuning",
        }
        for raw, canonical in aliases.items():
            if _capability_supported(explicit.get(raw)) and canonical not in caps:
                caps.append(canonical)
        if isinstance(explicit.get("reasoning_effort"), list) and explicit["reasoning_effort"] and "reasoning" not in caps:
            caps.append("reasoning")

    for raw, canonical in {
        "supports_vision": "vision",
        "supports_pdf": "document",
        "supports_tool_use": "tools",
        "supports_reasoning": "reasoning",
        "supports_thinking": "reasoning",
        "thinking": "reasoning",
        "supports_structured_outputs": "json",
    }.items():
        if raw_metadata.get(raw) is True and canonical not in caps:
            caps.append(canonical)

    return caps

_ID_SUFFIX_FLAGS = {
    "free": "free",
    "beta": "beta",
    "preview": "preview",
}


def _extract_id_flags(model_id: str) -> tuple[str, List[str]]:
    """'nvidia/nemotron-3-ultra:free' -> ('nvidia/nemotron-3-ultra', ['free'])."""
    if ":" not in model_id:
        return model_id, []
    base, suffix = model_id.rsplit(":", 1)
    flag = _ID_SUFFIX_FLAGS.get(suffix.strip().lower())
    return (base, [flag]) if flag else (model_id, [])


def normalize_model(raw: ModelInfo, provider_kind: str, provider_connection_name: str) -> NormalizedModel:
    vendor_raw = (raw.vendor or provider_kind or "").strip()
    vendor_key = _VENDOR_ALIASES.get(vendor_raw.lower(), vendor_raw.lower())
    vendor_display = vendor_key

    clean_name, flags = _extract_flags(raw.display_name)
    _base_id, id_flags = _extract_id_flags(raw.id)
    for f in id_flags:
        if f not in flags:
            flags.append(f)
    clean_name = _strip_vendor_prefix(clean_name, vendor_key)
    family = _guess_family(clean_name, vendor_key)
    variant = _guess_variant(clean_name, family)
    guessed_version = _guess_version(clean_name)

    metadata = raw.raw_metadata or {}
    canonical_kind = canonical_provider_kind(provider_kind)
    version_value = metadata.get("version")
    version = str(version_value) if version_value not in (None, "") else guessed_version
    aliases = [str(value) for value in (metadata.get("aliases") or []) if str(value).strip()] if isinstance(metadata.get("aliases"), list) else []
    # Providers usam nomes diferentes para o mesmo limite.
    context_window = (
        metadata.get("context_length")
        or metadata.get("max_context_length")
        or metadata.get("inputTokenLimit")
        or metadata.get("max_input_tokens")
    )
    max_output_tokens = (
        metadata.get("outputTokenLimit")
        or metadata.get("max_output_tokens")
        or metadata.get("max_tokens")
    )
    input_modalities, output_modalities = _modalities_from_metadata(metadata)
    description = metadata.get("description")
    created_at = metadata.get("created_at") or metadata.get("created")
    api_parameters = _parameter_descriptor(metadata)
    parameters = contract_parameters(canonical_kind, raw.id, metadata)
    for key, descriptor in api_parameters.items():
        parameters[key] = {**parameters.get(key, {}), **descriptor}
    pricing = metadata.get("pricing") or {}
    price_input = None
    price_output = None
    try:
        if "prompt" in pricing:
            price_input = round(float(pricing["prompt"]) * 1_000_000, 4)
        if "completion" in pricing:
            price_output = round(float(pricing["completion"]) * 1_000_000, 4)
    except (TypeError, ValueError):
        pass

    # xAI publica centavos por 100 milhões de tokens. Converter para
    # USD por 1 milhão mantém o contrato canônico do Studio.
    try:
        if price_input is None and metadata.get("prompt_text_token_price") is not None:
            price_input = round(float(metadata["prompt_text_token_price"]) / 10_000, 4)
        if price_output is None and metadata.get("completion_text_token_price") is not None:
            price_output = round(float(metadata["completion_text_token_price"]) / 10_000, 4)
    except (TypeError, ValueError):
        pass

    api_capabilities = _capabilities_from_metadata(metadata)
    contract_caps = contract_capabilities(canonical_kind, raw.id, metadata)
    capabilities = list(api_capabilities)
    for capability in contract_caps:
        if capability not in capabilities:
            capabilities.append(capability)
    capability_sources = {capability: "provider_api" for capability in api_capabilities}
    for capability, source in contract_caps.items():
        capability_sources.setdefault(capability, source)

    if metadata.get("archived") is True and "archived" not in flags:
        flags.append("archived")
    if metadata.get("is_deprecated") is True and "deprecated" not in flags:
        flags.append("deprecated")
    if metadata.get("finetuned") is True and "fine-tuned" not in flags:
        flags.append("fine-tuned")

    provider_details = contract_provider_details(canonical_kind, metadata)
    execution_support, execution_reason = _execution_support(metadata, canonical_kind, raw.id)

    canonical_parts = [vendor_key or "unknown", family or _slugify(clean_name)]
    if variant:
        canonical_parts.append(variant)
    if version:
        canonical_parts.append(version)
    canonical_parts.extend(flags)
    canonical_id = ".".join(p for p in canonical_parts if p)

    return NormalizedModel(
        raw_name=raw.display_name,
        display_name=clean_name,
        id=raw.id,
        provider=provider_connection_name,
        api_kind=canonical_kind,
        vendor=vendor_display,
        family=family,
        variant=variant,
        version=version,
        aliases=aliases,
        flags=flags,
        capabilities=capabilities,
        capability_sources=capability_sources,
        description=str(description) if description not in (None, "") else None,
        created_at=created_at,
        input_modalities=input_modalities,
        output_modalities=output_modalities,
        context_window=context_window,
        max_output_tokens=max_output_tokens,
        parameters=parameters,
        provider_details=provider_details,
        execution_support=execution_support,
        execution_reason=execution_reason,
        price_input_per_million=price_input,
        price_output_per_million=price_output,
        canonical_id=canonical_id,
        raw_metadata=dict(metadata),
    )


def normalize_models(models: List[ModelInfo], provider_kind: str, provider_connection_name: str) -> List[NormalizedModel]:
    return [normalize_model(m, provider_kind, provider_connection_name) for m in models]

