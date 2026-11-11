"""Ausência e exclusões registradas (344-79 item 2; 344-81).

Nada é imputado. Por condição: linhas, sem posição válida e sem contribuição
estruturada (a taxa por condição é o que o registro pede, porque taxa que
difere entre condições seria efeito da manipulação). Por pergunta: quem
ficou fora da análise de exposição e por quê.
"""

from __future__ import annotations

from norvald_lab.measures.aw9vf.exposure_eligibility import ineligible_b1
from norvald_lab.measures.conditions import CONDITIONS
from norvald_lab.measures.observation_table import ObservationTable


class Missingness:
    def compute(self, table: ObservationTable) -> dict:
        per_condition = {}
        for condition in CONDITIONS:
            rows = [r for r in table.rows if r.condition == condition]
            per_condition[condition] = {
                "linhas": len(rows), "sem_posicao": sum(r.option is None for r in rows),
                "sem_contribuicao_estruturada": sum(not r.structured for r in rows),
                "taxa_sem_contribuicao_estruturada": sum(not r.structured for r in rows) / len(rows) if rows else None,
            }
        exclusions = [
            {"rodada": unit[0], "pergunta": unit[1], "repeticao": unit[2], "participante": pid, "motivo": reason}
            for unit in table.by_question_unit for pid, reason in ineligible_b1(table, unit).items()
        ]
        return {"por_condicao": per_condition, "excluidos_da_exposicao_por_pergunta": exclusions, "nenhuma_imputacao": True}
