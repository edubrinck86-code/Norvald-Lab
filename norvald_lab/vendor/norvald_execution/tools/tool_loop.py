"""Ciclo de uso de ferramentas dentro de um turno."""

import asyncio
import itertools
import json
import unicodedata
import time
import uuid
from typing import Awaitable, Callable, List, Optional

from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.tool_contracts import ToolExchange
from norvald_lab.vendor.norvald_execution.contracts.tool_ports import ToolRuntimePort as ToolRuntime
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall, ToolResult
from norvald_lab.vendor.norvald_execution.tools.tool_context import compact_tool_exchanges, tool_context_chars
from norvald_lab.vendor.norvald_execution.tools.tool_syntax import is_only_tool_syntax, strip_tool_syntax

NATURAL_MAX_TOOL_ITERATIONS: Optional[int] = None
DEFAULT_MAX_NO_PROGRESS_CYCLES = 6
DEFAULT_STALL_PROFILE = "execution"
# Perfis declarados pelo domínio. Hoje todos com o mesmo teto — a
# estrutura existe porque o teto por perfil já era intenção do Studio
# (assistente e especialista tinham constantes separadas), não porque
# alguém precise de valores diferentes agora.
STALL_LIMIT_BY_PROFILE = {}
MAX_CONCURRENT_TOOL_EXECUTIONS = 6
WEB_SEARCH = "web_search"

MAX_CONTEXT_SCAN_REFUSALS = 2
def _usa_varredura(registry) -> bool:
    """O runtime deste domínio tem varredura de contexto?"""
    return callable(getattr(registry, "context_scan_required", None))


def _ferramentas_operacionais(registry) -> set:
    """Ferramentas que o próprio mecanismo dispara, e que por isso não
    contam como iniciativa do modelo.

    Quais são, quem diz é o runtime do domínio: no Studio são a busca no
    Working Context e a varredura; em outro domínio serão outras.
    """
    declaradas = getattr(registry, "operational_tools", None)
    return set(declaradas() if callable(declaradas) else declaradas or ())


def _stall_profile(request: ExecutionRequest) -> str:
    """Qual perfil de paciência vale para esta execução.

    Antes era `request.agent_id == "studio-assistant"`: o mecanismo
    reconhecia um agente do Studio pelo nome. Agora o domínio declara o
    perfil no metadata; quem não declara usa o padrão.
    """
    metadata = getattr(request.context, "metadata", None) if request.context else None
    perfil = metadata.get("stall_profile") if isinstance(metadata, dict) else None
    return str(perfil) if perfil else DEFAULT_STALL_PROFILE


def _teto_de_chamadas(request: ExecutionRequest) -> Optional[int]:
    """None = conclusão natural; número = intervenção explícita."""
    informado = getattr(request, "max_tool_calls", None)
    return None if informado is None else max(0, informado)


def _teto_web(request: ExecutionRequest) -> Optional[int]:
    """Web não possui budget nativo separado."""
    return None


def _stall_limit(request: ExecutionRequest) -> int:
    return STALL_LIMIT_BY_PROFILE.get(_stall_profile(request), DEFAULT_MAX_NO_PROGRESS_CYCLES)


def _stall_reason(request: ExecutionRequest) -> str:
    return f"{_stall_profile(request)}_no_progress"


def _successful_audit_count(audit: List[dict]) -> int:
    return sum(1 for item in audit if not item.get("is_error"))

def _describe(call: ToolCall, result: ToolResult, elapsed: float) -> dict:
    return {"name": call.name, "arguments": call.arguments, "result_chars": len(result.content), "is_error": result.is_error, "duration_seconds": round(elapsed, 3), "provenance": result.provenance_dicts()}


def _provenance(audit: List[dict]) -> List[dict]:
    return [{"tool_name": item["name"], **source} for item in audit for source in item.get("provenance", [])]

def _provider_state(result: ExecutionResult) -> dict:
    state = (result.metadata or {}).get("provider_state")
    return dict(state) if isinstance(state, dict) else {}


def _exchange_from_result(result: ExecutionResult, results: List[ToolResult]) -> ToolExchange:
    return ToolExchange(
        calls=list(result.tool_calls),
        results=results,
        assistant_text=result.content,
        provider_state=_provider_state(result),
    )



