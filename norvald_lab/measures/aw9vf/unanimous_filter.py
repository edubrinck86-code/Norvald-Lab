"""Exclusão registrada: pergunta unânime em B1 sai da análise principal (344-79, item 1).

Unânime = todas as posições válidas de B1 iguais (mínimo de duas), a mesma
definição do agrupamento da regra 1 (`B1Grouping`). A variante "mantidas"
(desvio aprovado em 11/11/2026) é a tabela sem filtro. A taxa de descarte é
resultado e sai junto.
"""

from __future__ import annotations

from norvald_lab.measures.b1_grouping import B1Grouping
from norvald_lab.measures.observation_table import ObservationTable


class UnanimousFilter:
    def unanimous_units(self, table: ObservationTable) -> set[tuple[str, str, str]]:
        return {unit for unit in table.by_question_unit if B1Grouping.classify(table.options(unit, "B1").values()).group == "unanime"}

    def without_unanimous(self, table: ObservationTable) -> ObservationTable:
        drop = self.unanimous_units(table)
        return ObservationTable(tuple(r for r in table.rows if r.question_unit not in drop), table.questions, table.runs)

    def discard_rate(self, table: ObservationTable) -> dict:
        with_b1 = [unit for unit, by_condition in table.by_question_unit.items() if "B1" in by_condition]
        dropped = self.unanimous_units(table)
        return {"perguntas_com_b1": len(with_b1), "perguntas_unanimes_em_b1": len(dropped), "taxa_de_descarte": len(dropped) / len(with_b1) if with_b1 else None}
