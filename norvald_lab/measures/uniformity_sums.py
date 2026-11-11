"""Escreve a uniformidade de uma pergunta (unanimidade e dispersão) nas somas, por condição e pareada.

Usado por B (todas as perguntas) e por H (só as de gabarito): a mesma conta,
populações diferentes. Pareamento: no contraste entre a e b só entram os
participantes com posição válida nas duas condições, e a pergunta só entra
com dois ou mais deles (ver criterion_b).
"""

from __future__ import annotations

from typing import Sequence

from norvald_lab.measures.conditions import CONDITIONS, CONTRASTS
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.panel_agreement import discordance, unanimity


def add_uniformity(table: ObservationTable, unit: tuple[str, str, str], unanimous: IndicatorContrasts, dispersion: IndicatorContrasts | None, groups: Sequence[str]) -> None:
    cluster = unit[1]
    for condition in CONDITIONS:
        options = list(table.options(unit, condition).values())
        unanimous.add_level(cluster, condition, unanimity(options), groups)
        if dispersion is not None:
            dispersion.add_level(cluster, condition, discordance(options), groups)
    for name, (arrival, base) in CONTRASTS.items():
        a, b = table.options(unit, arrival), table.options(unit, base)
        common = sorted(set(a) & set(b))
        first, second = [a[p] for p in common], [b[p] for p in common]
        unanimous.add_pair(cluster, name, unanimity(first), unanimity(second), groups)
        if dispersion is not None:
            dispersion.add_pair(cluster, name, discordance(first), discordance(second), groups)
