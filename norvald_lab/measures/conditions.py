"""Condições do Δ_herd e os contrastes entre elas.

O aninhamento B3 ⊂ EP ⊂ E (11/11/2026, 5ª condição EP) é o que dá sentido
aos dois contrastes novos: EP − B3 isola o efeito de ver só a posição dos
pares, e E − EP o de ver também a justificativa deles. Δ_pares é a soma dos
dois. B2 contra B1 caracteriza a variabilidade espontânea (TESE-005).
"""

from __future__ import annotations

CONDITIONS = ("B1", "B2", "B3", "EP", "E")

# nome do contraste → (condição de chegada, condição de base); Δ = M(chegada) − M(base)
CONTRASTS = {
    "delta_pares": ("E", "B3"),
    "delta_total": ("E", "B1"),
    "delta_posicao": ("EP", "B3"),
    "delta_justificativa": ("E", "EP"),
    "delta_espontanea": ("B2", "B1"),
}

PRIMARY_CONTRAST = "delta_pares"
