"""Ferramenta inválida sai do catálogo; o turno segue.

Três incidentes seguidos tiveram a mesma forma: um item do catálogo que o
provider recusa faz a API rejeitar a requisição inteira, e o especialista
falha sem produzir nada — mesmo que aquela ferramenta nem fosse usada
naquele turno. Foram um nome com ponto (OpenAI-compatible) e um schema
com `$schema`/`additionalProperties` (Gemini).

A causa comum não é o formato específico: é o catálogo ser tudo-ou-nada.
Um servidor MCP novo, declarando o que sua biblioteca de validação gerar,
derruba todos os especialistas daquele provider de uma vez.

Aqui o custo passa a ser proporcional: perde-se a ferramenta problemática,
não a deliberação. O que é descartado fica registrado para poder ser
corrigido — silenciar seria trocar uma falha visível por uma ausência que
ninguém explica.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple

if TYPE_CHECKING:  # evita ciclo: `tools` não importa este módulo, mas os
    # providers importam ambos e a ordem de carga varia.
    from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolDefinition

logger = logging.getLogger(__name__)

#: Limite mais restritivo entre os providers em uso.
MAX_NAME_LENGTH = 64

_VALID_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")


def _describe(reason: str, tool: "ToolDefinition") -> str:
    return f"{tool.name}: {reason}"


def valid_tools(
    tools: List["ToolDefinition"],
    *,
    provider_label: str,
    extra_check: Callable[["ToolDefinition"], str | None] | None = None,
) -> Tuple[List["ToolDefinition"], List[str]]:
    """Separa o catálogo entre o que o provider aceita e o que não.

    `extra_check` deixa cada provider acrescentar a própria regra sem
    duplicar as comuns; devolve o motivo da recusa, ou `None`.
    """
    aceitos: List["ToolDefinition"] = []
    recusados: List[str] = []
    vistos: set[str] = set()

    for tool in tools:
        motivo: str | None = None

        if not tool.name:
            motivo = "sem nome"
        elif not _VALID_NAME.match(tool.name):
            motivo = "nome com caractere fora de a-z A-Z 0-9 _ -"
        elif len(tool.name) > MAX_NAME_LENGTH:
            motivo = f"nome acima de {MAX_NAME_LENGTH} caracteres"
        elif tool.name in vistos:
            # Nome repetido faz o provider recusar a lista, e mesmo que
            # aceitasse não haveria como saber qual foi chamada.
            motivo = "nome repetido no catálogo"
        elif not isinstance(tool.parameters, dict):
            motivo = "parameters não é um objeto"
        elif extra_check is not None:
            motivo = extra_check(tool)

        if motivo:
            recusados.append(_describe(motivo, tool))
            continue

        vistos.add(tool.name)
        aceitos.append(tool)

    if recusados:
        logger.warning(
            "%s: %d ferramenta(s) fora do catálogo desta chamada — %s",
            provider_label,
            len(recusados),
            "; ".join(recusados),
        )
    return aceitos, recusados


def sanitize_name(name: str) -> str:
    """Nome aceito por qualquer provider, preservando a legibilidade."""
    limpo = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).strip("_")
    return (limpo or "ferramenta")[:MAX_NAME_LENGTH]


def prune_schema(schema: Any, allowed_keys: set[str]) -> Any:
    """Poda um schema às chaves que o provider reconhece.

    Campos fora da lista são restrições adicionais ou metadados, nunca a
    estrutura que o modelo precisa para preencher o argumento — por isso
    removê-los é seguro, enquanto mantê-los custa a requisição inteira.
    """
    if isinstance(schema, list):
        return [prune_schema(item, allowed_keys) for item in schema]
    if not isinstance(schema, dict):
        return schema

    podado: Dict[str, Any] = {}
    for chave, valor in schema.items():
        if chave not in allowed_keys:
            continue
        if chave == "properties" and isinstance(valor, dict):
            podado[chave] = {nome: prune_schema(sub, allowed_keys) for nome, sub in valor.items()}
        elif chave in ("items", "anyOf", "oneOf"):
            podado[chave] = prune_schema(valor, allowed_keys)
        else:
            podado[chave] = valor

    if podado.get("type") == "object" and "properties" not in podado:
        podado["properties"] = {}
    return podado