def _normalizar_valor(valor):
    """Texto sem acento, caixa nem pontuação, para comparar consultas.

    A assinatura era o JSON literal dos argumentos: trocar a caixa ou
    acrescentar uma palavra escapava da deduplicação. É exatamente o que
    um modelo faz quando não encontra o que procura — reformula um pouco
    e tenta de novo, gastando a rodada em buscas que devolvem o mesmo.

    Compara o conjunto de palavras, não a frase: "Constitution template"
    e "template Constitution" procuram a mesma coisa.
    """
    if not isinstance(valor, str):
        return valor
    dobrado = unicodedata.normalize("NFD", valor)
    limpo = "".join(
        c.lower() if c.isalnum() or c.isspace() else " "
        for c in dobrado
        if unicodedata.category(c) != "Mn"
    )
    palavras = limpo.split()
    # Descartar palavras curtas ajuda a ignorar preposições, mas números e
    # identificadores curtos fazem parte da identidade da consulta:
    # "consulta-0" e "consulta-1" não são a mesma busca. Sem preservá-los,
    # o guard de repetição pode fabricar um stall e encerrar o turno cedo.
    significativas = [
        p
        for p in palavras
        if len(p) > 2 or any(ch.isdigit() for ch in p)
    ]
    return " ".join(sorted(significativas or palavras))


def _assinatura(call: ToolCall) -> tuple:
    normalizados = {
        chave: _normalizar_valor(valor) for chave, valor in (call.arguments or {}).items()
    }
    return (call.name, json.dumps(normalizados, sort_keys=True, ensure_ascii=False))


async def _executar(call: ToolCall, registry: ToolRuntime, audit: List[dict]) -> ToolResult:
    started = time.monotonic()
    result = await asyncio.to_thread(registry.execute, call)
    audit.append(_describe(call, result, time.monotonic() - started))
    return result


async def _executar_lote(calls: List[ToolCall], registry: ToolRuntime, audit: List[dict]) -> List[ToolResult]:
    if not calls:
        return []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TOOL_EXECUTIONS)

    async def run(call: ToolCall) -> ToolResult:
        async with semaphore:
            return await _executar(call, registry, audit)

    return await asyncio.gather(*(run(call) for call in calls))


def _budget_result(call: ToolCall) -> ToolResult:
    return ToolResult(call_id=call.call_id, name=call.name, content=("O orçamento explícito de pesquisa Web desta condição foi atingido. Use e compare as fontes já obtidas e responda, ou declare se a evidência ainda é insuficiente."), is_error=False)


def _separar_execucoes(
    calls: List[ToolCall],
    ja_consultado: set,
    web_search_count: int,
    web_search_budget: Optional[int] = None,
):
    results = []
    executaveis: List[ToolCall] = []
    for call in calls:
        ja_consultado.add(_assinatura(call))
        if (
            call.name == WEB_SEARCH
            and web_search_budget is not None
            and web_search_count >= web_search_budget
        ):
            results.append(_budget_result(call))
            continue
        results.append(None)
        executaveis.append(call)
        if call.name == WEB_SEARCH:
            web_search_count += 1
    return results, executaveis, web_search_count


def _mesclar_resultados(results, executados: List[ToolResult]) -> List[ToolResult]:
    it = iter(executados)
    return [next(it) if item is None else item for item in results]


def _preflight_call(request: ExecutionRequest, registry) -> Optional[ToolCall]:
    """A chamada que o domínio exige antes de qualquer outra.

    Era fixa: buscar no Working Context. Mas "consultar primeiro o
    conhecimento já consolidado" é a política; *qual* é esse
    conhecimento é do domínio. Agora o runtime declara a chamada — e
    quem não declara nenhuma simplesmente não tem preflight.
    """
    declara = getattr(registry, "make_preflight_call", None)
    return declara(request) if callable(declara) else None


async def _executar_preflight(request: ExecutionRequest, registry: ToolRuntime, ja_consultado: set, audit: List[dict]) -> Optional[ToolExchange]:
    """Executa a chamada obrigatória declarada pelo domínio, antes das
    demais ferramentas.

    Guarda determinística: o modelo continua livre para escolher o que
    vem depois, mas a primeira consulta do turno é a que o domínio
    exige.
    """
    call = _preflight_call(request, registry)
    if call is None:
        return None
    ja_consultado.add(_assinatura(call))
    result = await _executar(call, registry, audit)
    return ToolExchange(calls=[call], results=[result], assistant_text="")


