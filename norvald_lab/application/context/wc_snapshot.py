from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from norvald_lab.domain.deliberation.working_context import WorkingContext


@dataclass(frozen=True)
class WCSnapshot:
    """Tamanho e composição do Working Context num instante.

    Deliberadamente contagens, não conteúdo. Guardar o WC inteiro antes e
    depois de cada contribuição duplicaria a fonte de verdade a cada
    turno e cresceria com o quadrado da deliberação — e a pergunta que a
    telemetria responde ("o que mudou de tamanho e de forma") não precisa
    do texto dos itens. Quem quiser o conteúdo lê o Working Context, que
    continua sendo o original.
    """

    items: int
    relations: int
    by_type: dict[str, int]

    @classmethod
    def capture(cls, context: WorkingContext) -> "WCSnapshot":
        payload = context.to_dict()
        items = payload.get("items") or []
        relations = payload.get("relations") or []
        counter: Counter[str] = Counter()
        for item in items:
            kind = (item.get("type") if isinstance(item, dict) else getattr(item, "type", None)) or "unknown"
            counter[str(kind)] += 1
        return cls(items=len(items), relations=len(relations), by_type=dict(counter))

    def as_dict(self) -> dict[str, Any]:
        return {"items": self.items, "relations": self.relations, "by_type": dict(self.by_type)}


def type_delta(before: WCSnapshot, after: WCSnapshot) -> dict[str, int]:
    """Variação por tipo, incluindo tipos que só existem de um dos lados.

    Um tipo que desapareceu vale tanto quanto um que surgiu; iterar só
    sobre o `after` esconderia remoções.
    """
    kinds = set(before.by_type) | set(after.by_type)
    return {
        kind: after.by_type.get(kind, 0) - before.by_type.get(kind, 0)
        for kind in sorted(kinds)
        if after.by_type.get(kind, 0) != before.by_type.get(kind, 0)
    }

