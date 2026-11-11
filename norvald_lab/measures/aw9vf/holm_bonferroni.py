"""Holm–Bonferroni sobre os três testes confirmatórios (344-77).

Ordena os p crescentes; p_ajustado(i) = max até i de min(1, (m − i + 1) · p(i)),
com i de 1 a m. O ajustado nunca é menor que o bruto e nunca decresce.
Os dois valores saem no relatório, para a correção ficar visível.
"""

from __future__ import annotations


class HolmBonferroni:
    def adjust(self, p_values: dict[str, float]) -> dict[str, float]:
        ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
        m = len(ordered)
        out: dict[str, float] = {}
        running = 0.0
        for index, (name, p) in enumerate(ordered):
            running = max(running, min(1.0, (m - index) * p))
            out[name] = running
        return {name: out[name] for name in p_values}
