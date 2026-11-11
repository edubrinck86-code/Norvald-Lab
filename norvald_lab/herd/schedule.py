"""Ordem de execução do TESE-002 §4.1.

Primeiro, para cada pergunta, B1 e B2 intercaladas; depois, para cada
pergunta, as três condições derivadas de B1 (B3, EP e E).

A ordem dentro do par cego alterna de uma pergunta para a outra, para que a
deriva do provider ao longo do dia não incida sempre sobre a mesma condição.

Na fase derivada (11/11/2026, com a 5ª condição EP) a ordem das três gira em
quadrado latino pelo índice da pergunta: a pergunta 0 vai B3, EP, E; a 1 vai
EP, E, B3; a 2 vai E, B3, EP; e repete. Com três perguntas ou mais, cada
condição abre a fase ao menos uma vez e ocupa cada posição o mesmo número de
vezes (±1). A rotação é cíclica, não sorteada: ninguém escolhe a ordem e ela
se reconstrói só pela posição da pergunta na lista.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

DERIVED_CONDITIONS = ("B3", "EP", "E")


@dataclass(frozen=True)
class Step:
    question_id: str
    condition_id: str  # B1, B2, B3, EP ou E

    @property
    def derived(self) -> bool:
        return self.condition_id in DERIVED_CONDITIONS


def derived_rotation(position: int) -> tuple[str, ...]:
    """Ordem das condições derivadas para a pergunta na posição dada (quadrado latino cíclico)."""
    shift = position % len(DERIVED_CONDITIONS)
    return DERIVED_CONDITIONS[shift:] + DERIVED_CONDITIONS[:shift]


def protocol_order(question_ids: Sequence[str], *, blind_first_only: bool = False) -> list[Step]:
    """blind_first_only: só B1, para os pilotos do TESE-002 §5.3 e §5.4."""
    if blind_first_only:
        return [Step(qid, "B1") for qid in question_ids]
    steps: list[Step] = []
    for position, qid in enumerate(question_ids):
        pair = ("B1", "B2") if position % 2 == 0 else ("B2", "B1")
        steps += [Step(qid, c) for c in pair]
    for position, qid in enumerate(question_ids):
        steps += [Step(qid, c) for c in derived_rotation(position)]
    return steps
