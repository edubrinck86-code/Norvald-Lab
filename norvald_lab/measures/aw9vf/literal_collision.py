"""Colisão literal entre participantes na onda cega (344-83 item 5). Exploratória.

Uma colisão é uma afirmação declarada com conteúdo byte a byte idêntico em
duas contribuições da mesma pergunta e onda (B1 e, ao lado, B2, que também é
cega). Compara as strings exatas, sem normalizar nada (nem espaço, nem caixa):
é o observável mais barato de redundância, determinístico, sem embedding nem
juiz. Por par de autores (agentes) e por onda saem só contagens, nunca o
texto da afirmação. Cada string distinta compartilhada pelo par numa pergunta
conta uma vez. `colisoes_em_decisoes` é o subconjunto em que a string é
conteúdo de uma unidade `decision` nos dois autores (a mais provável de
coincidir só porque a opção escolhida é a mesma).
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from norvald_lab.measures.observation_table import ObservationTable

WAVES = ("B1", "B2")


class LiteralCollision:
    def compute(self, table: ObservationTable) -> dict:
        out = {"exploratorio": True, "texto_no_relatorio": False, "ondas": {}}
        for wave in WAVES:
            pairs: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
            for unit, by_condition in table.by_question_unit.items():
                rows = [row for row in by_condition.get(wave, {}).values() if row.claims]
                for a, b in combinations(sorted(rows, key=lambda r: r.agent), 2):
                    shared = {c for _, c in a.claims if c} & {c for _, c in b.claims if c}
                    decisions = {c for t, c in a.claims if t == "decision" and c} & {c for t, c in b.claims if t == "decision" and c}
                    cell = pairs[(a.agent, b.agent)]
                    cell["itens_comparados"] += 1
                    cell["itens_com_colisao"] += int(bool(shared))
                    cell["colisoes"] += len(shared)
                    cell["colisoes_em_decisoes"] += len(decisions)
            compared = sum(c["itens_comparados"] for c in pairs.values())
            colliding = sum(c["itens_com_colisao"] for c in pairs.values())
            out["ondas"][wave] = {
                "itens_par_comparados": compared, "itens_par_com_colisao": colliding,
                "taxa": colliding / compared if compared else None, "colisoes": sum(c["colisoes"] for c in pairs.values()),
                "por_par_de_autores": {f"{a} × {b}": dict(cell) for (a, b), cell in sorted(pairs.items())},
            }
        return out
