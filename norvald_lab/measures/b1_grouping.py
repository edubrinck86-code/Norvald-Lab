"""Classifica uma pergunta pelo que os participantes disseram em B1 (regras 1 e 2).

- unanime: todas as posições válidas iguais (mínimo de duas). Regra 1:
  não se descarta; fica como grupo à parte.
- maioria: uma opção com MAIS da metade das posições válidas, sem unanimidade.
- sem_maioria: nenhuma opção passa da metade. Regra 2: o empate 2 × 2 é
  sem maioria, e qualquer outra divisão sem maioria estrita (2-2-1, 2-1-1-1,
  comum no MMLU-Pro com dez opções) também. Sem desempate forçado.
- insuficiente: menos de duas posições válidas.

A metade é das posições válidas, não do painel: uma B1 incompleta bloqueia
B3, EP e E (o runner recusa), então na prática as duas contas coincidem
onde há exposição.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class B1Grouping:
    group: str
    majority: str | None  # opção majoritária; None em sem_maioria e insuficiente

    @classmethod
    def classify(cls, options: Iterable[str]) -> "B1Grouping":
        counts = Counter(options)
        total = sum(counts.values())
        if total < 2:
            return cls("insuficiente", None)
        option, top = counts.most_common(1)[0]
        if top == total:
            return cls("unanime", option)
        if top * 2 > total:
            return cls("maioria", option)
        return cls("sem_maioria", None)
