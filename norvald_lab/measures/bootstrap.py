"""Bootstrap por cluster de pergunta, intervalo percentil, determinístico.

Por quê por pergunta: os cinco participantes respondem à mesma pergunta, e
as condições de um participante derivam da mesma B1. Reamostrar linhas
trataria como independentes observações que não são. É também o que Hao et
al. fazem (20.000 réplicas por cluster de pergunta, seed fixa).

Determinismo: `random.Random(seed)` próprio, nunca o gerador global; os
clusters entram ordenados por id. Mesma tabela + mesma seed = mesmo número.
A seed vai para o relatório.

Percentil: quantis das réplicas válidas com interpolação linear entre
estatísticas de ordem (tipo 7 de Hyndman & Fan, o padrão do R e do numpy).
Réplica em que a estatística não existe (denominador zero, variância zero)
não entra no quantil; quantas entraram fica em `valid_reps`.

Estratos: quando dados, a reamostragem é feita dentro de cada estrato com o
tamanho original (usado em E, que compara contestáveis com perguntas de
gabarito sem deixar a proporção entre elas variar).
"""

from __future__ import annotations

import math
import random
from array import array
from typing import Mapping, Sequence

from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.interval import Interval
from norvald_lab.measures.statistic import Statistic

DEFAULT_REPS = 20_000
DEFAULT_SEED = 20261111
DEFAULT_LEVEL = 0.95
CACHE_SHAPES = 4  # ~34 MB por forma com 420 perguntas e 20.000 réplicas


def quantile(sorted_values: Sequence[float], q: float) -> float:
    """Quantil tipo 7: posição (n − 1)·q, interpolação linear."""
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def _valid(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _dot_fallback(counts: Sequence[int], column: Sequence[float]) -> float:
    return sum(c * x for c, x in zip(counts, column) if c)


# math.sumprod (Python 3.12+) faz o produto escalar em C: ~7 µs por coluna de 420
# perguntas, contra ~11 µs somando a tupla da reamostragem (medido em 11/11/2026).
# No 3.10/3.11 cai na versão em Python. Os dois são determinísticos; com somas
# inteiras (contagens) dão o mesmo número.
_dot = getattr(math, "sumprod", _dot_fallback)


class ClusteredBootstrap:
    def __init__(self, reps: int = DEFAULT_REPS, seed: int = DEFAULT_SEED, level: float = DEFAULT_LEVEL):
        if reps < 1:
            raise ValueError("reps precisa ser positivo")
        self.reps, self.seed, self.level = reps, seed, level
        self._cache: dict[tuple, list[array]] = {}

    def _multiplicities(self, ordered_groups: list[list[int]]) -> list[array]:
        """Multiplicidade de cada cluster em cada réplica; o total de uma coluna
        na réplica é o produto escalar multiplicidades · coluna.

        Um gerador novo com a mesma seed por chamada: o sorteio depende só da
        seed e da composição dos estratos. Por isso medidas sobre o mesmo
        conjunto de perguntas recebem as mesmas réplicas, e guardar o sorteio
        (cache das últimas formas) não muda nenhum número, só o tempo.
        """
        # A chave é a composição exata dos estratos (quais índices em cada um),
        # não só os tamanhos: mesmos tamanhos com outra composição é outro sorteio.
        shape = tuple(tuple(group) for group in ordered_groups)
        if shape in self._cache:
            return self._cache[shape]
        rng = random.Random(self.seed)
        n = sum(len(group) for group in ordered_groups)
        out = []
        for _ in range(self.reps):
            # Guardado compacto (uint32, 4 bytes por pergunta); vira float na hora do
            # produto escalar, que no caminho float é ~40% mais rápido.
            counts = array("I", bytes(4 * n))
            for group in ordered_groups:
                for index in rng.choices(group, k=len(group)):
                    counts[index] += 1
            out.append(counts)
        if len(self._cache) >= CACHE_SHAPES:
            self._cache.pop(next(iter(self._cache)))
        self._cache[shape] = out
        return out

    def describe(self) -> dict:
        return {"reps": self.reps, "seed": self.seed, "nivel": self.level, "metodo": "percentil (tipo 7), reamostragem por pergunta"}

    def run(self, sums: ClusterSums, statistics: Mapping[str, Statistic]) -> dict[str, Interval]:
        clusters = sums.clusters()
        totals = sums.totals()
        point = {name: stat.compute(totals) for name, stat in statistics.items()}
        if not clusters:
            return {name: Interval(None, None, None, None, 0, 0) for name in statistics}
        keys = sorted({key for _, values in clusters for key in values})
        # Desempenho (20.000 réplicas em Python puro): coluna toda zero fica fora
        # do laço (as estatísticas leem com .get(chave, 0)), e colunas idênticas
        # (por exemplo o "n" de cada condição quando ninguém falhou) são somadas
        # uma vez só.
        distinct: dict[tuple[float, ...], list[str]] = {}
        for key in keys:
            column = tuple(float(values.get(key, 0.0)) for _, values in clusters)
            if any(column):
                distinct.setdefault(column, []).append(key)
        columns = list(distinct.items())
        strata = sums.strata()
        groups: dict[str, list[int]] = {}
        for index, (cluster, _) in enumerate(clusters):
            groups.setdefault(strata.get(cluster, ""), []).append(index)
        ordered_groups = [groups[label] for label in sorted(groups)]
        draws: dict[str, list[float]] = {name: [] for name in statistics}
        for stored in self._multiplicities(ordered_groups):
            counts = array("d", stored)
            replicate = {}
            for column, names in columns:
                total = _dot(counts, column)
                for key in names:
                    replicate[key] = total
            for name, stat in statistics.items():
                value = stat.compute(replicate)
                if _valid(value):
                    draws[name].append(value)
        alpha = (1 - self.level) / 2
        out = {}
        for name, stat in statistics.items():
            values = sorted(draws[name])
            low = quantile(values, alpha) if values else None
            high = quantile(values, 1 - alpha) if values else None
            estimate = point[name] if _valid(point[name]) else None
            n = totals.get(stat.n_key, 0.0) if stat.n_key else None
            out[name] = Interval(estimate, low, high, n, len(clusters), len(values))
        return out
