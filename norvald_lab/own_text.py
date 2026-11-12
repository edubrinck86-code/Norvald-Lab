"""Texto corrido da própria contribuição, para a condição B3T (estudo do formato, 12/11/2026).

B3 mostra a contribuição de B1 como itens e relações estruturados. B3T mostra
o mesmo conteúdo como texto: cada item vira um parágrafo, com a confiança
declarada, e cada relação vira uma frase. Nenhum conteúdo é acrescentado ou
retirado; muda só a forma. O teste `test_self_text.py` confere isso.
"""
from __future__ import annotations

from typing import Any, Dict


def render_own_text(snapshot: Dict[str, Any], author_id: str) -> str:
    items = [item for item in snapshot["items"] if item.get("author_id") == author_id]
    names = {item["id"]: f"o ponto {n}" for n, item in enumerate(items, 1)}
    lines = []
    for n, item in enumerate(items, 1):
        line = f"Ponto {n}: {item['content']}"
        if item.get("confidence"):
            line += f" (confiança: {item['confidence']})"
        lines.append(line)
    for rel in snapshot["relations"]:
        if rel.get("author_id") != author_id:
            continue
        source = names.get(rel["source_id"], rel["source_id"])
        if rel["relation_type"] == "selects":
            lines.append(f"Com {source}, você escolheu {rel['target_id']}.")
        else:
            lines.append(f"{source[0].upper() + source[1:]} tem a relação {rel['relation_type']} com {names.get(rel['target_id'], rel['target_id'])}.")
    return "Na rodada anterior, sua resposta foi:\n\n" + "\n".join(lines)
