"""Índice dos pares (pergunta, participante, condição) → PairOutcome.

Valem os pares em que o participante é elegível em B1 e tem posição válida na
condição. B2 entra como as demais: "mudou" é opção de B2 ≠ opção de B1 e os
fundamentos de B2 são comparados com os de B1 (344-62).
"""

from __future__ import annotations

from norvald_lab.measures.aw9vf.exposure_eligibility import eligible_b1
from norvald_lab.measures.aw9vf.new_grounds import NewGrounds, PERMISSIVE, STRICT
from norvald_lab.measures.aw9vf.pair_outcome import PairOutcome
from norvald_lab.measures.observation_table import ObservationTable

SECOND_WAVE = ("B2", "B3", "EP", "E")


class PairOutcomeIndex:
    def __init__(self, table: ObservationTable):
        grounds = NewGrounds()
        self.table = table
        self._pairs: dict[tuple[tuple[str, str, str], str, str], PairOutcome] = {}
        for unit, by_condition in table.by_question_unit.items():
            b1 = eligible_b1(table, unit)
            for condition in SECOND_WAVE:
                for pid, row in by_condition.get(condition, {}).items():
                    if pid not in b1 or row.option is None:
                        continue
                    first = b1[pid]
                    self._pairs[(unit, pid, condition)] = PairOutcome(
                        unit, pid, row.agent, condition, first.option, row.option, row.option != first.option,
                        grounds.has_new(first.grounds, row.grounds, STRICT), grounds.has_new(first.grounds, row.grounds, PERMISSIVE))

    def get(self, unit: tuple[str, str, str], participant_id: str, condition: str) -> PairOutcome | None:
        return self._pairs.get((unit, participant_id, condition))

    def of_condition(self, condition: str) -> list[PairOutcome]:
        return [pair for (_, _, c), pair in self._pairs.items() if c == condition]

    def paired(self, condition_x: str, condition_y: str) -> list[tuple[PairOutcome, PairOutcome]]:
        """Os pares válidos nas duas condições (mesmo participante, mesma pergunta)."""
        return [(pair, other) for (unit, pid, c), pair in self._pairs.items() if c == condition_x and (other := self._pairs.get((unit, pid, condition_y))) is not None]
