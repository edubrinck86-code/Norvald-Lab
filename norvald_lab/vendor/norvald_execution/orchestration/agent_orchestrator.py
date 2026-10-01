from dataclasses import replace
import re
import json
import time
import uuid
from typing import Callable, Optional

from norvald_lab.vendor.norvald_execution.support.provider_gate import provider_gate
from norvald_lab.vendor.norvald_execution.contracts.tool_ports import ToolLoopPort, ToolRuntimePort
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.support.retry import with_retry
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry
from norvald_lab.vendor.norvald_execution.support import pricing_cache
from norvald_lab.vendor.norvald_execution.orchestration.execution_observer import ExecutionEvent, ExecutionObserver, NullExecutionObserver
from norvald_lab.vendor.norvald_execution.support.provider_intelligence import provider_intelligence_cache

DISCARD_MARKER = "\x00discard\x00"

_PURE_CONVERSATIONAL_RE = re.compile(
    r"^(?:oi|olá|ola|olá!|ola!|oi!|hey|hello|hi|bom dia|boa tarde|boa noite|obrigado|obrigada|valeu|tchau|até mais|ate mais|ok|okay|certo|beleza|blz)[.!?]*$",
    re.IGNORECASE,
)


def _is_pure_conversational_turn(user_message: Optional[str]) -> bool:
    normalized = re.sub(r"\s+", " ", (user_message or "").strip()).lower()
    return bool(normalized and _PURE_CONVERSATIONAL_RE.fullmatch(normalized))


def _requires_wc_scan(request: ExecutionRequest) -> bool:
    metadata = request.context.metadata if request.context else {}
    return bool(
        isinstance(metadata, dict)
        and metadata.get("wc_scan_required")
        and request.agent_id != "studio-assistant"
    )


def _chamar_stream(stream_method, request, model, on_delta, on_reasoning_delta):
    try:
        return stream_method(request, model, on_delta, on_reasoning_delta)
    except TypeError as exc:
        if "positional argument" not in str(exc):
            raise
        return stream_method(request, model, on_delta)


