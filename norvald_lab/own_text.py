"""Texto corrido da própria contribuição, para a condição B3T (estudo do formato, 12/11/2026).

B3 mostra a contribuição de B1 como itens e relações estruturados. B3T mostra
o mesmo conteúdo como texto: cada item vira um parágrafo, com a confiança
declarada, e cada relação vira uma frase. Nenhum conteúdo é acrescentado ou
retirado; muda só a forma. O teste `test_self_text.py` confere isso.
"""
from __future__ import annotations

from typing import Any, Dict


# O texto sai no idioma da rodada: em 12/11/2026 a primeira versão escrevia em português
# dentro de prompts em inglês (conf2 é "en"), o que misturaria idioma com formato.
WORDS = {
    "pt-BR": {"header": "Na rodada anterior, sua resposta foi:", "point": "Ponto", "the_point": "o ponto",
              "confidence": "confiança", "selects": "Com {s}, você escolheu {t}.", "relation": "{s} tem a relação {r} com {t}."},
    "en": {"header": "In the previous round, your answer was:", "point": "Point", "the_point": "point",
           "confidence": "confidence", "selects": "With {s}, you chose {t}.", "relation": "{s} has the relation {r} with {t}."},
}


def render_own_text(snapshot: Dict[str, Any], author_id: str, language: str = "pt-BR") -> str:
    w = WORDS["en" if language.startswith("en") else "pt-BR"]
    items = [item for item in snapshot["items"] if item.get("author_id") == author_id]
    names = {item["id"]: f"{w['the_point']} {n}" for n, item in enumerate(items, 1)}
    lines = []
    for n, item in enumerate(items, 1):
        line = f"{w['point']} {n}: {item['content']}"
        if item.get("confidence"):
            line += f" ({w['confidence']}: {item['confidence']})"
        lines.append(line)
    for rel in snapshot["relations"]:
        if rel.get("author_id") != author_id:
            continue
        source = names.get(rel["source_id"], rel["source_id"])
        if rel["relation_type"] == "selects":
            lines.append(w["selects"].format(s=source, t=rel["target_id"]))
        else:
            line = w["relation"].format(s=source, r=rel["relation_type"], t=names.get(rel["target_id"], rel["target_id"]))
            lines.append(line[0].upper() + line[1:])
    return w["header"] + "\n\n" + "\n".join(lines)
