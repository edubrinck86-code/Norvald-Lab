"""Somas aditivas por cluster (pergunta): a matéria-prima do bootstrap.

Toda medida daqui se escreve como função de somas (contagens, numeradores,
denominadores, Σxy...). Reamostrar perguntas vira somar as colunas das
perguntas sorteadas, e a estatística é recalculada a partir das somas. É o
que permite 20.000 réplicas em Python puro, e é o que garante que pesos como
os da padronização por estrato de Hao sejam recalculados em cada réplica,
sem código especial.
"""

from __future__ import annotations

from collections import defaultdict


class ClusterSums:
    def __init__(self):
        self._sums: dict[str, defaultdict[str, float]] = {}
        self._strata: dict[str, str] = {}

    def add(self, cluster: str, key: str, value: float = 1.0, *, stratum: str = "") -> None:
        sums = self._sums.setdefault(cluster, defaultdict(float))
        sums[key] += value
        if stratum:
            self._strata[cluster] = stratum

    def touch(self, cluster: str, *, stratum: str = "") -> None:
        """Registra o cluster mesmo sem soma não nula: ele conta no sorteio."""
        self._sums.setdefault(cluster, defaultdict(float))
        if stratum:
            self._strata[cluster] = stratum

    def clusters(self) -> list[tuple[str, dict[str, float]]]:
        return [(cluster, dict(self._sums[cluster])) for cluster in sorted(self._sums)]

    def strata(self) -> dict[str, str]:
        return dict(self._strata)

    def totals(self) -> dict[str, float]:
        out: defaultdict[str, float] = defaultdict(float)
        for sums in self._sums.values():
            for key, value in sums.items():
                out[key] += value
        return dict(out)

    def __len__(self) -> int:
        return len(self._sums)
