"""Ordem de execução do TESE-002 §4.1.

Primeiro, para cada pergunta, B1 e B2 intercaladas; depois, para cada
pergunta, B3 e E intercaladas. A ordem dentro do par alterna de uma pergunta
para a outra, para que a deriva do provider ao longo do dia não incida
sempre sobre a mesma condição.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Step:
    question_id: str
    condition_id: str  # B1, B2, B3 ou E

    @property
    def derived(self) -> bool:
        return self.condition_id in {"B3", "E"}


def protocol_order(question_ids: Sequence[str]) -> list[Step]:
    steps: list[Step] = []
    for position, qid in enumerate(question_ids):
        pair = ("B1", "B2") if position % 2 == 0 else ("B2", "B1")
        steps += [Step(qid, c) for c in pair]
    for position, qid in enumerate(question_ids):
        pair = ("B3", "E") if position % 2 == 0 else ("E", "B3")
        steps += [Step(qid, c) for c in pair]
    return steps
