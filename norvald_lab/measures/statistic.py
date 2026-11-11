"""Uma estatística calculada a partir das somas dos clusters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

Totals = Mapping[str, float]


def ratio_of(totals: Totals, numerator: str, denominator: str) -> float | None:
    den = totals.get(denominator, 0.0)
    return None if den == 0 else totals.get(numerator, 0.0) / den


@dataclass(frozen=True)
class Statistic:
    compute: Callable[[Totals], float | None]
    n_key: str | None = None  # soma que vai para o campo "n" (o denominador, em geral)

    @classmethod
    def ratio(cls, numerator: str, denominator: str) -> "Statistic":
        return cls(lambda t: ratio_of(t, numerator, denominator), denominator)

    @classmethod
    def difference_of_ratios(cls, first: tuple[str, str], second: tuple[str, str]) -> "Statistic":
        """r1 − r2 com denominadores próprios (grupos diferentes, não pareados)."""
        def compute(t: Totals) -> float | None:
            a, b = ratio_of(t, *first), ratio_of(t, *second)
            return None if a is None or b is None else a - b
        return cls(compute, None)
