"""Critério G — consenso falso acima do acaso (JuryProbe, 2608.20607).

Braço de gabarito, só B1, só perguntas em que todos os participantes da
rodada têm posição válida (P(todos erram) só tem sentido com o painel
inteiro). Razão = P(todos erram) / Π_i taxa de erro de i, com as taxas
calculadas nas mesmas perguntas. Sob independência a razão é 1.

Previsão: razão > 1, intervalo acima de 1. Produto de taxas zero (algum
modelo nunca erra nessas perguntas) deixa a razão indefinida.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.statistic import Statistic, Totals, ratio_of
from norvald_lab.measures.verdict import directional


class CriterionG:
    letter = "G"
    source = "critério G (bloco 1.2); afirmação do JuryProbe, 2608.20607"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        agents: set[str] = set()
        excluded = 0
        for unit, by_condition in table.by_question_unit.items():
            if table.answer(unit[1]) is None:
                continue
            rows = list(by_condition.get("B1", {}).values())
            if not rows or any(row.correct is None for row in rows):
                excluded += 1
                continue
            cluster = unit[1]
            sums.add(cluster, "G|N")
            sums.add(cluster, "G|todos", float(all(not row.correct for row in rows)))
            for row in rows:
                agents.add(row.agent)
                sums.add(cluster, f"G|{row.agent}|n")
                sums.add(cluster, f"G|{row.agent}|s", float(not row.correct))

        def product(t: Totals) -> float | None:
            value = 1.0
            for agent in sorted(agents):
                rate = ratio_of(t, f"G|{agent}|s", f"G|{agent}|n")
                if rate is None:
                    return None
                value *= rate
            return value if agents else None

        def ratio(t: Totals) -> float | None:
            p_all, prod = ratio_of(t, "G|todos", "G|N"), product(t)
            return None if p_all is None or not prod else p_all / prod

        stats = {"p_todos_erram": Statistic.ratio("G|todos", "G|N"), "produto_taxas": Statistic(product, "G|N"), "razao": Statistic(ratio, "G|N")}
        intervals = bootstrap.run(sums, stats)
        return {
            "fonte": self.source,
            "medida": "P(todos erram em B1) ÷ produto das taxas individuais de erro",
            "resultado": {name: interval.to_dict() for name, interval in intervals.items()},
            "perguntas_excluidas_painel_incompleto": excluded,
            "veredito": directional(intervals["razao"], expected="acima", reference=1.0),
        }
