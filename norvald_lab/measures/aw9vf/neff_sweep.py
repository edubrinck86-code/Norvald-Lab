"""Varredura analítica de N_eff = n / (1 + (n − 1) ρ̄) (344-66 item 6; 344-71).

Tabela analítica, não empírica: vale qualquer que seja o ρ̄ estimado, que
entra só como âncora, nunca como limite. n em {4, 5, 8, ∞} (o registro
declarou 4 e 8; o painel real tem 5, e ∞ dá 1/ρ̄) e ρ̄ em (0, 1].
"""

from __future__ import annotations

from norvald_lab.measures.pairwise_dependence import effective_n

RHOS = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00)
SIZES: tuple[int | None, ...] = (4, 5, 8, None)  # None = infinito


def n_eff(n: int | None, rho: float) -> float | None:
    return 1.0 / rho if n is None else effective_n(n, rho)


def label(n: int | None) -> str:
    return "n=inf" if n is None else f"n={n}"


class NeffSweep:
    def table(self, panel_size: int, anchors: dict[str, float | None]) -> dict:
        sizes = tuple(sorted({s for s in SIZES if s is not None} | {panel_size})) + (None,)
        return {
            "natureza": "analitica (não empírica); vale qualquer que seja o ρ̄ observado",
            "formula": "N_eff = n / (1 + (n − 1) ρ̄); n = ∞ → 1/ρ̄",
            "linhas": [{"rho": rho, **{label(n): n_eff(n, rho) for n in sizes}} for rho in RHOS],
            "ancoras_empiricas": {
                name: None if rho is None else {"rho": rho, **{label(n): n_eff(n, rho) if rho > 0 else None for n in sizes}}
                for name, rho in anchors.items()
            },
        }
