"""Estimativa pontual com intervalo bootstrap percentil."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    estimate: float | None
    low: float | None
    high: float | None
    n: float | None  # denominador da estimativa, quando a estatística declara um
    n_clusters: int
    valid_reps: int  # réplicas em que a estatística existia (ex.: denominador > 0)

    def includes(self, value: float) -> bool | None:
        if self.low is None or self.high is None:
            return None
        return self.low <= value <= self.high

    def side(self, value: float = 0.0) -> str | None:
        """'acima', 'abaixo' ou 'inclui' o valor de referência; None sem intervalo."""
        if self.low is None or self.high is None:
            return None
        if self.low > value:
            return "acima"
        if self.high < value:
            return "abaixo"
        return "inclui"

    def to_dict(self) -> dict:
        n = int(self.n) if self.n is not None and float(self.n).is_integer() else self.n
        # O nível do intervalo (95% por padrão) fica no topo do relatório, junto da seed.
        return {"estimativa": self.estimate, "ic": [self.low, self.high], "n": n, "n_perguntas": self.n_clusters, "replicas_validas": self.valid_reps}
