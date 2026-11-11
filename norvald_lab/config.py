"""Contrato portátil. Dados entram por valor; credenciais entram pelo ambiente."""
from __future__ import annotations

import copy
import math
import re
from typing import Any
from urllib.parse import urlsplit

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}\Z")
ENV = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def identifier(value: Any, field: str = "id") -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"{field}: use letras, números, ponto, hífen ou sublinhado (1–120 caracteres).")
    return value


def _keys(value, allowed, field):
    if not isinstance(value, dict):
        raise ValueError(f"{field} deve ser um objeto.")
    unknown = set(value) - set(allowed.split())
    if unknown:
        raise ValueError(f"{field}: campos desconhecidos: {', '.join(sorted(unknown))}")


def _text(value, field, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f"{field} deve conter texto.")
    return value


def _positive(value, field):
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} deve ser inteiro positivo.")
    return value


def validate_spec(payload: dict) -> dict:
    """Validação antes de escrever manifesto ou criar clientes de rede."""
    _keys(payload, "schema_version experiment_id task participants providers documents working_context repetitions condition budget mode source language", "experimento")
    spec = copy.deepcopy(payload)
    if spec.setdefault("schema_version", "norvald.lab.spec.v1") != "norvald.lab.spec.v1":
        raise ValueError("schema_version não suportada.")
    identifier(spec.get("experiment_id"), "experiment_id")
    if spec.setdefault("mode", "demo") not in {"demo", "live"}:
        raise ValueError("mode deve ser demo ou live.")
    # `language` é opcional e NÃO ganha valor padrão no spec: acrescentar a
    # chave mudaria a impressão digital de specs antigos, e um spec sem o
    # campo precisa gerar exatamente os mesmos requests de sempre (pt-BR).
    if "language" in spec and spec["language"] not in {"pt-BR", "en"}:
        raise ValueError("language deve ser pt-BR ou en.")
    task = spec.get("task")
    _keys(task, "id objective instructions", "task")
    identifier(task.get("id"), "task.id")
    _text(task.get("objective"), "task.objective")
    _text(task.setdefault("instructions", ""), "task.instructions", empty=True)
    participants = spec.get("participants")
    if not isinstance(participants, list) or not participants:
        raise ValueError("Informe pelo menos um participante.")
    ids = []
    for p in participants:
        _keys(p, "id name role provider model reasoning_effort sampling sampling_with_reasoning", "participante")
        ids.append(identifier(p.get("id"), "participant.id"))
        for key in ("provider", "model"):
            _text(p.get(key), f"participant.{key}")
        _text(p.setdefault("name", p["id"]), "participant.name")
        _text(p.setdefault("role", "Analista"), "participant.role")
        if p.setdefault("reasoning_effort", "off") not in {"default", "off", "none", "minimal", "low", "medium", "high", "xhigh", "max"}:
            raise ValueError("reasoning_effort inválido.")
        if not isinstance(p.get("sampling_with_reasoning", False), bool):
            raise ValueError("sampling_with_reasoning deve ser true ou false.")
        sampling = p.setdefault("sampling", {})
        _keys(sampling, "temperature top_p max_tokens", "sampling")
        for key, upper in (("temperature", 2), ("top_p", 1)):
            val = sampling.get(key)
            if val is not None and (type(val) not in (int, float) or not math.isfinite(val) or not 0 <= val <= upper):
                raise ValueError(f"sampling.{key} fora da faixa [0, {upper}].")
        if sampling.get("max_tokens") is not None:
            _positive(sampling["max_tokens"], "sampling.max_tokens")
    if len(ids) != len(set(ids)):
        raise ValueError("IDs de participantes duplicados.")
    providers = spec.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise ValueError("Informe providers.")
    for name, provider in providers.items():
        identifier(name, "provider.id")
        _keys(provider, "kind credential_env base_url", "provider")
        _text(provider.get("kind"), "provider.kind")
        if spec["mode"] == "demo" and provider["kind"] != "demo":
            raise ValueError("Demonstração aceita apenas o provider demo, sem rede.")
        if spec["mode"] == "live" and provider["kind"] == "demo":
            raise ValueError("Experimento real não pode misturar respostas simuladas.")
        if provider.get("credential_env") and not ENV.fullmatch(provider["credential_env"]):
            raise ValueError("credential_env deve ser o nome de uma variável, nunca a chave.")
        if provider.get("base_url"):
            url = urlsplit(provider["base_url"])
            if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError("base_url deve ser HTTP(S), sem credenciais, query ou fragmento.")
    if any(p["provider"] not in providers for p in participants):
        raise ValueError("Participante aponta para provider não declarado.")
    documents = spec.setdefault("documents", [])
    if not isinstance(documents, list):
        raise ValueError("documents deve ser uma lista.")
    docids = []
    for doc in documents:
        _keys(doc, "id title text source", "documento")
        docids.append(identifier(doc.get("id"), "document.id"))
        _text(doc.get("title"), "document.title")
        _text(doc.get("text"), "document.text")
        _text(doc.setdefault("source", ""), "document.source", empty=True)
    if len(docids) != len(set(docids)):
        raise ValueError("IDs de documentos duplicados.")
    _positive(spec.setdefault("repetitions", 1), "repetitions")
    if not isinstance(spec.setdefault("working_context", {}), dict):
        raise ValueError("working_context deve ser objeto.")
    condition = spec.setdefault("condition", {})
    _keys(condition, "id exposure prior_experiment tools max_tool_calls max_tool_iterations", "condition")
    identifier(condition.setdefault("id", "B1"), "condition.id")
    if condition.setdefault("exposure", "blind") not in {"blind", "self", "exposed", "stance"}:
        raise ValueError("exposure deve ser blind, self, exposed ou stance.")
    if condition["exposure"] == "blind" and condition.get("prior_experiment"):
        raise ValueError("Condição cega não recebe respostas anteriores.")
    if condition["exposure"] != "blind":
        identifier(condition.get("prior_experiment"), "condition.prior_experiment")
        if condition["prior_experiment"] == spec["experiment_id"]:
            raise ValueError("Experimento não pode usar a si próprio como origem.")
        if condition["exposure"] in {"exposed", "stance"} and len(ids) < 2:
            raise ValueError("Exposição a pares exige pelo menos dois participantes.")
    if condition.setdefault("tools", "off") not in {"off", "corpus"}:
        raise ValueError("tools deve ser off ou corpus.")
    for name in ("max_tool_calls", "max_tool_iterations"):
        if condition.get(name) is not None:
            _positive(condition[name], name)
    budget = spec.setdefault("budget", {})
    _keys(budget, "max_concurrency max_concurrency_per_provider timeout_seconds max_logical_executions", "budget")
    planned = len(participants) * spec["repetitions"]
    for name, default in (("max_concurrency", 3), ("max_concurrency_per_provider", 2), ("timeout_seconds", 300), ("max_logical_executions", planned)):
        _positive(budget.setdefault(name, default), name)
    if planned > budget["max_logical_executions"]:
        raise ValueError("Execuções planejadas excedem o orçamento declarado.")
    source = spec.setdefault("source", {})
    _keys(source, "repository commit session_id notes", "source")
    for name, val in source.items():
        _text(val, f"source.{name}", empty=True)
    return spec