async def _iniciar_varredura_wc(
    request: ExecutionRequest,
    registry: ToolRuntime,
    ja_consultado: set,
    audit: List[dict],
) -> Optional[ToolExchange]:
    """Entrega o primeiro bloco antes da primeira resposta.

    Só acontece quando o runtime do domínio declara varredura
    obrigatória — quem não tem varredura não paga por ela.
    """
    if not _usa_varredura(registry) or not registry.context_scan_required():
        return None
    call = registry.make_initial_context_scan_call()
    if call is None:
        return None
    ja_consultado.add(_assinatura(call))
    result = await _executar(call, registry, audit)
    return ToolExchange(calls=[call], results=[result], assistant_text="")


def _instructions_for_iteration(
    request: ExecutionRequest,
    registry: ToolRuntime,
    no_progress_cycles: int,
) -> str:
    instructions = _continuation_instructions(request, no_progress_cycles)
    if _usa_varredura(registry) and registry.context_scan_pending():
        scan = registry.context_scan_instruction()
        if scan:
            instructions += "\n\n" + scan
    return instructions


def _chargeable_tool_calls(calls: List[ToolCall], registry=None) -> int:
    operacionais = _ferramentas_operacionais(registry)
    return sum(1 for call in calls if call.name not in operacionais)


def _chargeable_audit_calls(audit: List[dict], registry=None) -> int:
    operacionais = _ferramentas_operacionais(registry)
    return sum(1 for item in audit if item.get("name") not in operacionais)


def _ensure_scan_finished(registry: ToolRuntime, reason: str) -> None:
    if registry.context_scan_pending():
        raise RuntimeError(
            "A execução tentou encerrar antes de concluir a varredura "
            f"canônica obrigatória do Working Context ({reason})."
        )


async def _executar_novas_com_repeticoes(
    calls: List[ToolCall],
    ja_consultado: set,
    web_search_count: int,
    registry: ToolRuntime,
    audit: List[dict],
    web_search_budget: Optional[int] = None,
):
    results = []
    executaveis: List[ToolCall] = []
    for call in calls:
        assinatura = _assinatura(call)
        if assinatura in ja_consultado:
            results.append(ToolResult(call_id=call.call_id, name=call.name, content=(f"Esta consulta a '{call.name}' é idêntica a uma que você já fez neste turno, e devolveria o mesmo resultado. Responda com o que já tem, mude a consulta ou declare a insuficiência."), is_error=False))
            continue
        if (
            call.name == WEB_SEARCH
            and web_search_budget is not None
            and web_search_count >= web_search_budget
        ):
            results.append(_budget_result(call))
            ja_consultado.add(assinatura)
            continue
        ja_consultado.add(assinatura)
        results.append(None)
        executaveis.append(call)
        if call.name == WEB_SEARCH:
            web_search_count += 1
    executed = await _executar_lote(executaveis, registry, audit)
    return _mesclar_resultados(results, executed), web_search_count


def _synthesis_instructions(request: ExecutionRequest) -> str:
    return (f"{request.instructions}\n\nENCERRAMENTO OBRIGATÓRIO DESTE TURNO:\nVocê está na etapa final de síntese. As ferramentas já foram executadas e seus resultados estão no histórico abaixo. NÃO faça novas consultas. Produza agora a resposta final ao usuário usando essas evidências. Se as evidências forem insuficientes, diga isso explicitamente. Não espere outra rodada nem peça para consultar uma ferramenta.")


def _final_request(request: ExecutionRequest, exchanges: List[ToolExchange]) -> ExecutionRequest:
    return ExecutionRequest(agent_id=request.agent_id, instructions=_synthesis_instructions(request), shared_instructions=request.shared_instructions, wave_instructions=request.wave_instructions, context=request.context, user_message=request.user_message, attachments=request.attachments, reasoning_effort=request.reasoning_effort, sampling=request.sampling, allow_tools=False, tools=[], tool_exchanges=compact_tool_exchanges(exchanges))


