"""Quem entra na análise de exposição de uma pergunta (344-79, item 2; 344-81).

Entra o participante com posição válida em B1 e contribuição estruturada.
Quem não declarou estrutura não entrou no Working Context e ninguém o viu:
sai da análise de exposição naquela pergunta (não é par que ele possa ter
induzido, nem cobaia que tenha mudado diante de um painel que o inclui). A
saída é por pergunta e fica registrada em `ineligible_b1`.
"""

from __future__ import annotations

from norvald_lab.measures.observation import Observation
from norvald_lab.measures.observation_table import ObservationTable


def eligible_b1(table: ObservationTable, unit: tuple[str, str, str]) -> dict[str, Observation]:
    rows = table.by_question_unit.get(unit, {}).get("B1", {})
    return {pid: row for pid, row in rows.items() if row.option is not None and row.structured}


def ineligible_b1(table: ObservationTable, unit: tuple[str, str, str]) -> dict[str, str]:
    """participante → motivo, de quem está em B1 e não entra."""
    rows = table.by_question_unit.get(unit, {}).get("B1", {})
    out = {}
    for pid, row in rows.items():
        if row.option is None:
            out[pid] = "sem_posicao"
        elif not row.structured:
            out[pid] = "sem_contribuicao_estruturada"
    return out