class AgentOrchestrator:
    def __init__(
        self,
        registry: AgentRegistry,
        tool_registry: Optional[ToolRuntimePort] = None,
        execution_observer: Optional[ExecutionObserver] = None,
        tool_loop: Optional[ToolLoopPort] = None,
    ):
        self.registry = registry
        self.tool_registry = tool_registry
        self.execution_observer = execution_observer or NullExecutionObserver()
        # O laço de ferramentas é injetado: o orquestrador sabe que ele
        # existe, não como funciona. Sem laço, executa sem ferramentas —
        # que é o certo para quem não as tem.
        self.tool_loop = tool_loop

    def _tools_for(
        self,
        request: ExecutionRequest,
        provider,
        runtime: Optional[ToolRuntimePort] = None,
    ) -> list:
        if self.tool_registry is None or self.tool_loop is None or not request.allow_tools:
            return []
        if not getattr(provider, "SUPPORTS_TOOL_USE", False):
            return []
        if _is_pure_conversational_turn(request.user_message):
            return []
        source = runtime or self.tool_registry
        return source.definitions()

    def _runtime_for(self, request: ExecutionRequest, on_tool_event: Optional[Callable[[str, dict], None]] = None) -> Optional[ToolRuntimePort]:
        if self.tool_registry is None:
            return None
        runtime = self.tool_registry.for_execution_context(request.context)
        if on_tool_event is not None:
            runtime._on_event = on_tool_event
        return runtime

    def _scope_of(self, request: ExecutionRequest) -> dict:
        """O recorte declarado pelo domínio, com as partes nomeadas.

        Sessão e rodada no Studio; build e tentativa no Builder. O
        pacote não conhece nenhuma das duas listas — só preserva o que
        recebe, para que a auditoria possa perguntar por parte."""
        metadata = request.context.metadata if request.context else {}
        if not isinstance(metadata, dict):
            return {}
        scope = metadata.get("execution_scope")
        return dict(scope) if isinstance(scope, dict) else {}

    def _execution_id_of(self, request: ExecutionRequest) -> str:
        """Identifica esta execução para correlacionar eventos.

        Três formas, nesta ordem:

        1. `execution_id` no metadata — o domínio já nomeou a execução;
        2. `execution_scope` — as partes nomeadas que o domínio declara
           e que, juntas, distinguem uma execução das outras. O id junta
           os valores na ordem declarada; a auditoria não usa este id,
           usa as partes (ver `ExecutionEvent.scope`);
        3. o `agent_id`, quando nada foi declarado.

        A forma anterior montava a chave com `session_id`, `round` e
        `participant_id`: vocabulário da deliberação dentro da
        infraestrutura. Um build do Builder não tem rodada, e uma
        execução avulsa não tem participante.

        Ver `docs/Chave_de_Execucao.md`: a compatibilidade com o formato
        antigo está registrada lá, não resolvida.
        """
        metadata = request.context.metadata if request.context else {}
        if not isinstance(metadata, dict):
            return request.agent_id
        if metadata.get("execution_id"):
            return str(metadata["execution_id"])
        scope = metadata.get("execution_scope")
        if isinstance(scope, dict) and scope:
            return ":".join(str(valor) for valor in scope.values())
        return request.agent_id

    def _emit_pipeline(self, event: str, request: ExecutionRequest, **data: object) -> None:
        emitter = getattr(self.tool_registry, "_emit", None) if self.tool_registry is not None else None
        if not callable(emitter):
            return
        emitter(event, {"execution_id": self._execution_id_of(request), **data})

    def _record_success(self, event_id: str, request: ExecutionRequest, provider_name: str, model: str, scope: dict, result: ExecutionResult, duration_ms: float) -> None:
        result_metadata = dict(result.metadata or {})
        provider_kind = self.registry.provider_kind_for(request.agent_id)
        provider_intelligence_cache.record_success(provider_name, provider_kind, model, result_metadata)
        reported_cost = result_metadata.get("cost")
        resolved_provider = result.provider or provider_name
        resolved_model = result.model or model
        estimated_cost = pricing_cache.estimate_cost(resolved_provider, resolved_model, result.input_tokens, result.output_tokens)
        cost = reported_cost if isinstance(reported_cost, (int, float)) else estimated_cost
        self.execution_observer.record(ExecutionEvent(event_id=event_id, event_type="llm.request.completed", agent_id=request.agent_id, provider=resolved_provider, model=resolved_model, status="ok", latency_ms=duration_ms, input_tokens=result.input_tokens, output_tokens=result.output_tokens, cost=float(cost) if isinstance(cost, (int, float)) else None, scope=scope, metadata=result_metadata))

    def _record_failure(self, event_id: str, request: ExecutionRequest, provider_name: str, model: str, scope: dict, started: float, exc: Exception) -> None:
        provider_kind = self.registry.provider_kind_for(request.agent_id)
        provider_intelligence_cache.record_failure(provider_name, provider_kind, model, exc)
        self.execution_observer.record(ExecutionEvent(event_id=event_id, event_type="llm.request.failed", agent_id=request.agent_id, provider=provider_name, model=model, status="error", latency_ms=(time.monotonic() - started) * 1000, scope=scope, error=str(exc)))

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        provider, model = self.registry.resolve(request.agent_id)
        provider_name = self.registry.provider_name_for(request.agent_id)
        provider_kind = self.registry.provider_kind_for(request.agent_id)
        started = time.monotonic()
        event_id = str(uuid.uuid4())
        scope = self._scope_of(request)
        runtime = self._runtime_for(request)
        tools = self._tools_for(request, provider, runtime)
        if not tools:
            runtime = None
        request_number = 0

        async def provider_execute(req: ExecutionRequest) -> ExecutionResult:
            return await provider_gate().run(
                provider_name,
                lambda: _provider_execute(req),
                provider_kind=provider_kind,
                on_retry=lambda _attempt, _wait, exc: provider_intelligence_cache.record_failure(
                    provider_name, provider_kind, model, exc
                ),
            )

        async def _provider_execute(req: ExecutionRequest) -> ExecutionResult:
            nonlocal request_number
            request_number += 1
            request_id = str(uuid.uuid4())
            request_started = time.monotonic()
            diagnostics = _request_context_diagnostics(req, tools)
            self._emit_pipeline("provider.request.started", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, context_diagnostics=diagnostics)
            try:
                result = await with_retry(
                    lambda: provider.execute(req, model),
                    on_retry=lambda tentativa, espera, exc: (
                        provider_intelligence_cache.record_failure(provider_name, provider_kind, model, exc),
                        self._emit_pipeline("provider.request.retry", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, error=str(exc), attempt=tentativa, delay_seconds=round(espera, 3)),
                    ),
                )
                duration = result.duration_seconds if result.duration_seconds else time.monotonic() - request_started
                self._emit_pipeline("provider.request.completed", req, request_id=request_id, iteration=request_number, phase="provider", provider=result.provider or provider_name, model=result.model or model, duration_seconds=round(duration, 3), context_diagnostics=diagnostics)
                _append_request_diagnostic(result, request_number, diagnostics)
                return result
            except Exception as exc:
                self._emit_pipeline("provider.request.failed", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, error=str(exc), duration_seconds=round(time.monotonic() - request_started, 3), context_diagnostics=diagnostics)
                raise

        try:
            if _requires_wc_scan(request) and not tools:
                raise RuntimeError(
                    "Este turno exige varredura integral do Working Context, "
                    "mas o provider/modelo não disponibilizou tool use. "
                    "O Studio não continuará com um recorte silenciosamente."
                )
            if tools:
                request_with_tools = replace(request, tools=tools)
                result = await self.tool_loop.execute_with_tools(
                    provider_execute,
                    request_with_tools,
                    runtime,
                    max_iterations=request_with_tools.max_tool_iterations,
                )
            else:
                result = await provider_execute(request)
            duration_ms = result.duration_seconds * 1000 if result.duration_seconds else (time.monotonic() - started) * 1000
            result.metadata["advertised_tool_names"] = [
                tool.name for tool in tools
            ]
            result.metadata["provider_supports_tool_use"] = bool(
                getattr(provider, "SUPPORTS_TOOL_USE", False)
            )
            _annotate_tool_cost(result, tools, request_number)
            self._record_success(event_id, request, provider_name, model, scope, result, duration_ms)
            return result
        except Exception as exc:
            self._record_failure(event_id, request, provider_name, model, scope, started, exc)
            raise

    async def execute_stream(self, request: ExecutionRequest, on_delta: Callable[[str], None], on_reasoning_delta: Optional[Callable[[str], None]] = None, on_tool_event: Optional[Callable[[str, dict], None]] = None) -> ExecutionResult:
        provider, model = self.registry.resolve(request.agent_id)
        provider_name = self.registry.provider_name_for(request.agent_id)
        provider_kind = self.registry.provider_kind_for(request.agent_id)
        started = time.monotonic()
        event_id = str(uuid.uuid4())
        scope = self._scope_of(request)
        stream_method = getattr(provider, "execute_stream", None)
        runtime = self._runtime_for(request, on_tool_event)
        tools = self._tools_for(request, provider, runtime)
        if not tools:
            runtime = None
        request_number = 0

        async def provider_execute(req: ExecutionRequest) -> ExecutionResult:
            return await provider_gate().run(
                provider_name,
                lambda: _provider_execute(req),
                provider_kind=provider_kind,
                on_retry=lambda _attempt, _wait, exc: provider_intelligence_cache.record_failure(
                    provider_name, provider_kind, model, exc
                ),
            )

        async def _provider_execute(req: ExecutionRequest) -> ExecutionResult:
            nonlocal request_number
            request_number += 1
            request_id = str(uuid.uuid4())
            request_started = time.monotonic()
            diagnostics = _request_context_diagnostics(req, tools)
            self._emit_pipeline("provider.request.started", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, context_diagnostics=diagnostics)
            try:
                result = await with_retry(
                    lambda: provider.execute(req, model),
                    on_retry=lambda tentativa, espera, exc: (
                        provider_intelligence_cache.record_failure(provider_name, provider_kind, model, exc),
                        self._emit_pipeline("provider.request.retry", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, error=str(exc), attempt=tentativa, delay_seconds=round(espera, 3)),
                    ),
                )
                duration = result.duration_seconds if result.duration_seconds else time.monotonic() - request_started
                self._emit_pipeline("provider.request.completed", req, request_id=request_id, iteration=request_number, phase="provider", provider=result.provider or provider_name, model=result.model or model, duration_seconds=round(duration, 3), context_diagnostics=diagnostics)
                _append_request_diagnostic(result, request_number, diagnostics)
                return result
            except Exception as exc:
                self._emit_pipeline("provider.request.failed", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, error=str(exc), duration_seconds=round(time.monotonic() - request_started, 3), context_diagnostics=diagnostics)
                raise

        async def provider_stream(req: ExecutionRequest) -> ExecutionResult:
            return await provider_gate().run(
                provider_name,
                lambda: _provider_stream(req),
                provider_kind=provider_kind,
                on_retry=lambda _attempt, _wait, exc: provider_intelligence_cache.record_failure(
                    provider_name, provider_kind, model, exc
                ),
            )

        async def _provider_stream(req: ExecutionRequest) -> ExecutionResult:
            nonlocal request_number
            request_number += 1
            request_id = str(uuid.uuid4())
            request_started = time.monotonic()
            diagnostics = _request_context_diagnostics(req, tools)
            self._emit_pipeline("provider.request.started", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, context_diagnostics=diagnostics)
            try:
                if stream_method is not None:
                    result = await _chamar_stream(stream_method, req, model, on_delta, on_reasoning_delta)
                else:
                    result = await provider.execute(req, model)
                    if result.content:
                        on_delta(result.content)
                duration = result.duration_seconds if result.duration_seconds else time.monotonic() - request_started
                self._emit_pipeline("provider.request.completed", req, request_id=request_id, iteration=request_number, phase="provider", provider=result.provider or provider_name, model=result.model or model, duration_seconds=round(duration, 3), context_diagnostics=diagnostics)
                _append_request_diagnostic(result, request_number, diagnostics)
                return result
            except Exception as exc:
                self._emit_pipeline("provider.request.failed", req, request_id=request_id, iteration=request_number, phase="provider", provider=provider_name, model=model, error=str(exc), duration_seconds=round(time.monotonic() - request_started, 3), context_diagnostics=diagnostics)
                raise

        try:
            if _requires_wc_scan(request) and not tools:
                raise RuntimeError(
                    "Este turno exige varredura integral do Working Context, "
                    "mas o provider/modelo não disponibilizou tool use. "
                    "O Studio não continuará com um recorte silenciosamente."
                )
            if tools:
                request_with_tools = replace(request, tools=tools)
                result = await self.tool_loop.resolve_tools_then_stream(
                    provider_execute,
                    provider_stream,
                    request_with_tools,
                    runtime,
                    max_iterations=request_with_tools.max_tool_iterations,
                    on_discard=lambda: on_delta(DISCARD_MARKER),
                )
            else:
                result = await provider_stream(request)
            duration_ms = result.duration_seconds * 1000 if result.duration_seconds else (time.monotonic() - started) * 1000
            result.metadata["advertised_tool_names"] = [
                tool.name for tool in tools
            ]
            result.metadata["provider_supports_tool_use"] = bool(
                getattr(provider, "SUPPORTS_TOOL_USE", False)
            )
            _annotate_tool_cost(result, tools, request_number)
            self._record_success(event_id, request, provider_name, model, scope, result, duration_ms)
            return result
        except Exception as exc:
            self._record_failure(event_id, request, provider_name, model, scope, started, exc)
            raise


