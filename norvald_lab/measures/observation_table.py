"""A tabela única de observações. Toda medida lê só daqui.

Guarda as linhas e o catálogo das perguntas (tipo, gabarito, texto). Não
calcula medida nenhuma: só oferece os agrupamentos que todas usam, para que
nenhuma medida reinvente a chave de pareamento.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from functools import cached_property
from typing import Mapping

from norvald_lab.measures.observation import Observation
from norvald_lab.measures.question_info import QuestionInfo

# (run, question_id, repetition) → condição → participant_id → linha
QuestionUnits = dict[tuple[str, str, str], dict[str, dict[str, Observation]]]


@dataclass(frozen=True)
class ObservationTable:
    rows: tuple[Observation, ...]
    questions: Mapping[str, QuestionInfo] = field(default_factory=dict)
    runs: tuple[str, ...] = ()

    def info(self, question_id: str) -> QuestionInfo:
        return self.questions.get(question_id) or QuestionInfo(question_id)

    def answer(self, question_id: str) -> str | None:
        return self.info(question_id).answer

    @property
    def indirect_rows(self) -> int:
        return sum(row.indirect and row.option is not None for row in self.rows)

    def without_indirect(self) -> "ObservationTable":
        """Variante "sem indiretas" da regra 3: a linha fica (conta como tentativa
        e custo), mas sem posição. Assim toda medida a exclui pelo mesmo caminho
        de qualquer outra posição ausente."""
        rows = tuple(replace(row, option=None, correct=None) if row.indirect else row for row in self.rows)
        return ObservationTable(rows, self.questions, self.runs)

    @cached_property
    def by_question_unit(self) -> QuestionUnits:
        grouped: dict = defaultdict(lambda: defaultdict(dict))
        for row in self.rows:
            grouped[row.question_unit][row.condition][row.participant_id] = row
        return {key: {cond: dict(sorted(by_pid.items())) for cond, by_pid in grouped[key].items()} for key in sorted(grouped)}

    def options(self, question_unit: tuple[str, str, str], condition: str) -> dict[str, str]:
        """participant_id → opção, só das posições válidas."""
        rows = self.by_question_unit.get(question_unit, {}).get(condition, {})
        return {pid: row.option for pid, row in rows.items() if row.option is not None}
