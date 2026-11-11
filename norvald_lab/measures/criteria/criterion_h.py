"""Critério H — a uniformidade sobe sem acompanhamento do acerto (Herding).

Braço de gabarito. Duas medidas, nas mesmas perguntas:
- Δ_pares(unanimidade), por pergunta, pareada por participante (como em B);
- Δ_pares(taxa de acerto), por participante.

Leitura da tabela:
- compatível: unanimidade ↑ (intervalo acima de 0) e acerto sem alteração
  (intervalo inclui 0);
- não compatível: acerto ↑ junto (intervalo acima de 0).
Casos que a tabela não cobre (unanimidade não sobe; acerto cai) saem
nomeados como "fora da tabela", com a direção de cada um.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import CONDITIONS, PRIMARY_CONTRAST
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.uniformity_sums import add_uniformity
from norvald_lab.measures.verdict import COMPATIVEL, INDETERMINADO, NAO_COMPATIVEL, side_text


class CriterionH:
    letter = "H"
    source = "critério H (bloco 1.2); afirmação do Herding, 2610.30769"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        unanimous = IndicatorContrasts(sums, "H.unanimidade")
        accuracy = IndicatorContrasts(sums, "H.acerto")
        for unit, by_condition in table.by_question_unit.items():
            if table.answer(unit[1]) is None:
                continue
            add_uniformity(table, unit, unanimous, None, ("todas",))
            for pid in sorted({pid for rows in by_condition.values() for pid in rows}):
                values = {}
                for condition in CONDITIONS:
                    row = by_condition.get(condition, {}).get(pid)
                    values[condition] = None if row is None or row.correct is None else float(row.correct)
                accuracy.add(unit[1], values)
        intervals = bootstrap.run(sums, unanimous.statistics() | accuracy.statistics())
        if not unanimous.groups or not accuracy.groups:
            return {"fonte": self.source, "resultado": {}, "veredito": INDETERMINADO}
        up = unanimous.interval(intervals, PRIMARY_CONTRAST).side(0.0)
        acc = accuracy.interval(intervals, PRIMARY_CONTRAST).side(0.0)
        if up is None or acc is None:
            verdict = INDETERMINADO
        elif acc == "acima":
            verdict = NAO_COMPATIVEL
        elif up == "acima" and acc == "inclui":
            verdict = COMPATIVEL
        else:
            verdict = f"fora da tabela (intervalo da unanimidade {side_text(up)}, do acerto {side_text(acc)})"
        return {
            "fonte": self.source,
            "medida": "Δ_pares(unanimidade) por pergunta junto de Δ_pares(taxa de acerto) por participante, perguntas com gabarito",
            "resultado": {"unanimidade": unanimous.organize(intervals), "acerto": accuracy.organize(intervals)},
            "veredito": verdict,
        }
