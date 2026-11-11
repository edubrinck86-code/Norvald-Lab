"""new_grounds nas duas leituras de 344-75.

Fundamento novo = fundamento da contribuição da segunda onda que não está
entre os da própria B1 (mesmo tipo de alvo, mesma chave; ver `Ground`).

- estrita: só `base` e `local` contam. Fundamento que aponta para a
  contribuição de outro participante (`peer`) NÃO conta como novo; o que
  aponta para a contribuição anterior do próprio participante (`own`)
  também não, nas duas leituras.
- permissiva: o que a estrita conta, mais qualquer `peer`.
"""

from __future__ import annotations

from typing import Iterable

from norvald_lab.measures.ground import Ground

STRICT, PERMISSIVE = "estrita", "permissiva"
READINGS = (STRICT, PERMISSIVE)
_COUNTING = {STRICT: ("base", "local"), PERMISSIVE: ("base", "local", "peer")}


class NewGrounds:
    def has_new(self, first_wave: Iterable[Ground], later: Iterable[Ground], reading: str) -> bool:
        known = set(first_wave)
        counting = _COUNTING[reading]
        return any(g.scope in counting and g not in known for g in later)
