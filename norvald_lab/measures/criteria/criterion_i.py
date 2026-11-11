"""Critério I — a exposição altera respostas que coincidiam com o gabarito (2611.04289).

População: participantes que ACERTARAM em B1, nas perguntas com gabarito.
Valor em c: 1 se a posição em c não coincide com o gabarito (transição
coincidente → não coincidente), 0 se coincide. Em B1 vale 0 por construção.

"Separadas pela posição da maioria": a maioria de B1 da pergunta —
unânime (todos certos), maioria certa, maioria errada, sem maioria.
Quem acertou numa pergunta de maioria errada estava em minoria; é aí que a
pressão dos pares é maior.

Previsão: Δ_pares > 0, intervalo acima de 0 (no total).
"""

from __future__ import annotations

from norvald_lab.measures.b1_grouping import B1Grouping
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import CONDITIONS, PRIMARY_CONTRAST
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.verdict import INDETERMINADO, directional


def majority_label(grouping: B1Grouping, answer: str) -> str:
    if grouping.group == "unanime":
        return "unanime"
    if grouping.group == "maioria":
        return "maioria_certa" if grouping.majority == answer else "maioria_errada"
    return grouping.group


class CriterionI:
    letter = "I"
    source = "critério I (bloco 1.2); afirmação de 2611.04289"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        rates = IndicatorContrasts(sums, "I")
        for unit, by_condition in table.by_question_unit.items():
            answer = table.answer(unit[1])
            if answer is None:
                continue
            label = majority_label(B1Grouping.classify(table.options(unit, "B1").values()), answer)
            for pid, row in by_condition.get("B1", {}).items():
                if not row.correct:
                    continue
                values = {}
                for condition in CONDITIONS:
                    later = by_condition.get(condition, {}).get(pid)
                    values[condition] = None if later is None or later.correct is None else float(not later.correct)
                rates.add(unit[1], values, ("todas", label))
        intervals = bootstrap.run(sums, rates.statistics())
        primary = rates.interval(intervals, PRIMARY_CONTRAST) if rates.groups else None
        return {
            "fonte": self.source,
            "medida": "fração dos que acertaram em B1 que deixam de coincidir com o gabarito",
            "resultado": rates.organize(intervals),
            "veredito": directional(primary, expected="acima") if primary else INDETERMINADO,
        }
