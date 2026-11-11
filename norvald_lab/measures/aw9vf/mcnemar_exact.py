"""McNemar exato, bilateral (344-77: alfa 0,05, duas caudas).

Só contam os pares discordantes: b = (1 em X, 0 em Y), c = (0 em X, 1 em Y).
Sob H0, b ~ Binomial(b + c, 1/2). p = min(1, 2 · P(Bin(n, ½) ≤ min(b, c))).
Sem discordantes, p = 1 (nada a observar). Aritmética de inteiros: sem erro
de arredondamento até n grande.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb


@dataclass(frozen=True)
class McNemarResult:
    b: int
    c: int
    p: float


class McNemarExact:
    def test(self, pairs: list[tuple[bool, bool]]) -> McNemarResult:
        """pairs: (evento em X, evento em Y) de cada par pareado."""
        b = sum(x and not y for x, y in pairs)
        c = sum(y and not x for x, y in pairs)
        n = b + c
        if n == 0:
            return McNemarResult(b, c, 1.0)
        tail = sum(comb(n, k) for k in range(min(b, c) + 1))
        return McNemarResult(b, c, min(1.0, 2 * tail / 2 ** n))
