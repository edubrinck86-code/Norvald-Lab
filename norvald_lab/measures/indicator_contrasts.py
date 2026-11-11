"""Nível por condição e contrastes pareados de um valor por unidade.

Nível M(c) = Σ valor / nº de unidades com valor em c. Contraste
Δ(a, b) = Σ (valor_a − valor_b) / nº de unidades com valor em a E em b:
pareado, para que uma posição ausente numa condição não mude a população
comparada. A unidade pode ser um participante numa pergunta (A, C, I) ou a
própria pergunta (B, H): quem chama decide o que é unidade e o que é valor.

Os grupos (por exemplo "todas", "unanime", "maioria") são rótulos de
recorte; uma unidade pode estar em mais de um.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import CONDITIONS, CONTRASTS
from norvald_lab.measures.interval import Interval
from norvald_lab.measures.statistic import Statistic


class IndicatorContrasts:
    def __init__(self, sums: ClusterSums, namespace: str, conditions: Sequence[str] = CONDITIONS, contrasts: Mapping[str, tuple[str, str]] = CONTRASTS):
        self.sums, self.namespace = sums, namespace
        self.conditions, self.contrasts = tuple(conditions), dict(contrasts)
        self.groups: list[str] = []

    def _key(self, group: str, *parts: str) -> str:
        if group not in self.groups:
            self.groups.append(group)
        return "|".join((self.namespace, group) + parts)

    def add_level(self, cluster: str, condition: str, value: float | None, groups: Sequence[str] = ("todas",)) -> None:
        if value is None:
            return
        for group in groups:
            self.sums.add(cluster, self._key(group, "n", condition))
            self.sums.add(cluster, self._key(group, "s", condition), value)

    def add_pair(self, cluster: str, contrast: str, arrival: float | None, base: float | None, groups: Sequence[str] = ("todas",)) -> None:
        if arrival is None or base is None:
            return
        for group in groups:
            self.sums.add(cluster, self._key(group, "pn", contrast))
            self.sums.add(cluster, self._key(group, "pd", contrast), arrival - base)

    def add(self, cluster: str, values: Mapping[str, float | None], groups: Sequence[str] = ("todas",)) -> None:
        for condition in self.conditions:
            self.add_level(cluster, condition, values.get(condition), groups)
        for name, (arrival, base) in self.contrasts.items():
            self.add_pair(cluster, name, values.get(arrival), values.get(base), groups)

    def level_keys(self, group: str, condition: str) -> tuple[str, str]:
        return ("|".join((self.namespace, group, "s", condition)), "|".join((self.namespace, group, "n", condition)))

    def contrast_keys(self, group: str, contrast: str) -> tuple[str, str]:
        return ("|".join((self.namespace, group, "pd", contrast)), "|".join((self.namespace, group, "pn", contrast)))

    def statistics(self) -> dict[str, Statistic]:
        stats = {}
        for group in self.groups:
            for condition in self.conditions:
                stats[f"{self.namespace}|{group}|nivel|{condition}"] = Statistic.ratio(*self.level_keys(group, condition))
            for name in self.contrasts:
                stats[f"{self.namespace}|{group}|contraste|{name}"] = Statistic.ratio(*self.contrast_keys(group, name))
        return stats

    def organize(self, intervals: Mapping[str, Interval]) -> dict:
        out = {}
        for group in self.groups:
            out[group] = {
                "niveis": {c: intervals[f"{self.namespace}|{group}|nivel|{c}"].to_dict() for c in self.conditions},
                "contrastes": {name: intervals[f"{self.namespace}|{group}|contraste|{name}"].to_dict() for name in self.contrasts},
            }
        return out

    def interval(self, intervals: Mapping[str, Interval], contrast: str, group: str = "todas") -> Interval:
        return intervals[f"{self.namespace}|{group}|contraste|{contrast}"]
