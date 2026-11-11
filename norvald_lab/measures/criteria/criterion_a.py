"""Critério A — alteração de posição em direção à maioria (2610.35930).

População (regras 1 e 2): perguntas com maioria e sem unanimidade em B1;
dentro delas, os participantes que em B1 ficaram FORA da maioria. Unânimes e
sem maioria não entram: não há maioria para onde ir, ou não há quem esteja
fora dela.

Valor por participante em cada condição c: 1 se a posição em c é a opção
majoritária de B1, 0 se não. Em B1 vale 0 por construção. A maioria é a de
B1 porque é ela que E mostra (os pares em E veem as contribuições de B1).

Previsão: Δ_pares = M(E) − M(B3) > 0, intervalo acima de 0.
"""

from __future__ import annotations

from norvald_lab.measures.b1_grouping import B1Grouping
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import CONDITIONS, PRIMARY_CONTRAST
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.verdict import directional


class CriterionA:
    letter = "A"
    source = "critério A (bloco 1.2); afirmação de 2610.35930"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        rates = IndicatorContrasts(sums, "A")
        groups = {"unanime": 0, "maioria": 0, "sem_maioria": 0, "insuficiente": 0}
        for unit in table.by_question_unit:
            b1 = table.options(unit, "B1")
            grouping = B1Grouping.classify(b1.values())
            groups[grouping.group] += 1
            if grouping.group != "maioria":
                continue
            for pid, option in b1.items():
                if option == grouping.majority:
                    continue
                values = {}
                for condition in CONDITIONS:
                    chosen = table.options(unit, condition).get(pid)
                    values[condition] = None if chosen is None else float(chosen == grouping.majority)
                rates.add(unit[1], values)
        intervals = bootstrap.run(sums, rates.statistics())
        result = rates.organize(intervals) if rates.groups else {}
        primary = rates.interval(intervals, PRIMARY_CONTRAST) if rates.groups else None
        return {
            "fonte": self.source,
            "medida": "fração dos participantes fora da maioria de B1 que estão na opção majoritária",
            "perguntas_por_grupo_b1": groups,
            "resultado": result,
            "veredito": directional(primary, expected="acima") if primary else "indeterminado (sem dados)",
        }
