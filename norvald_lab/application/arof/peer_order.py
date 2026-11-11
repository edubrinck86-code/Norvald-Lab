"""Ordem sorteada das contribuições dos pares na condição exposta (E).

Por quê (11/11/2026): o TESE-002 §4.1 exige que a ordem em que os pares
aparecem em E seja sorteada por execução e gravada. Até aqui o Lab mostrava
sempre a ordem do spec: o primeiro participante aparecia sempre primeiro.
Assim, um efeito de posição (dar mais peso ao que se lê primeiro ou por
último) ficava misturado com o efeito de quem é o participante, e não podia
ser separado depois.

Só a ordem de apresentação muda. O contexto é semeado uma vez por leva, na
ordem do spec, e depois cada participante recebe os mesmos itens, com os
mesmos ids e o mesmo conteúdo, reagrupados por autor na ordem sorteada para
ele. O estímulo continua comum à leva (TESE-001 §4.2); muda só a posição.

O sorteio é determinístico: a semente sai do id do experimento, da repetição
e do participante. Ninguém escolhe a ordem, ela é reproduzível e fica gravada
em cada execução, para virar covariável na análise.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Sequence

PEER_ORDER_METHOD = "sha256-seeded-shuffle-v1"


def peer_order_seed(experiment_id: str, repetition_index: int, participant_id: str) -> int:
    digest = hashlib.sha256(f"{experiment_id}:{repetition_index}:{participant_id}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def draw_peer_order(peer_ids: Sequence[str], *, experiment_id: str, repetition_index: int, participant_id: str) -> list[str]:
    """Devolve os ids dos pares na ordem sorteada para esta execução."""
    order = list(peer_ids)
    random.Random(peer_order_seed(experiment_id, repetition_index, participant_id)).shuffle(order)
    return order


def reorder_by_author(context: dict[str, Any], peer_order: Sequence[str]) -> dict[str, Any]:
    """Reagrupa itens e relações dos pares na ordem dada, sem mudar mais nada.

    Itens sem autor da lista (as opções, por exemplo) ficam na frente, como
    estavam. Dentro de cada autor, a ordem original é mantida (sort estável).
    Não altera o dicionário recebido.
    """
    rank = {author: position for position, author in enumerate(peer_order)}

    def key(entry: dict[str, Any]) -> int:
        return rank.get(entry.get("author_id"), -1)

    reordered = dict(context)
    reordered["items"] = sorted(context.get("items", []), key=key)
    reordered["relations"] = sorted(context.get("relations", []), key=key)
    return reordered
