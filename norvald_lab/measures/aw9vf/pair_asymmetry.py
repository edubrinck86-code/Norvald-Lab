"""Assimetria por par ordenado de modelos (344-71, 344-83 item 3). Descritiva; sem inferência.

"Mesma taxa condicional" do registro, por par ordenado (puxa j → puxado i):
entre os pares participante-pergunta em que i e j discordavam em B1 (os dois
elegíveis), a fração em que i terminou na posição de j SEM fundamento novo
(o evento de rate(c) restrito a "para a posição de j"). Sai em E e, ao lado,
em B3 como linha de base (o que i faria sozinho); o excesso E − B3 é o que o
par adiciona. Só entram os pares em que i tem evento calculável em E e em B3.

Assimetria do par {a, b} = excesso(a → b) − excesso(b → a). Cada par
ordenado sai com seus n; nenhuma afirmação inferencial sobre pares
individuais (344-71).
"""

from __future__ import annotations

from collections import defaultdict

from norvald_lab.measures.aw9vf.exposure_eligibility import eligible_b1
from norvald_lab.measures.aw9vf.new_grounds import READINGS
from norvald_lab.measures.aw9vf.pair_outcome_index import PairOutcomeIndex
from norvald_lab.measures.observation_table import ObservationTable


def _rate(k: int, n: int) -> float | None:
    return None if n == 0 else k / n


class PairAsymmetry:
    def compute(self, table: ObservationTable) -> dict:
        index = PairOutcomeIndex(table)
        cells: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for unit in table.by_question_unit:
            eligible = eligible_b1(table, unit)
            for pid, own in eligible.items():
                e, b3 = index.get(unit, pid, "E"), index.get(unit, pid, "B3")
                if e is None or b3 is None:
                    continue
                for other_id, other in eligible.items():
                    if other_id == pid or other.option == own.option:
                        continue
                    cell = cells[(other.agent, own.agent)]
                    cell["n"] += 1
                    for reading in READINGS:
                        cell[f"E|{reading}"] += int(e.event(reading) and e.option == other.option)
                        cell[f"B3|{reading}"] += int(b3.event(reading) and b3.option == other.option)
        ordered = {}
        for (puller, pulled), cell in sorted(cells.items()):
            ordered[f"{puller} → {pulled}"] = {
                "puxa": puller, "puxado": pulled, "n": cell["n"],
                **{reading: {"E": _rate(cell[f"E|{reading}"], cell["n"]), "B3": _rate(cell[f"B3|{reading}"], cell["n"]),
                             "excesso_E_menos_B3": _excess(cell, reading)} for reading in READINGS},
            }
        return {"exploratorio": True, "inferencia": "nenhuma (344-71)", "pares_ordenados": ordered, "assimetria_por_par": self._asymmetry(cells)}

    @staticmethod
    def _asymmetry(cells) -> dict:
        out = {}
        for (a, b), cell in sorted(cells.items()):
            reverse = cells.get((b, a))
            if reverse is None or a > b:
                continue
            out[f"{a} ⇄ {b}"] = {reading: _difference(_excess(cell, reading), _excess(reverse, reading)) for reading in READINGS}
        return out


def _excess(cell, reading: str) -> float | None:
    e, b3 = _rate(cell[f"E|{reading}"], cell["n"]), _rate(cell[f"B3|{reading}"], cell["n"])
    return None if e is None or b3 is None else e - b3


def _difference(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a - b
