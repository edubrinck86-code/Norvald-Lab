"""Catálogo obtido pelos adapters existentes; sem inferência ou listas fixas."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from norvald_lab.settings import LocalSettings, credential_env, validate_address
from norvald_lab.vendor.norvald_execution.providers.llm_providers import build_provider
from norvald_lab.vendor.norvald_execution.providers.ollama_provider import OllamaProvider


def declared(capabilities, *names):
    if isinstance(capabilities, list):
        return any(name in capabilities for name in names)
    if isinstance(capabilities, dict):
        for name in names:
            v = capabilities.get(name)
            if isinstance(v, bool):
                return v
            if isinstance(v, dict) and isinstance(v.get("supported"), bool):
                return v["supported"]
    return None


def normalize_model(model, kind):
    metadata = model.raw_metadata or {}
    params = metadata.get("supported_parameters")
    parameter_names = list(params) if isinstance(params, (list, dict)) else None
    capabilities = metadata.get("capabilities")
    tools = any(p in parameter_names for p in ("tools", "tool_choice")) if parameter_names is not None else declared(capabilities, "tools", "tool_use", "function_calling")
    reasoning = any(p in parameter_names for p in ("reasoning", "reasoning_effort", "thinking")) if parameter_names is not None else declared(capabilities, "thinking", "reasoning")
    if isinstance(metadata.get("thinking"), bool):
        reasoning = metadata["thinking"]
    pricing = metadata.get("pricing") or {}
    free = None
    if isinstance(pricing, dict) and pricing.get("prompt") is not None and pricing.get("completion") is not None:
        try:
            values = [Decimal(str(v)) for v in pricing.values() if v is not None]
            if values and all(v.is_finite() and v >= 0 for v in values):
                free = all(v == 0 for v in values)
        except (InvalidOperation, ValueError):
            pass
    context = metadata.get("context_length") or metadata.get("inputTokenLimit") or metadata.get("max_input_tokens")
    if not isinstance(context, int) or context <= 0:
        context = None
    methods = metadata.get("supportedGenerationMethods")
    usable = kind != "gemini" or isinstance(methods, list) and "generateContent" in methods
    architecture = metadata.get("architecture") or {}
    if isinstance(architecture, dict) and isinstance(architecture.get("output_modalities"), list):
        usable = usable and "text" in architecture["output_modalities"]
    return {"id": model.id, "name": model.display_name, "vendor": model.vendor, "tools": tools,
            "reasoning": reasoning, "free": free, "local": kind == "ollama", "context_length": context,
            "pricing": {k: str(v) for k, v in pricing.items()} if isinstance(pricing, dict) else {},
            "supported_parameters": parameter_names, "usable": usable,
            "declaration_source": "provider_catalog", "dynamic_router": kind == "openrouter" and model.id in {"openrouter/auto", "openrouter/free"}}


class ModelCatalog:
    def __init__(self, settings: LocalSettings):
        self.settings = settings

    def provider(self, payload):
        if set(payload) - {"kind", "credential_env", "base_url", "refresh"}:
            raise ValueError("Catálogo aceita provedor, referência da credencial e endereço, nunca a chave.")
        kind = payload["kind"]
        c = self.settings.connection(kind)
        address = validate_address(payload.get("base_url") or c.get("base_url", ""))
        env = payload.get("credential_env") or credential_env(kind)
        if not isinstance(env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env):
            raise ValueError("Referência de credencial inválida.")
        key = self.settings.resolve(kind, env, address or None)
        if kind == "ollama":
            return OllamaProvider(address or "http://localhost:11434")
        if not key and kind != "openrouter":
            raise ValueError("Cadastre a chave em Configurações antes de consultar este provedor.")
        return build_provider(kind, key, address or None)

    async def get(self, payload):
        kind = payload["kind"]
        provider = self.provider(payload)
        try:
            models = await asyncio.wait_for(provider.list_models(), timeout=60)
            normalized = [normalize_model(m, kind) for m in models]
            result = {"kind": kind, "fetched_at": datetime.now(timezone.utc).isoformat(),
                      "models": sorted([m for m in normalized if m["usable"]], key=lambda m: m["name"].lower())}
            return result
        finally:
            await provider._client.aclose()

    async def test(self, kind):
        provider = self.provider({"kind": kind})
        try:
            ok = await asyncio.wait_for(provider.test_connection(), timeout=60)
            return {"kind": kind, "ok": bool(ok), "message": "Consulta de conexão concluída sem gerar resposta de modelo." if ok else "Chave recusada pelo provedor."}
        finally:
            await provider._client.aclose()
