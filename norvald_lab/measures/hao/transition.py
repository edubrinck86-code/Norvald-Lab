"""Classifica uma mudança de resposta pelo efeito no acerto (Hao et al., §3 item 3).

C→W: era certa, ficou errada ("harmful"); W→C: era errada, ficou certa
("beneficial"); W→W: trocou de resposta errada sem mudar o acerto. Sem
mudança, None. Sem gabarito, None.
"""

from __future__ import annotations


def transition(before: str, after: str, answer: str | None) -> str | None:
    if answer is None or before == after:
        return None
    if before == answer:
        return "C→W"
    if after == answer:
        return "W→C"
    return "W→W"
