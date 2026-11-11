"""Uniformidade das posições de um painel numa pergunta.

Dispersão = fração de pares de participantes que discordam,
1 − Σ n_k(n_k − 1) / (m(m − 1)), com n_k participantes na opção k e m
participantes. É o índice de Gini–Simpson sem reposição: 0 com unanimidade,
1 quando ninguém concorda com ninguém, e lê-se como "probabilidade de dois
participantes sorteados discordarem". Escolhido por ser o mesmo objeto da
discordância entre modelos do critério D.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence


def unanimity(options: Sequence[str]) -> float | None:
    if len(options) < 2:
        return None
    return 1.0 if len(set(options)) == 1 else 0.0


def discordance(options: Sequence[str]) -> float | None:
    m = len(options)
    if m < 2:
        return None
    agreeing = sum(n * (n - 1) for n in Counter(options).values())
    return 1.0 - agreeing / (m * (m - 1))
