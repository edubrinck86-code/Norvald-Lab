"""Critério D — divergência entre modelos maior que dentro do mesmo modelo (2609.31013).

Por pergunta (todas):
- dentro: fração dos participantes com posição em B1 e em B2 cuja B2 difere
  da B1 (o mesmo modelo, às cegas, em sessão nova);
- entre: fração de pares de participantes distintos que discordam em B1
  (`panel_agreement.discordance`).
As duas são frações por pergunta e se agregam com o mesmo peso por pergunta.

Previsão: entre − dentro > 0, intervalo acima de 0; "igual" (intervalo
inclui 0) é não compatível.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.panel_agreement import discordance
from norvald_lab.measures.statistic import Statistic
from norvald_lab.measures.verdict import directional


class CriterionD:
    letter = "D"
    source = "critério D (bloco 1.2); afirmação de 2609.31013"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        for unit in table.by_question_unit:
            b1, b2 = table.options(unit, "B1"), table.options(unit, "B2")
            common = sorted(set(b1) & set(b2))
            within = sum(b1[p] != b2[p] for p in common) / len(common) if common else None
            between = discordance(list(b1.values()))
            cluster = unit[1]
            if within is not None:
                sums.add(cluster, "D|dentro|n")
                sums.add(cluster, "D|dentro|s", within)
            if between is not None:
                sums.add(cluster, "D|entre|n")
                sums.add(cluster, "D|entre|s", between)
            if within is not None and between is not None:
                sums.add(cluster, "D|par|n")
                sums.add(cluster, "D|par|d", between - within)
        stats = {
            "dentro": Statistic.ratio("D|dentro|s", "D|dentro|n"),
            "entre": Statistic.ratio("D|entre|s", "D|entre|n"),
            "entre_menos_dentro": Statistic.ratio("D|par|d", "D|par|n"),
        }
        intervals = bootstrap.run(sums, stats)
        return {
            "fonte": self.source,
            "medida": "discordância B1×B2 do mesmo participante × discordância entre pares de participantes em B1",
            "resultado": {name: interval.to_dict() for name, interval in intervals.items()},
            "veredito": directional(intervals["entre_menos_dentro"], expected="acima"),
        }
