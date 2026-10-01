"""Controle de contexto para o ciclo de ferramentas.

O histórico completo das ferramentas continua existindo no orquestrador para
auditoria/proveniência. O que muda é apenas a representação enviada de volta
à LLM: um histórico de tools não pode crescer sem limite a cada round-trip.

A compactação é determinística e extrativa. Ela não chama outra LLM, não
altera o Working Context e não descarta a chamada/proveniência; apenas reduz
o texto de resultados antigos para manter o payload de cada nova chamada
limitado.
"""

from dataclasses import replace
from typing import List

from norvald_lab.vendor.norvald_execution.contracts.tool_contracts import ToolExchange

# Limites em caracteres, deliberadamente independentes do contexto do modelo.
# 30k caracteres representam uma fração pequena de um contexto moderno e,
# principalmente, impedem crescimento quadrático entre os round-trips.
# 30k caracteres somavam ~7,5k tokens por iteração, reenviados a cada
# round-trip e somados ao Working Context e ao prompt. Medido numa
# deliberação real: 360 mil tokens em 8 rodadas, com dois textos
# produzidos. O material das ferramentas é insumo para a síntese, não
# transcrição a carregar inteira.
MAX_TOOL_CONTEXT_CHARS = 26_000
# Leituras documentais são diferentes de resultados de busca: o conteúdo
# recém-pedido é o objeto de trabalho do próximo passo. Ele pode usar uma
# janela maior, mas somente enquanto for o exchange mais recente. Quando
# envelhece, volta aos mesmos limites compactos do restante do histórico.
DOCUMENT_READ_TOOLS = frozenset({
    "read_library_document",
    "read_artifact",
    "read_document",
    "cloud_read",
    "read_context_item",
    "read_contribution",
})
MAX_DOCUMENT_TOOL_CONTEXT_CHARS = 70_000
MAX_DOCUMENT_RECENT_EXCHANGE_CHARS = 66_000
MAX_DOCUMENT_RECENT_RESULT_CHARS = 65_000

MAX_RECENT_EXCHANGE_CHARS = 21_000
MAX_RECENT_RESULT_CHARS = 20_000
MAX_OLD_EXCHANGE_CHARS = 3_000
MAX_OLD_RESULT_CHARS = 1_200
MAX_ASSISTANT_TEXT_CHARS = 1_200


def _compact_text(text: str, limit: int) -> str:
    text = text or ""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    marker = "\n\n[... resultado compactado pelo orquestrador ...]\n\n"
    if limit <= len(marker) + 2:
        return text[:limit]
    available = limit - len(marker)
    head = max(1, int(available * 0.68))
    tail = max(1, available - head)
    omitted = len(text) - head - tail
    marker = f"\n\n[... resultado compactado pelo orquestrador: {omitted} caracteres omitidos ...]\n\n"
    if len(marker) > limit:
        return text[:limit]
    available = limit - len(marker)
    head = max(1, int(available * 0.68))
    tail = max(1, available - head)
    return f"{text[:head]}{marker}{text[-tail:]}"


def _exchange_chars(exchange: ToolExchange) -> int:
    return len(exchange.assistant_text or "") + sum(len(result.content or "") for result in exchange.results)


def _compact_exchange(exchange: ToolExchange, *, result_limit: int, exchange_limit: int) -> ToolExchange:
    """Cria uma cópia limitada sem tocar no histórico original."""
    assistant_text = _compact_text(exchange.assistant_text or "", min(MAX_ASSISTANT_TEXT_CHARS, exchange_limit // 5))
    remaining = max(0, exchange_limit - len(assistant_text))
    results = []
    total_results = len(exchange.results)
    for index, result in enumerate(exchange.results):
        if remaining <= 0:
            content = "[resultado anterior preservado na auditoria, omitido do contexto da LLM por orçamento]"
        else:
            pending = max(1, total_results - index)
            fair_share = max(1, remaining // pending)
            per_result = min(result_limit, fair_share)
            content = _compact_text(result.content, per_result)
        results.append(replace(result, content=content))
        remaining -= len(content)
    return replace(exchange, assistant_text=assistant_text, results=results)


def _is_document_read_exchange(exchange: ToolExchange) -> bool:
    return any(call.name in DOCUMENT_READ_TOOLS for call in exchange.calls)


def compact_tool_exchanges(exchanges: List[ToolExchange]) -> List[ToolExchange]:
    """Retorna uma visão limitada do histórico para o próximo request da LLM.

    O último exchange recebe prioridade porque contém a evidência mais nova.
    Exchanges anteriores continuam presentes em forma compactada, portanto a
    LLM mantém continuidade e pode comparar resultados, mas o payload não
    cresce proporcionalmente a cada rodada.
    """
    if not exchanges:
        return []

    compacted: List[ToolExchange] = []
    latest_is_document = _is_document_read_exchange(exchanges[-1])
    budget = (
        MAX_DOCUMENT_TOOL_CONTEXT_CHARS
        if latest_is_document
        else MAX_TOOL_CONTEXT_CHARS
    )

    for index in range(len(exchanges) - 1, -1, -1):
        exchange = exchanges[index]
        is_recent = index == len(exchanges) - 1
        recent_document = is_recent and _is_document_read_exchange(exchange)
        if recent_document:
            exchange_limit = min(MAX_DOCUMENT_RECENT_EXCHANGE_CHARS, budget)
            result_limit = MAX_DOCUMENT_RECENT_RESULT_CHARS
        else:
            exchange_limit = min(
                MAX_RECENT_EXCHANGE_CHARS if is_recent else MAX_OLD_EXCHANGE_CHARS,
                budget,
            )
            result_limit = (
                MAX_RECENT_RESULT_CHARS if is_recent else MAX_OLD_RESULT_CHARS
            )
        if exchange_limit <= 0:
            break
        view = _compact_exchange(exchange, result_limit=result_limit, exchange_limit=exchange_limit)
        compacted.append(view)
        budget -= _exchange_chars(view)
        if budget <= 0:
            break

    compacted.reverse()
    return compacted


def tool_context_chars(exchanges: List[ToolExchange]) -> int:
    """Mede o tamanho efetivamente enviado à LLM na visão compactada."""
    return sum(_exchange_chars(exchange) for exchange in exchanges)

