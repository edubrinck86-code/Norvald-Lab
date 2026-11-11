"""Dependência entre pares de participantes, a partir de somas aditivas.

Dois objetos (TESE-005 §5 pede que fiquem distintos):

- correlação de indicadores 0/1 (phi = Pearson em binário), usada nos erros
  com gabarito (F): r = (nΣxy − ΣxΣy) / √((nΣx − (Σx)²)(nΣy − (Σy)²)).
  Par com variância zero (modelo que nunca erra, ou sempre erra, naquelas
  perguntas) não tem correlação definida e fica fora da média.
- kappa de Cohen sobre rótulos (as opções), usado nas posições das
  contestáveis (E): κ = (P_o − P_e)/(1 − P_e), com
  P_e = Σ_k π_i(k) π_j(k) a partir das frequências de cada participante.
  Contestável não tem "erro", então correlação de erro não se aplica; o
  kappa é o análogo para rótulos nominais. Os rótulos são os ids das
  opções (option-a é sempre a primeira apresentada), então P_e inclui a
  preferência de cada modelo por posição na lista.

Em ambos os casos ρ̄ é a média simples dos pares definidos, e
N_eff = n / (1 + (n − 1) ρ̄), com n = número de participantes.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Mapping, Sequence

from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.statistic import Totals


def add_binary_pairs(sums: ClusterSums, cluster: str, prefix: str, values: Mapping[str, float], *, stratum: str = "") -> None:
    for i, j in combinations(sorted(values), 2):
        x, y = values[i], values[j]
        key = f"{prefix}|{i}|{j}"
        sums.add(cluster, key + "|n", 1.0, stratum=stratum)
        sums.add(cluster, key + "|sx", x, stratum=stratum)
        sums.add(cluster, key + "|sy", y, stratum=stratum)
        sums.add(cluster, key + "|sxy", x * y, stratum=stratum)


def add_label_pairs(sums: ClusterSums, cluster: str, prefix: str, labels: Mapping[str, str], *, stratum: str = "") -> None:
    for i, j in combinations(sorted(labels), 2):
        key = f"{prefix}|{i}|{j}"
        sums.add(cluster, key + "|n", 1.0, stratum=stratum)
        sums.add(cluster, key + "|agree", float(labels[i] == labels[j]), stratum=stratum)
        sums.add(cluster, f"{key}|i|{labels[i]}", 1.0, stratum=stratum)
        sums.add(cluster, f"{key}|j|{labels[j]}", 1.0, stratum=stratum)


def phi(totals: Totals, prefix: str, i: str, j: str) -> float | None:
    key = f"{prefix}|{i}|{j}"
    n = totals.get(key + "|n", 0.0)
    sx, sy, sxy = totals.get(key + "|sx", 0.0), totals.get(key + "|sy", 0.0), totals.get(key + "|sxy", 0.0)
    var = (n * sx - sx * sx) * (n * sy - sy * sy)
    if n < 2 or var <= 0:
        return None
    return (n * sxy - sx * sy) / math.sqrt(var)


def kappa(totals: Totals, prefix: str, i: str, j: str, labels: Sequence[str]) -> float | None:
    key = f"{prefix}|{i}|{j}"
    n = totals.get(key + "|n", 0.0)
    if n == 0:
        return None
    observed = totals.get(key + "|agree", 0.0) / n
    expected = sum(totals.get(f"{key}|i|{label}", 0.0) * totals.get(f"{key}|j|{label}", 0.0) for label in labels) / (n * n)
    if expected >= 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def agreement(totals: Totals, prefix: str, i: str, j: str) -> float | None:
    n = totals.get(f"{prefix}|{i}|{j}|n", 0.0)
    return None if n == 0 else totals.get(f"{prefix}|{i}|{j}|agree", 0.0) / n


def mean_over_pairs(agents: Sequence[str], value) -> float | None:
    values = [v for i, j in combinations(sorted(agents), 2) if (v := value(i, j)) is not None]
    return sum(values) / len(values) if values else None


def effective_n(n: int, rho: float | None) -> float | None:
    if rho is None:
        return None
    denominator = 1 + (n - 1) * rho
    return None if denominator <= 0 else n / denominator
