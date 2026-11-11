"""Wilcoxon de postos sinalizados, pareado, bilateral (344-71, 344-77).

Diferenças nulas saem (convenção clássica; o número de nulos fica no
resultado). |d| recebe postos médios nos empates. A estatística é W+ (soma
dos postos das diferenças positivas).

p-valor:
- exato quando restam até EXACT_LIMIT diferenças não nulas: distribuição de
  permutação dos sinais, condicionada aos postos observados (com empates
  também, usando os postos médios dobrados, que são inteiros). p = P(|2W − T|
  ≥ |2W+ − T|), T = soma dos postos; contagem por programação dinâmica.
- aproximação normal acima disso: média T/2, variância
  [n(n+1)(2n+1) − ½ Σ(t³ − t)] / 24 (correção de empates), correção de
  continuidade 0,5.

Tamanho de efeito: correlação bisserial por postos pareada,
r = (W+ − W−)/(W+ + W−), de −1 a +1 (sinal da mudança), e a mediana das
diferenças. O IC bootstrap do efeito sai da diferença média (ver quem chama).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from statistics import median
from typing import Sequence

EXACT_LIMIT = 50


@dataclass(frozen=True)
class WilcoxonResult:
    n: int  # pares totais
    n_nonzero: int
    n_zero: int
    w_plus: float
    w_minus: float
    p: float | None
    method: str  # exato, normal ou sem_diferencas
    rank_biserial: float | None
    median_difference: float | None


def midranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


class WilcoxonSignedRank:
    def test(self, differences: Sequence[float]) -> WilcoxonResult:
        # Diferenças vêm de médias de 0/1 e de postos: o arredondamento evita que
        # 0.30000000000000004 e 0.3 deixem de empatar.
        values = [round(float(d), 12) for d in differences]
        nonzero = [d for d in values if d != 0]
        n_zero = len(values) - len(nonzero)
        mid = round(median(values), 12) if values else None
        if not nonzero:
            return WilcoxonResult(len(values), 0, n_zero, 0.0, 0.0, None, "sem_diferencas", None, mid)
        ranks = midranks([abs(d) for d in nonzero])
        w_plus = sum(r for r, d in zip(ranks, nonzero) if d > 0)
        w_minus = sum(r for r, d in zip(ranks, nonzero) if d < 0)
        n = len(nonzero)
        if n <= EXACT_LIMIT:
            p, method = self._exact(ranks, w_plus), "exato"
        else:
            p, method = self._normal(ranks, w_plus), "normal"
        return WilcoxonResult(len(values), n, n_zero, w_plus, w_minus, p, method, (w_plus - w_minus) / (w_plus + w_minus), mid)

    @staticmethod
    def _exact(ranks: Sequence[float], w_plus: float) -> float:
        doubled = [int(round(2 * r)) for r in ranks]
        total = sum(doubled)
        counts = [0] * (total + 1)
        counts[0] = 1
        for weight in doubled:
            for s in range(total, weight - 1, -1):
                counts[s] += counts[s - weight]
        observed = abs(2 * int(round(2 * w_plus)) - total)
        extreme = sum(c for s, c in enumerate(counts) if abs(2 * s - total) >= observed)
        return min(1.0, extreme / 2 ** len(ranks))

    @staticmethod
    def _normal(ranks: Sequence[float], w_plus: float) -> float:
        n = len(ranks)
        total = n * (n + 1) / 2
        ties = sum(t ** 3 - t for t in Counter(ranks).values())
        variance = (n * (n + 1) * (2 * n + 1) - ties / 2) / 24
        if variance <= 0:
            return 1.0
        deviation = max(0.0, abs(w_plus - total / 2) - 0.5)
        return min(1.0, math.erfc(deviation / math.sqrt(variance) / math.sqrt(2)))
