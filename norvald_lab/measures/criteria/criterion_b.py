"""Critério B — a exposição eleva a uniformidade das posições (Herding, 2610.30769).

Unidade: a pergunta (todas, regra 1). Duas medidas por condição:
unanimidade (1 se todas as posições válidas coincidem) e dispersão (fração
de pares discordantes, `panel_agreement.discordance`).

Pareamento: no contraste entre a e b só entram os participantes com posição
válida nas duas condições, e a pergunta só entra com dois ou mais deles.
Sem isso, tirar uma linha indireta de E deixaria o painel de E menor que o
de B3, e um painel menor fica unânime com mais facilidade.

Previsão: Δ_pares(unanimidade) > 0 e Δ_pares(dispersão) < 0, intervalos sem 0.
Também por grupo de B1 (unânime, maioria, sem maioria).
"""

from __future__ import annotations

from norvald_lab.measures.b1_grouping import B1Grouping
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import PRIMARY_CONTRAST
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.uniformity_sums import add_uniformity
from norvald_lab.measures.verdict import COMPATIVEL, INDETERMINADO, NAO_COMPATIVEL, side_text


class CriterionB:
    letter = "B"
    source = "critério B (bloco 1.2); afirmação do Herding, 2610.30769"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        unanimous = IndicatorContrasts(sums, "B.unanimidade")
        dispersion = IndicatorContrasts(sums, "B.dispersao")
        for unit in table.by_question_unit:
            group = B1Grouping.classify(table.options(unit, "B1").values()).group
            add_uniformity(table, unit, unanimous, dispersion, ("todas", group))
        stats = unanimous.statistics() | dispersion.statistics()
        intervals = bootstrap.run(sums, stats)
        if not unanimous.groups:
            return {"fonte": self.source, "resultado": {}, "veredito": INDETERMINADO}
        up = unanimous.interval(intervals, PRIMARY_CONTRAST).side(0.0)
        down = dispersion.interval(intervals, PRIMARY_CONTRAST).side(0.0) if dispersion.groups else None
        if up is None or down is None:
            verdict = INDETERMINADO
        elif up == "acima" and down == "abaixo":
            verdict = COMPATIVEL
        elif up == "inclui" and down == "inclui":
            verdict = NAO_COMPATIVEL
        else:
            # A tabela só prevê os dois casos acima; qualquer mistura é relatada como tal.
            verdict = f"fora da tabela (intervalo da unanimidade {side_text(up)}, da dispersão {side_text(down)})"
        return {
            "fonte": self.source,
            "medida": "unanimidade (0/1) e dispersão (fração de pares discordantes) por pergunta",
            "resultado": {"unanimidade": unanimous.organize(intervals), "dispersao": dispersion.organize(intervals) if dispersion.groups else {}},
            "veredito": verdict,
        }
