"""Ordem do prompt para caching por prefixo.

Todos os providers que cacheiam prompt cacheiam por PREFIXO. O bloco
estável (evidências, formato da Contribution, instruções de ferramenta)
precisa vir antes do trecho que muda a cada participante e a cada
rodada, ou o prefixo nunca casa.
"""

from __future__ import annotations

from typing import List

from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest


def _ordered_blocks(request: ExecutionRequest) -> List[str]:
    """Do mais estável ao mais volátil.

    Três faixas, porque o cache é por prefixo e o Studio tem três
    escopos de estabilidade:

    1. `shared_instructions` — evidências, material de projeto,
       dimensões. Não muda entre rodadas.
    2. `wave_instructions` — o Working Context. Muda a cada rodada, mas
       é idêntico para todos os especialistas da mesma leva: o primeiro
       escreve o cache, os demais leem.
    3. `instructions` — nome, papel e rodada do participante. Varia
       sempre, e por isso vem por último: qualquer coisa depois dele
       seria impossível de cachear.
    """
    return [
        block
        for block in (request.shared_instructions, request.wave_instructions, request.instructions)
        if block
    ]


def system_text(request: ExecutionRequest) -> str:
    return "\n\n".join(_ordered_blocks(request)) or request.instructions


def _system_parts(request: ExecutionRequest) -> List[dict]:
    blocks = _ordered_blocks(request)
    return [{"text": block} for block in blocks] or [{"text": request.instructions}]

