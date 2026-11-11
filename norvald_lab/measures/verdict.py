"""Leitura do intervalo contra a tabela de critérios (compatível / não compatível).

O bloco 1.2 só escreve dois casos por critério. O intervalo inteiro do lado
oposto ao previsto não está na tabela; aqui ele sai como "não compatível
(sinal oposto)", para não esconder a direção. Sem intervalo (sem dados),
"indeterminado".
"""

from __future__ import annotations

from norvald_lab.measures.interval import Interval

COMPATIVEL = "compatível"
NAO_COMPATIVEL = "não compatível"
SINAL_OPOSTO = "não compatível (sinal oposto)"
INDETERMINADO = "indeterminado (sem dados)"
A_DEFINIR = "a definir"


def side_text(side: str | None) -> str:
    return {"acima": "acima de 0", "abaixo": "abaixo de 0", "inclui": "inclui 0"}.get(side or "", "sem intervalo")


def directional(interval: Interval, *, expected: str, reference: float = 0.0) -> str:
    """expected: 'acima' ou 'abaixo' da referência."""
    side = interval.side(reference)
    if side is None:
        return INDETERMINADO
    if side == expected:
        return COMPATIVEL
    if side == "inclui":
        return NAO_COMPATIVEL
    return SINAL_OPOSTO
