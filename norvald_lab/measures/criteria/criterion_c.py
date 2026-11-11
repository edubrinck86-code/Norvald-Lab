"""Critério C — a alteração se concentra nas decisões por margem mínima (2608.06940).

Unidade: participante com posição válida em B1. Valor em c: 1 se a posição
em c difere da própria B1. Grupos (regras 1 e 2, C usa todas): "divididas"
(B1 com maioria sem unanimidade + B1 sem maioria) × "unanimes"; e o
detalhe "maioria" e "sem_maioria".

Previsão: taxa de alteração em E maior nas divididas que nas unânimes,
diferença com intervalo acima de 0. A tabela fala de "alteração em E"; a
mesma diferença sobre Δ_pares (E − B3, que desconta a reconsideração
sozinha) sai ao lado, sem entrar no veredito.
"""

from __future__ import annotations

from norvald_lab.measures.b1_grouping import B1Grouping
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import CONDITIONS, CONTRASTS
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.statistic import Statistic
from norvald_lab.measures.verdict import directional


class CriterionC:
    letter = "C"
    source = "critério C (bloco 1.2); afirmação de 2608.06940"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        rates = IndicatorContrasts(sums, "C")
        for unit in table.by_question_unit:
            b1 = table.options(unit, "B1")
            group = B1Grouping.classify(b1.values()).group
            if group == "insuficiente":
                continue
            labels = ("unanimes",) if group == "unanime" else ("divididas", group)
            for pid, before in b1.items():
                values = {}
                for condition in CONDITIONS:
                    after = table.options(unit, condition).get(pid)
                    values[condition] = None if after is None else float(after != before)
                rates.add(unit[1], values, labels)
        stats = rates.statistics()
        for condition in CONDITIONS:
            stats[f"C|diferenca|nivel|{condition}"] = Statistic.difference_of_ratios(rates.level_keys("divididas", condition), rates.level_keys("unanimes", condition))
        for name in CONTRASTS:
            stats[f"C|diferenca|contraste|{name}"] = Statistic.difference_of_ratios(rates.contrast_keys("divididas", name), rates.contrast_keys("unanimes", name))
        intervals = bootstrap.run(sums, stats)
        primary = intervals["C|diferenca|nivel|E"]
        return {
            "fonte": self.source,
            "medida": "fração de participantes cuja posição difere da própria B1",
            "resultado": rates.organize(intervals),
            "divididas_menos_unanimes": {
                "niveis": {c: intervals[f"C|diferenca|nivel|{c}"].to_dict() for c in CONDITIONS},
                "contrastes": {name: intervals[f"C|diferenca|contraste|{name}"].to_dict() for name in CONTRASTS},
            },
            "veredito": directional(primary, expected="acima"),
        }
