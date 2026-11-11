"""Resolve a posição de uma execução: a opção aceita, ou a seleção indireta (regra 3).

Regra 3 (aprovada em 11/11/2026, vista no fumaca-2 com o Nemotron): quando a
decisão aponta (`selects`) para a decisão de um participante, e não para uma
opção, a posição é resolvida UM passo — a opção que aquela decisão escolheu —
e marcada como indireta. O validador recusa `decision → decision`, então a
linha chega aqui com `option_accepted` vazio e o id do item apontado em
`option_selected`.

Só valem as opções do enunciado (itens `option` sem autor no Working Context
da própria execução). Uma `option` criada por um participante não é opção da
pergunta: apontar para ela fica sem posição, em vez de virar um palpite.
Um passo só: se a decisão apontada também apontar para outra decisão, não há
posição (evita cadeia que ninguém declarou).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from norvald_lab.application.arof.outcome_extract import OutcomeRow


@dataclass(frozen=True)
class ResolvedPosition:
    option: str | None
    indirect: bool = False
    source_author: str = ""


def _working_context(payload: Mapping[str, Any]) -> dict:
    request = payload.get("request") or {}
    context = request.get("context") if isinstance(request, Mapping) else None
    text = context.get("working_context") if isinstance(context, Mapping) else None
    try:
        data = json.loads(text) if isinstance(text, str) and text.strip() else {}
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


class PositionResolver:
    def resolve(self, payload: Mapping[str, Any], row: OutcomeRow) -> ResolvedPosition:
        context = _working_context(payload)
        items = {str(item.get("id")): item for item in context.get("items", []) if isinstance(item, Mapping)}
        base_options = {item_id for item_id, item in items.items() if item.get("type") == "option" and not item.get("author_id")}
        if row.option_accepted and row.option_accepted in base_options:
            return ResolvedPosition(row.option_accepted)
        target = items.get(row.option_selected) if row.option_selected else None
        if target is None or target.get("type") != "decision":
            return ResolvedPosition(None)
        for relation in context.get("relations", []):
            if relation.get("relation_type") == "selects" and str(relation.get("source_id")) == row.option_selected:
                chosen = str(relation.get("target_id"))
                if chosen in base_options:
                    return ResolvedPosition(chosen, indirect=True, source_author=str(target.get("author_id") or ""))
        return ResolvedPosition(None)
