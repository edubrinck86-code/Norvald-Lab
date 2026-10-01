import json
import time
from dataclasses import replace
from typing import List, Tuple

import httpx

from norvald_lab.vendor.norvald_execution.support.http_client import build_client

from norvald_lab.vendor.norvald_execution.contracts.attachment_contracts import ATTACHMENT_KIND_IMAGE, AttachmentResult
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.contracts.prompt_prefix import system_text
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.support.stream_metrics import StreamMetrics
from norvald_lab.vendor.norvald_execution.contracts.tool_catalog_guard import sanitize_name as _safe_tool_name, valid_tools
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall

_DEFAULT_BASE_URL = "http://localhost:11434"


def _safe_json(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


class OllamaProvider(LLMProvider):
    # Família do provider. A política de amostragem depende dela.
    kind = "ollama"
    ATTACHMENT_CAPABILITIES = frozenset({ATTACHMENT_KIND_IMAGE})
    SUPPORTS_REASONING_OUTPUT = True
    SUPPORTS_TOOL_USE = True
    """Provider real — servidor Ollama local/remoto.

    Protocolo genuinamente diferente dos demais (sem autenticação por
    chave, endpoints próprios /api/chat e /api/tags), por isso não
    compartilha implementação com o provider OpenAI-compatível.

    'credential' aqui não é uma API key: é a base_url do servidor (ex:
    "http://localhost:11434"). Vazia cai no default local.

    Assíncrono, com `httpx.AsyncClient` mantido vivo pela vida útil da
    instância — conexão reaproveitada entre chamadas. Timeout mais
    generoso (modelo local pode ser bem mais lento que uma API na nuvem).
    """

    def __init__(self, credential: str):
        self._base_url = (credential or _DEFAULT_BASE_URL).rstrip("/")
        # Ollama local expõe HTTP/1.1. Não tentar negociar HTTP/2 evita
        # falhas de transporte em instalações locais sem TLS/h2c.
        self._client = build_client(timeout=600.0, http2=False)

    async def list_models(self) -> List[ModelInfo]:
        try:
            response = await self._client.get(f"{self._base_url}/api/tags", timeout=30.0)
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama retornou {exc.response.status_code} ao listar modelos: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao listar modelos do Ollama ({self._base_url}): {type(exc).__name__}: {exc!s}") from exc

        models = []
        for m in raw.get("models", []):
            details = m.get("details", {})
            raw_metadata = {}
            if details:
                raw_metadata["ollama_details"] = details
            models.append(ModelInfo(id=m["name"], display_name=m["name"], vendor="Ollama", raw_metadata=raw_metadata))
        return models

    def _build_user_message(self, request: ExecutionRequest) -> Tuple[dict, List[AttachmentResult]]:
        message = {"role": "user", "content": request.user_message or ""}
        if not request.attachments:
            return message, []
        supported, results = self.classify_attachments(request.attachments)
        if supported:
            message["images"] = [att.data_base64 for att in supported]
            results.extend(AttachmentResult(identifier=att.identifier, filename=att.filename, mime_type=att.mime_type, status="sent") for att in supported)
        return message, results

    @staticmethod
    def _tool_messages(request: ExecutionRequest) -> list:
        messages = []
        for exchange in request.tool_exchanges:
            messages.append({
                "role": "assistant",
                "content": exchange.assistant_text or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": call.name,
                            "arguments": call.arguments,
                        }
                    }
                    for call in exchange.calls
                ],
            })
            messages.extend(
                {
                    "role": "tool",
                    "content": result.content,
                }
                for result in exchange.results
            )
        return messages

    def _tool_payload(self, request: ExecutionRequest) -> list:
        saneadas = [replace(tool, name=_safe_tool_name(tool.name)) for tool in request.tools]
        aceitos, _ = valid_tools(saneadas, provider_label="ollama")
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in aceitos
        ]

    def _build_payload(self, request: ExecutionRequest, model: str, *, stream: bool) -> Tuple[dict, List[AttachmentResult]]:
        """Corpo da requisição, igual para stream e não-stream.

        Extraído porque os dois caminhos precisam exatamente da mesma
        montagem: duplicá-la faria a amostragem ou o `think` divergirem
        entre streaming e resposta cheia sem ninguém notar.
        """
        user_message, attachment_results = self._build_user_message(request)
        payload = {
            "model": model,
            "stream": stream,
            "messages": [{"role": "system", "content": system_text(request)}, user_message],
        }
        if request.tools:
            payload["tools"] = self._tool_payload(request)
        if request.tool_exchanges:
            payload["messages"].extend(self._tool_messages(request))

        sampling = request.sampling
        if sampling:
            # Ollama recebe amostragem em `options`, não na raiz.
            options = {}
            if sampling.temperature is not None:
                options["temperature"] = sampling.temperature
            if sampling.top_p is not None:
                options["top_p"] = sampling.top_p
            if sampling.max_tokens is not None:
                options["num_predict"] = sampling.max_tokens
            if options:
                payload["options"] = options
        if request.reasoning_effort != "off":
            payload["think"] = True
        return payload, attachment_results

    @staticmethod
    def _parse_tool_calls(message: dict) -> List[ToolCall]:
        calls = []
        for call in message.get("tool_calls") or []:
            function = call.get("function") or {}
            name = function.get("name") or ""
            if not name:
                continue
            calls.append(
                ToolCall(
                    call_id=call.get("id") or f"ollama-tool-{len(calls)}",
                    name=name,
                    arguments=_safe_json(function.get("arguments")),
                )
            )
        return calls

    async def execute_stream(self, request: ExecutionRequest, model: str, on_delta, on_reasoning_delta=None) -> ExecutionResult:
        """Streaming nativo do Ollama (NDJSON, uma linha por delta).

        Além de conteúdo e reasoning, acumula tool calls fragmentadas para
        entregá-las ao `ToolLoop` no mesmo contrato usado pelos demais
        providers.
        """
        payload, attachment_results = self._build_payload(request, model, stream=True)
        started = time.monotonic()
        metrics = StreamMetrics(started=started)
        text_parts: List[str] = []
        thinking_parts: List[str] = []
        tool_calls: dict = {}
        raw_final: dict = {}

        try:
            async with self._client.stream(
                "POST", f"{self._base_url}/api/chat", json=payload,
                headers={"content-type": "application/json"},
            ) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise RuntimeError(f"Ollama retornou {response.status_code}: {response.text}")
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    message = event.get("message") or {}
                    piece = message.get("content") or ""
                    if piece:
                        metrics.record(piece)
                        text_parts.append(piece)
                        on_delta(piece)
                    thought = message.get("thinking") or ""
                    if thought:
                        thinking_parts.append(thought)
                        if on_reasoning_delta:
                            on_reasoning_delta(thought)
                    for index, call in enumerate(message.get("tool_calls") or []):
                        function = call.get("function") or {}
                        current = tool_calls.setdefault(index, {"id": "", "name": "", "arguments": {}})
                        if call.get("id"):
                            current["id"] = call["id"]
                        if function.get("name"):
                            current["name"] = function["name"]
                        arguments = function.get("arguments")
                        if isinstance(arguments, dict):
                            current["arguments"].update(arguments)
                        elif arguments:
                            current["arguments_text"] = current.get("arguments_text", "") + str(arguments)
                    if event.get("done"):
                        raw_final = event
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar o Ollama ({self._base_url}): {type(exc).__name__}: {exc!s}") from exc

        parsed_tool_calls = []
        for index, item in sorted(tool_calls.items()):
            arguments = item.get("arguments") or _safe_json(item.get("arguments_text", "{}"))
            parsed_tool_calls.append(
                ToolCall(
                    call_id=item.get("id") or f"ollama-tool-{index}",
                    name=item.get("name") or "",
                    arguments=arguments,
                )
            )
        parsed_tool_calls = [call for call in parsed_tool_calls if call.name]

        duration = time.monotonic() - started
        input_tokens = raw_final.get("prompt_eval_count", 0)
        output_tokens = raw_final.get("eval_count", 0)
        return ExecutionResult(
            content="".join(text_parts),
            tokens=input_tokens + output_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=duration,
            provider="ollama",
            model=model,
            metadata={
                "raw_usage": {
                    k: raw_final.get(k)
                    for k in ("prompt_eval_count", "eval_count", "total_duration")
                    if raw_final.get(k) is not None
                },
                "attachment_results": [r.to_dict() for r in attachment_results],
                "stream": metrics.as_dict(output_tokens or None),
            },
            reasoning="".join(thinking_parts) or None,
            tool_calls=parsed_tool_calls,
        )

    async def execute(self, request: ExecutionRequest, model: str) -> ExecutionResult:
        payload, attachment_results = self._build_payload(request, model, stream=False)
        started = time.monotonic()
        try:
            response = await self._client.post(f"{self._base_url}/api/chat", json=payload, headers={"content-type": "application/json"})
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama retornou {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar o Ollama ({self._base_url}): {type(exc).__name__}: {exc!s}") from exc

        duration = time.monotonic() - started
        message = raw.get("message", {})
        content = message.get("content", "")
        reasoning = message.get("thinking") or None
        tool_calls = self._parse_tool_calls(message)
        tokens = raw.get("prompt_eval_count", 0) + raw.get("eval_count", 0)
        return ExecutionResult(content=content, tokens=tokens, input_tokens=raw.get("prompt_eval_count", 0), output_tokens=raw.get("eval_count", 0), duration_seconds=duration, provider="ollama", model=model, metadata={"raw_usage": {k: raw.get(k) for k in ("prompt_eval_count", "eval_count", "total_duration") if raw.get(k) is not None}, "attachment_results": [r.to_dict() for r in attachment_results]}, reasoning=reasoning, tool_calls=tool_calls)