def _texto_ja_produzido(exchanges: List[ToolExchange]) -> str:
    """O que o modelo escreveu junto das chamadas de ferramenta.

    Um modelo pode responder e pedir ferramenta na mesma mensagem. Esse
    texto era descartado — `on_discard` só avisava a tela — e a aposta
    era que a síntese final o reproduziria. Quando ela vem vazia, porque
    o modelo considera que já respondeu, o turno inteiro se perde: as
    ferramentas rodaram, o conhecimento foi consultado, e o especialista
    não deixou nada.

    Guardar não é reaproveitar cegamente: só entra se a síntese não
    produzir texto próprio.
    """
    # Limpo antes de recuperar: o texto escrito junto das chamadas
    # costuma ser a própria chamada em prosa, e recuperá-la sem limpar
    # entregaria a marcação do protocolo como se fosse a análise.
    partes = [
        limpo
        for exchange in exchanges
        if (limpo := strip_tool_syntax(exchange.assistant_text or ""))
    ]
    return "\n\n".join(partes)


def _garantir_resposta(result: ExecutionResult, exchanges: List[ToolExchange]) -> ExecutionResult:
    """Um turno nunca termina em branco.

    Se a síntese não devolveu texto, recupera o que foi escrito durante
    a fase de ferramentas. Sem isso o especialista aparece na timeline
    sem resposta, e nem quem lê nem a rodada seguinte sabem se ele não
    tinha o que dizer ou se algo se perdeu no caminho.
    """
    # A síntese também pode vir só com marcação vazada — visto em
    # deliberação real, com as ferramentas nativas funcionando ao lado.
    if is_only_tool_syntax(result.content or ""):
        result.content = ""
        result.metadata = {**result.metadata, "tool_syntax_stripped": True}
    elif (result.content or "").strip():
        limpo = strip_tool_syntax(result.content)
        if limpo != result.content:
            result.content = limpo
            result.metadata = {**result.metadata, "tool_syntax_stripped": True}
        return result

    recuperado = _texto_ja_produzido(exchanges)
    if recuperado:
        result.content = recuperado
        result.metadata = {**result.metadata, "content_recovered_from_tool_phase": True}
        return result
    # Nem síntese nem texto na fase de ferramentas: declarar é melhor que
    # gravar vazio, que se lê como "não quis contribuir".
    result.content = (
        "[O especialista consultou as ferramentas e não produziu resposta "
        "nesta rodada.]"
    )
    result.metadata = {**result.metadata, "empty_synthesis": True}
    return result


async def _final_stream_answer(execute_stream: Callable[[ExecutionRequest], Awaitable[ExecutionResult]], request: ExecutionRequest, exchanges: List[ToolExchange]) -> ExecutionResult:
    return _garantir_resposta(await execute_stream(_final_request(request, exchanges)), exchanges)


async def _final_answer(execute: Callable[[ExecutionRequest], Awaitable[ExecutionResult]], request: ExecutionRequest, exchanges: List[ToolExchange]) -> ExecutionResult:
    return _garantir_resposta(await execute(_final_request(request, exchanges)), exchanges)


def _decorate_final_result(result: ExecutionResult, *, total_tokens: int, input_tokens: int, output_tokens: int, audit: List[dict], reason: str, iterations: int, stream: bool, tool_context_size: int = 0) -> ExecutionResult:
    result.tokens = total_tokens
    result.input_tokens = input_tokens
    result.output_tokens = output_tokens
    result.metadata = {**result.metadata, "tool_calls": audit, "provenance": _provenance(audit), "tool_loop_truncated": True, "tool_loop_reason": reason, "tool_loop_iterations": iterations, "tool_context_chars": tool_context_size, "stream_content_ready": stream}
    return result



def _continuation_instructions(
    request: ExecutionRequest,
    no_progress_cycles: int,
) -> str:
    if no_progress_cycles <= 0:
        return request.instructions
    if _stall_profile(request) == "assistant":
        return (
            request.instructions
            + "\n\nCONTINUIDADE OPERACIONAL DO ASSISTANT:\n"
            + "Uma ou mais chamadas não produziram progresso novo. "
              "Não repita a mesma chamada. Mude ferramenta, argumentos "
              "ou estratégia e continue. Só responda sem tool_calls quando "
              "a solicitação estiver concluída de ponta a ponta ou houver "
              "impedimento externo real."
        )
    return (
        request.instructions
        + "\n\nCONTINUIDADE DO ESPECIALISTA:\n"
        + "Uma ou mais consultas não produziram progresso novo. A chamada "
          "repetida não será executada novamente. Mude consulta, fonte ou "
          "estratégia se ainda precisar investigar. Se já houver fundamento "
          "suficiente, encerre naturalmente produzindo sua Contribution. "
          "Não continue pesquisando apenas porque ferramentas estão disponíveis."
    )