def _request_context_diagnostics(request: ExecutionRequest, tools: list) -> dict:
    system_chars = len(request.instructions or "") + len(request.shared_instructions or "") + len(request.wave_instructions or "")
    user_chars = len(request.user_message or "")
    current_message_chars = len((request.user_message or "").rsplit("\n\nuser: ", 1)[-1])
    conversation_chars = max(0, user_chars - current_message_chars)
    tool_context_chars = 0
    for exchange in request.tool_exchanges or []:
        tool_context_chars += len(exchange.assistant_text or "")
        for result in exchange.results:
            tool_context_chars += len(result.content or "")
    try:
        schema_chars = len(json.dumps([{"name": t.name, "description": t.description, "parameters": t.parameters} for t in tools], ensure_ascii=False)) if tools else 0
    except (TypeError, ValueError):
        schema_chars = 0
    total_chars = system_chars + user_chars + schema_chars
    return {
        "system_chars": system_chars,
        "conversation_chars": conversation_chars,
        "current_message_chars": current_message_chars,
        "tool_schema_chars": schema_chars,
        "tool_context_chars": tool_context_chars,
        "total_estimated_chars": total_chars,
        "estimated_input_tokens": round(total_chars / 4),
        "tools_available": len(tools),
        "tool_round_trips": len(request.tool_exchanges or []),
    }


def _append_request_diagnostic(result: ExecutionResult, request_number: int, diagnostics: dict) -> None:
    metadata = result.metadata
    history = list(metadata.get("request_context_diagnostics") or [])
    history.append({"request": request_number, **diagnostics, "actual_input_tokens": result.input_tokens})
    metadata["request_context_diagnostics"] = history


def _annotate_tool_cost(result, tools: list, requests_made: int) -> None:
    metadata = getattr(result, "metadata", None)
    if metadata is None:
        return
    try:
        schema_bytes = len(json.dumps([{"name": t.name, "description": t.description, "parameters": t.parameters} for t in tools], ensure_ascii=False)) if tools else 0
    except (TypeError, ValueError):
        schema_bytes = None
    metadata["tools_available"] = len(tools)
    metadata["tool_schema_bytes"] = schema_bytes
    metadata["llm_followups"] = max(0, requests_made - 1)

