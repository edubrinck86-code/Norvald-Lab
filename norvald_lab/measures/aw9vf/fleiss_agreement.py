"""Kappa de Fleiss sobre as posições de B1 nas contestáveis (344-75: rho_bar_behaviour).

Por pergunta, P_i = (Σ_k n_ik² − m_i) / (m_i (m_i − 1)), a fração de pares do
painel que concordam, com m_i posições válidas (mínimo 2; o Fleiss clássico
supõe m fixo, aqui m_i pode variar quando falta posição, e as frequências de
categoria são pooled sobre todas as posições). Sobre o conjunto:
κ = (P̄ − P_e) / (1 − P_e), com P̄ = média dos P_i e P_e = Σ_k p_k², p_k =
fração de todas as posições na categoria k. Categorias = ids das opções
(option-a é sempre a primeira apresentada), então P_e inclui a preferência
de cada modelo por posição na lista, como no kappa do critério E.

É descritiva: rho_bar_behaviour não entra na tabela de N_eff, e concordância
acima do acaso inclui concordância por pergunta fácil (retratação declarada
em 344-75): é teto candidato, não piso.
"""

from __future__ import annotations

from collections import Counter

from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.statistic import Totals


class FleissAgreement:
    PREFIX = "fleiss"

    def add(self, sums: ClusterSums, cluster: str, options: list[str], *, stratum: str = "") -> None:
        m = len(options)
        if m < 2:
            return
        counts = Counter(options)
        sums.add(cluster, f"{self.PREFIX}|itens", 1.0, stratum=stratum)
        sums.add(cluster, f"{self.PREFIX}|p_i", (sum(n * n for n in counts.values()) - m) / (m * (m - 1)), stratum=stratum)
        sums.add(cluster, f"{self.PREFIX}|posicoes", float(m), stratum=stratum)
        for option, n in counts.items():
            sums.add(cluster, f"{self.PREFIX}|cat|{option}", float(n), stratum=stratum)

    def kappa(self, totals: Totals) -> float | None:
        items, positions = totals.get(f"{self.PREFIX}|itens", 0.0), totals.get(f"{self.PREFIX}|posicoes", 0.0)
        if items == 0:
            return None
        observed = totals.get(f"{self.PREFIX}|p_i", 0.0) / items
        expected = sum((v / positions) ** 2 for k, v in totals.items() if k.startswith(f"{self.PREFIX}|cat|"))
        if expected >= 1.0:
            return None
        return (observed - expected) / (1.0 - expected)

    def observed(self, totals: Totals) -> float | None:
        items = totals.get(f"{self.PREFIX}|itens", 0.0)
        return None if items == 0 else totals.get(f"{self.PREFIX}|p_i", 0.0) / items
