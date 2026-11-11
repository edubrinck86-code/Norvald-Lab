"""Deriva, do RAW, os fundamentos declarados, a estrutura e as afirmações de uma execução.

Regra dos fundamentos (aw9vf, 344-62 e 344-75; documentada em
docs/estudo/herd-medidas.md §8). Fundamento = alvo de uma relação de
fundamento (`derived_from`, `evidenced_by`, `documents`, as mesmas do
extrator da tabela tidy) DECLARADO no bloco, aceito ou não pelo validador.
Por quê declarado: o registro diz "declares a ground", e o validador recusa
quase todos (11/11/2026, 501 linhas de B1 em dados reais: 19 declararam
fundamento, 0 foram aceitos; a regra de tipos só admite, por exemplo,
inferência → afirmação). Medir só o aceito faria new_grounds ser sempre falso.
O alvo é classificado contra o Working Context que a execução recebeu e
contra a própria contribuição:

- alvo é unidade da própria contribuição: se for a decisão que seleciona a
  opção, não é fundamento (é a própria posição, que `changed_position` já
  mede); as demais viram `local`, identificadas pelo conteúdo normalizado
  (minúsculas, espaços colapsados), porque o `local_id` ("k1") é reutilizado
  em toda contribuição e não identifica nada;
- alvo é item do Working Context com autor: `own` se o autor é o próprio
  participante, `peer` se é outro;
- alvo é item do Working Context sem autor: `base`, pelo id;
- alvo que não existe em nenhum dos dois (id inventado, "evidence-<id>"):
  também `base`, pelo texto do id; é fundamento declarado que não resolve,
  e conta como declarado.

Nada de juízo semântico: a comparação é de identificador ou de texto igual.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from norvald_lab.application.arof.outcome_extract import OutcomeRow
from norvald_lab.domain.deliberation.contribution import Contribution
from norvald_lab.measures.ground import Ground
from norvald_lab.measures.read_contribution import ReadContribution


def normalized(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def _context_items(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    request = payload.get("request") or {}
    context = request.get("context") if isinstance(request, Mapping) else None
    text = context.get("working_context") if isinstance(context, Mapping) else None
    try:
        data = json.loads(text) if isinstance(text, str) and text.strip() else {}
    except ValueError:
        return {}
    items = data.get("items", []) if isinstance(data, dict) else []
    return {str(item.get("id")): item for item in items if isinstance(item, Mapping)}


def _content(payload: Mapping[str, Any]) -> str:
    result = payload.get("result")
    return str(result.get("content") or "") if isinstance(result, Mapping) else ""


class ContributionReader:
    def read(self, payload: Mapping[str, Any], row: OutcomeRow) -> ReadContribution:
        author = str(payload.get("participant_id") or "")
        contribution = Contribution.parse(_content(payload), author_id=author, round_number=int(payload.get("round_number") or 1))
        units = {unit.local_id: unit for unit in contribution.knowledge}
        selecting = {str(r.source) for r in contribution.relations if str(r.relation_type) == "selects"}
        context = _context_items(payload)
        grounds = set()
        for target in (t for t in row.grounding_targets.split(";") if t):
            ground = self._ground(target, units, selecting, context, author)
            if ground is not None:
                grounds.add(ground)
        structured = bool(int(row.items_accepted)) if row.items_accepted.isdigit() else bool(contribution.knowledge)
        claims = tuple((str(unit.type), str(unit.content)) for unit in contribution.knowledge)
        return ReadContribution(structured, tuple(sorted(grounds, key=lambda g: (g.scope, g.key))), claims)

    @staticmethod
    def _ground(target: str, units: Mapping[str, Any], selecting: set[str], context: Mapping[str, Mapping[str, Any]], author: str) -> Ground | None:
        if target in units:
            if target in selecting:
                return None
            return Ground("local", normalized(units[target].content))
        item = context.get(target)
        owner = str(item.get("author_id") or "") if item else ""
        if not owner:
            return Ground("base", target)
        return Ground("own" if owner == author else "peer", target)