async def resolve_tools_then_stream(
    execute: Callable[[ExecutionRequest], Awaitable[ExecutionResult]],
    execute_stream: Callable[[ExecutionRequest], Awaitable[ExecutionResult]],
    request: ExecutionRequest,
    registry: Optional[ToolRuntime],
    max_iterations: Optional[int] = NATURAL_MAX_TOOL_ITERATIONS,
    on_discard: Callable[[], None] = lambda: None,
) -> ExecutionResult:
    if registry is None or not request.tools:
        return await execute_stream(request)

    exchanges: List[ToolExchange] = list(request.tool_exchanges)
    audit: List[dict] = []
    total_tokens = input_tokens = output_tokens = 0
    ja_consultado: set = set()
    web_search_count = 0
    wc_preflight_done = False
    no_progress_cycles = 0
    scan_refusals = 0
    web_search_budget = _teto_web(request)

    initial_scan = await _iniciar_varredura_wc(
        request, registry, ja_consultado, audit
    )
    if initial_scan is not None:
        exchanges.append(initial_scan)
        wc_preflight_done = True

    iterations = (
        itertools.count()
        if max_iterations is None
        else range(max_iterations)
    )

    for iteration in iterations:
        visible_exchanges = compact_tool_exchanges(exchanges)
        probe = ExecutionRequest(
            agent_id=request.agent_id,
            instructions=_instructions_for_iteration(
                request, registry, no_progress_cycles
            ),
            shared_instructions=request.shared_instructions,
            wave_instructions=request.wave_instructions,
            context=request.context,
            user_message=request.user_message,
            attachments=request.attachments,
            model=request.model,
            reasoning_effort=request.reasoning_effort,
            sampling=request.sampling,
            allow_tools=request.allow_tools,
            tools=request.tools,
            max_tool_calls=request.max_tool_calls,
            max_tool_iterations=request.max_tool_iterations,
            tool_exchanges=visible_exchanges,
        )
        result = await execute_stream(probe)

        if result.tool_calls and result.content:
            on_discard()

        total_tokens += result.tokens
        input_tokens += result.input_tokens
        output_tokens += result.output_tokens

        if not result.tool_calls:
            if registry.context_scan_pending():
                scan_refusals += 1
                if scan_refusals >= MAX_CONTEXT_SCAN_REFUSALS:
                    _ensure_scan_finished(
                        registry, "o modelo não chamou o próximo bloco"
                    )
                # O bloco atual continua sendo o último ToolExchange enviado.
                # Repetimos a requisição com a instrução operacional explícita,
                # sem avançar nem escolher IDs em nome da LLM.
                continue
            result.tokens = total_tokens
            result.input_tokens = input_tokens
            result.output_tokens = output_tokens
            result.metadata = {
                **result.metadata,
                **({"tool_calls": audit} if audit else {}),
                **(
                    {"provenance": _provenance(audit)}
                    if audit
                    else {}
                ),
                "tool_context_chars": tool_context_chars(
                    visible_exchanges
                ),
                "stream_content_ready": True,
                "tool_loop_truncated": False,
                "tool_loop_reason": "natural_completion",
                "tool_loop_iterations": iteration + 1,
            }
            return _garantir_resposta(result, exchanges)

        tool_budget = _teto_de_chamadas(request)
        model_calls_used = _chargeable_audit_calls(audit, registry)
        if (
            tool_budget is not None
            and model_calls_used + _chargeable_tool_calls(result.tool_calls, registry)
            > tool_budget
        ):
            _ensure_scan_finished(registry, "orçamento de ferramentas")
            final_result = await _final_stream_answer(
                execute_stream, request, exchanges
            )
            total_tokens += final_result.tokens
            input_tokens += final_result.input_tokens
            output_tokens += final_result.output_tokens
            return _decorate_final_result(
                final_result,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                audit=audit,
                reason="tool_call_budget_exceeded",
                iterations=iteration + 1,
                stream=True,
                tool_context_size=tool_context_chars(
                    compact_tool_exchanges(exchanges)
                ),
            )

        if not wc_preflight_done:
            preflight = await _executar_preflight(request, registry, ja_consultado, audit)
            if preflight is not None:
                exchanges.append(preflight)
            wc_preflight_done = True

        repetidas = [
            call
            for call in result.tool_calls
            if _assinatura(call) in ja_consultado
        ]
        success_before = _successful_audit_count(audit)

        if repetidas:
            results, web_search_count = (
                await _executar_novas_com_repeticoes(
                    result.tool_calls,
                    ja_consultado,
                    web_search_count,
                    registry,
                    audit,
                    web_search_budget,
                )
            )
            exchanges.append(
                _exchange_from_result(result, results)
            )
        else:
            (
                results,
                executaveis,
                web_search_count,
            ) = _separar_execucoes(
                result.tool_calls,
                ja_consultado,
                web_search_count,
                web_search_budget,
            )
            executed = await _executar_lote(
                executaveis, registry, audit
            )
            exchanges.append(
                _exchange_from_result(
                    result,
                    _mesclar_resultados(
                        results, executed
                    ),
                )
            )

        success_after = _successful_audit_count(audit)
        if success_after > success_before:
            scan_refusals = 0
        no_progress_cycles = (
            0
            if success_after > success_before
            else no_progress_cycles + 1
        )

        if no_progress_cycles >= _stall_limit(request):
            _ensure_scan_finished(registry, "ciclo sem progresso")
            final_result = await _final_stream_answer(
                execute_stream, request, exchanges
            )
            total_tokens += final_result.tokens
            input_tokens += final_result.input_tokens
            output_tokens += final_result.output_tokens
            return _decorate_final_result(
                final_result,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                audit=audit,
                reason=_stall_reason(request),
                iterations=iteration + 1,
                stream=True,
                tool_context_size=tool_context_chars(
                    compact_tool_exchanges(exchanges)
                ),
            )

    # Só é alcançado quando max_iterations foi explicitamente definido.
    _ensure_scan_finished(registry, "limite explícito de iterações")
    final_result = await _final_stream_answer(
        execute_stream, request, exchanges
    )
    total_tokens += final_result.tokens
    input_tokens += final_result.input_tokens
    output_tokens += final_result.output_tokens
    return _decorate_final_result(
        final_result,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        audit=audit,
        reason="iteration_limit",
        iterations=int(max_iterations or 0),
        stream=True,
        tool_context_size=tool_context_chars(
            compact_tool_exchanges(exchanges)
        ),
    )


async def execute_with_tools(
    execute: Callable[
        [ExecutionRequest], Awaitable[ExecutionResult]
    ],
    request: ExecutionRequest,
    registry: Optional[ToolRuntime],
    max_iterations: Optional[int] = NATURAL_MAX_TOOL_ITERATIONS,
) -> ExecutionResult:
    if registry is None or not request.tools:
        return await execute(request)

    exchanges: List[ToolExchange] = list(request.tool_exchanges)
    audit: List[dict] = []
    total_tokens = input_tokens = output_tokens = 0
    ja_consultado: set = set()
    web_search_count = 0
    wc_preflight_done = False
    no_progress_cycles = 0
    scan_refusals = 0
    web_search_budget = _teto_web(request)

    initial_scan = await _iniciar_varredura_wc(
        request, registry, ja_consultado, audit
    )
    if initial_scan is not None:
        exchanges.append(initial_scan)
        wc_preflight_done = True

    iterations = (
        itertools.count()
        if max_iterations is None
        else range(max_iterations)
    )

    for iteration in iterations:
        visible_exchanges = compact_tool_exchanges(exchanges)
        current = ExecutionRequest(
            agent_id=request.agent_id,
            instructions=_instructions_for_iteration(
                request, registry, no_progress_cycles
            ),
            shared_instructions=request.shared_instructions,
            wave_instructions=request.wave_instructions,
            context=request.context,
            user_message=request.user_message,
            attachments=request.attachments,
            model=request.model,
            reasoning_effort=request.reasoning_effort,
            sampling=request.sampling,
            allow_tools=request.allow_tools,
            tools=request.tools,
            max_tool_calls=request.max_tool_calls,
            max_tool_iterations=request.max_tool_iterations,
            tool_exchanges=visible_exchanges,
        )
        result = await execute(current)

        total_tokens += result.tokens
        input_tokens += result.input_tokens
        output_tokens += result.output_tokens

        if not result.tool_calls:
            if registry.context_scan_pending():
                scan_refusals += 1
                if scan_refusals >= MAX_CONTEXT_SCAN_REFUSALS:
                    _ensure_scan_finished(
                        registry, "o modelo não chamou o próximo bloco"
                    )
                continue
            result.tokens = total_tokens
            result.input_tokens = input_tokens
            result.output_tokens = output_tokens
            if audit:
                result.metadata = {
                    **result.metadata,
                    "tool_calls": audit,
                    "provenance": _provenance(audit),
                }
            result.metadata = {
                **result.metadata,
                "tool_context_chars": tool_context_chars(
                    visible_exchanges
                ),
                "tool_loop_truncated": False,
                "tool_loop_reason": "natural_completion",
                "tool_loop_iterations": iteration + 1,
            }
            return _garantir_resposta(result, exchanges)

        tool_budget = _teto_de_chamadas(request)
        model_calls_used = _chargeable_audit_calls(audit, registry)
        if (
            tool_budget is not None
            and model_calls_used + _chargeable_tool_calls(result.tool_calls, registry)
            > tool_budget
        ):
            _ensure_scan_finished(registry, "orçamento de ferramentas")
            final_result = await _final_answer(
                execute, request, exchanges
            )
            total_tokens += final_result.tokens
            input_tokens += final_result.input_tokens
            output_tokens += final_result.output_tokens
            return _decorate_final_result(
                final_result,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                audit=audit,
                reason="tool_call_budget_exceeded",
                iterations=iteration + 1,
                stream=False,
                tool_context_size=tool_context_chars(
                    compact_tool_exchanges(exchanges)
                ),
            )

        if not wc_preflight_done:
            preflight = await _executar_preflight(request, registry, ja_consultado, audit)
            if preflight is not None:
                exchanges.append(preflight)
            wc_preflight_done = True

        repetidas = [
            call
            for call in result.tool_calls
            if _assinatura(call) in ja_consultado
        ]
        success_before = _successful_audit_count(audit)

        if repetidas:
            results, web_search_count = (
                await _executar_novas_com_repeticoes(
                    result.tool_calls,
                    ja_consultado,
                    web_search_count,
                    registry,
                    audit,
                    web_search_budget,
                )
            )
            exchanges.append(
                _exchange_from_result(result, results)
            )
        else:
            (
                results,
                executaveis,
                web_search_count,
            ) = _separar_execucoes(
                result.tool_calls,
                ja_consultado,
                web_search_count,
                web_search_budget,
            )
            executed = await _executar_lote(
                executaveis, registry, audit
            )
            exchanges.append(
                _exchange_from_result(
                    result,
                    _mesclar_resultados(
                        results, executed
                    ),
                )
            )

        success_after = _successful_audit_count(audit)
        if success_after > success_before:
            scan_refusals = 0
        no_progress_cycles = (
            0
            if success_after > success_before
            else no_progress_cycles + 1
        )

        if no_progress_cycles >= _stall_limit(request):
            _ensure_scan_finished(registry, "ciclo sem progresso")
            final_result = await _final_answer(
                execute, request, exchanges
            )
            total_tokens += final_result.tokens
            input_tokens += final_result.input_tokens
            output_tokens += final_result.output_tokens
            return _decorate_final_result(
                final_result,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                audit=audit,
                reason=_stall_reason(request),
                iterations=iteration + 1,
                stream=False,
                tool_context_size=tool_context_chars(
                    compact_tool_exchanges(exchanges)
                ),
            )

    # Só é alcançado quando max_iterations foi explicitamente definido.
    _ensure_scan_finished(registry, "limite explícito de iterações")
    final_result = await _final_answer(
        execute, request, exchanges
    )
    total_tokens += final_result.tokens
    input_tokens += final_result.input_tokens
    output_tokens += final_result.output_tokens
    return _decorate_final_result(
        final_result,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        audit=audit,
        reason="iteration_limit",
        iterations=int(max_iterations or 0),
        stream=False,
        tool_context_size=tool_context_chars(
            compact_tool_exchanges(exchanges)
        ),
    )

