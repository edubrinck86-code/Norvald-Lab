import time
from typing import List, Tuple

import httpx

from norvald_lab.vendor.norvald_execution.providers.stream_errors import read_stream_body
from norvald_lab.vendor.norvald_execution.support.http_client import build_client
from norvald_lab.vendor.norvald_execution.support.stream_metrics import StreamMetrics

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall
from norvald_lab.vendor.norvald_execution.contracts.tool_catalog_guard import valid_tools
from norvald_lab.vendor.norvald_execution.contracts.attachment_contracts import ATTACHMENT_KIND_DOCUMENT, ATTACHMENT_KIND_IMAGE, AttachmentResult, classify_attachment_kind
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.support.provider_errors import classify_http_error, operational_headers


class AnthropicProvider(LLMProvider):
    # Família do provider. A política de amostragem depende dela.
    kind = "anthropic"
    ATTACHMENT_CAPABILITIES = frozenset({ATTACHMENT_KIND_IMAGE, ATTACHMENT_KIND_DOCUMENT})
    SUPPORTS_REASONING_OUTPUT = True
    SUPPORTS_TOOL_USE = True
    _REASONING_BUDGET_TOKENS = {"low": 2000, "medium": 8000, "high": 16000}
    API_URL = "https://api.anthropic.com/v1/messages"
    MODELS_URL = "https://api.anthropic.com/v1/models"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str):
        # 60s: mesmo raciocínio dos outros providers remotos (gemini_provider.py,
        # openai_compatible_provider.py) — prefere falhar rápido a segurar a
        # rodada esperando congestionamento; retry já cobre lentidão transitória.
        self._api_key = api_key; self._client = build_client(timeout=60.0)

    def _headers(self) -> dict: return {"x-api-key": self._api_key, "anthropic-version": self.API_VERSION}

    async def list_models(self) -> List[ModelInfo]:
        models: List[ModelInfo] = []
        after_id: str | None = None
        try:
            for _ in range(20):
                params = {"limit": 100}
                if after_id:
                    params["after_id"] = after_id
                response = await self._client.get(
                    self.MODELS_URL,
                    headers=self._headers(),
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                raw = response.json()
                page = raw.get("data", [])
                for item in page:
                    model_id = item["id"]
                    metadata = {
                        key: value
                        for key, value in item.items()
                        if key not in {"id", "display_name", "type"} and value is not None
                    }
                    models.append(
                        ModelInfo(
                            id=model_id,
                            display_name=item.get("display_name", model_id),
                            vendor="Anthropic",
                            raw_metadata=metadata,
                        )
                    )
                if not raw.get("has_more") or not page:
                    break
                after_id = str(raw.get("last_id") or page[-1].get("id") or "").strip() or None
                if not after_id:
                    break
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind="anthropic",
                provider_label="Anthropic",
                model="",
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao listar modelos da Anthropic: {exc}") from exc
        return models

    def _build_user_content(self, request: ExecutionRequest) -> Tuple[list | str, List[AttachmentResult]]:
        text = request.user_message or ""
        if not request.attachments: return text, []
        supported, results = self.classify_attachments(request.attachments); blocks = [{"type": "text", "text": text}]
        for att in supported:
            kind = classify_attachment_kind(att.mime_type); block_type = "image" if kind == ATTACHMENT_KIND_IMAGE else "document"
            blocks.append({"type": block_type, "source": {"type": "base64", "media_type": att.mime_type, "data": att.data_base64}})
            results.append(AttachmentResult(identifier=att.identifier, filename=att.filename, mime_type=att.mime_type, status="sent"))
        return blocks, results

    @staticmethod
    def _tool_messages(request: ExecutionRequest) -> list:
        messages = []
        for exchange in request.tool_exchanges:
            # Com thinking + tool use a Anthropic exige que os blocos do turno
            # anterior voltem sem alteração, inclusive signature e blocos de
            # thinking vazios. Quando o adapter capturou a resposta nativa,
            # ela é a fonte de verdade; a reconstrução abaixo fica só como
            # compatibilidade para históricos antigos/sem provider_state.
            state = exchange.provider_state if isinstance(exchange.provider_state, dict) else {}
            preserved = state.get("anthropic_content")
            if isinstance(preserved, list) and preserved:
                assistant_blocks = preserved
            else:
                assistant_blocks = []
                if exchange.assistant_text:
                    assistant_blocks.append({"type": "text", "text": exchange.assistant_text})
                assistant_blocks.extend(
                    {"type": "tool_use", "id": call.call_id, "name": call.name, "input": call.arguments}
                    for call in exchange.calls
                )
            messages.append({"role": "assistant", "content": assistant_blocks})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": result.call_id, "content": result.content, **({"is_error": True} if result.is_error else {})}
                for result in exchange.results
            ]})
        return messages

    @staticmethod
    def _system_blocks(request: ExecutionRequest) -> list:
        """System em dois blocos, o estável primeiro.

        O cache da Anthropic é por prefixo. Enquanto `instructions`
        começava com "Você é E1... na rodada 4 de 5", o prefixo mudava a
        cada participante e a cada rodada: o cache era escrito e
        descartado todo turno, e as evidências — o volume do prompt —
        eram cobradas cheias sempre. Com o bloco compartilhado na frente,
        4 especialistas x N rodadas passam a ler o mesmo prefixo.
        """
        blocks = []
        # Dois pontos de cache, não um.
        #
        # O primeiro fecha o material estável entre rodadas; o segundo
        # fecha o Working Context, que é o mesmo para os cinco
        # especialistas da leva. Com um breakpoint só, o WC era cobrado
        # cheio em cada uma das cinco requisições.
        if request.shared_instructions:
            blocks.append({"type": "text", "text": request.shared_instructions,
                           "cache_control": {"type": "ephemeral"}})
        if request.wave_instructions:
            blocks.append({"type": "text", "text": request.wave_instructions,
                           "cache_control": {"type": "ephemeral"}})
        if not blocks:
            return [{"type": "text", "text": request.instructions, "cache_control": {"type": "ephemeral"}}]
        # A cauda do participante fica fora do cache: varia a cada turno,
        # e marcá-la invalidaria o bloco a cada requisição.
        blocks.append({"type": "text", "text": request.instructions})
        return blocks

    @staticmethod
    def _adaptive_thinking(model: str) -> bool:
        normalized = (model or "").lower()
        # Claude 4.6+ nas famílias que expõem adaptive thinking. Haiku 4.5
        # continua no modo extended thinking e rejeita type=adaptive.
        return normalized.startswith((
            "claude-opus-4-6",
            "claude-opus-4-7",
            "claude-opus-4-8",
            "claude-opus-5",
            "claude-sonnet-4-6",
            "claude-sonnet-5",
            "claude-fable-5",
            "claude-mythos-5",
            "claude-mythos-preview",
        ))

    def _build_payload(self, request: ExecutionRequest, model: str) -> Tuple[dict, List[AttachmentResult]]:
        user_content, attachment_results = self._build_user_content(request); budget = self._REASONING_BUDGET_TOKENS.get(request.reasoning_effort); adaptive = self._adaptive_thinking(model); max_tokens = 4096 + budget if budget and not adaptive else 8192 if adaptive else 4096
        sampling = request.sampling
        if sampling and sampling.max_tokens:
            max_tokens = sampling.max_tokens + (budget if budget and not adaptive else 0)
        payload = {"model": model, "max_tokens": max_tokens, "system": self._system_blocks(request), "messages": [{"role": "user", "content": user_content}]}
        # A política já garantiu que temperatura e top_p não vêm juntos
        # e que nenhum dos dois acompanha raciocínio estendido.
        if sampling:
            if sampling.temperature is not None:
                payload["temperature"] = sampling.temperature
            if sampling.top_p is not None:
                payload["top_p"] = sampling.top_p
        if request.tools:
            aceitos, _ = valid_tools(request.tools, provider_label="Anthropic")
            payload["tools"] = [{"name": tool.name, "description": tool.description, "input_schema": tool.parameters} for tool in aceitos]
        if request.tool_exchanges:
            payload["messages"].extend(self._tool_messages(request))
        if adaptive:
            normalized = (model or "").lower()
            if normalized.startswith(("claude-fable-5", "claude-mythos-5")):
                payload["thinking"] = {"display": "summarized"}
            else:
                payload["thinking"] = {"type": "adaptive", "display": "summarized"}
            payload["output_config"] = {"effort": request.reasoning_effort if request.reasoning_effort in {"low", "medium", "high"} else "medium"}
        elif budget:
            payload["thinking"] = {"type": "enabled", "budget_tokens": budget}
        return payload, attachment_results

    async def execute(self, request: ExecutionRequest, model: str) -> ExecutionResult:
        payload, attachment_results = self._build_payload(request, model); started = time.monotonic()
        try:
            response = await self._client.post(self.API_URL, json=payload, headers={"content-type": "application/json", **self._headers()}); response.raise_for_status(); raw = response.json()
        except httpx.HTTPStatusError as exc:
            detalhe = await read_stream_body(exc.response)
            raise classify_http_error(
                provider_kind="anthropic",
                provider_label="Anthropic",
                model=model,
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=detalhe,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar a Anthropic API: {exc}") from exc
        text_blocks = [block.get("text", "") for block in raw.get("content", []) if block.get("type") == "text"]; thinking_blocks = [block.get("thinking", "") for block in raw.get("content", []) if block.get("type") == "thinking"]
        tool_calls = [ToolCall(call_id=block.get("id", ""), name=block.get("name", ""), arguments=block.get("input") or {}) for block in raw.get("content", []) if block.get("type") == "tool_use"]
        usage = raw.get("usage", {}); input_tokens = usage.get("input_tokens", 0); output_tokens = usage.get("output_tokens", 0)
        return ExecutionResult(content="\n".join(text_blocks), tokens=input_tokens + output_tokens, input_tokens=input_tokens, output_tokens=output_tokens, duration_seconds=time.monotonic() - started, provider="anthropic", model=model, metadata={"raw_usage": dict(usage), "request_id": raw.get("id"), "provider_operational": {"headers": operational_headers(response.headers)}, "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0), "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0), "attachment_results": [r.to_dict() for r in attachment_results], "provider_state": {"anthropic_content": raw.get("content", [])}}, reasoning="\n".join(t for t in thinking_blocks if t) or None, tool_calls=tool_calls)

    async def execute_stream(self, request: ExecutionRequest, model: str, on_delta, on_reasoning_delta=None) -> ExecutionResult:
        import json as _json

        payload, attachment_results = self._build_payload(request, model)
        payload["stream"] = True
        started = time.monotonic()
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        blocks: dict[int, dict] = {}
        partial_tool_json: dict[int, str] = {}
        input_tokens = output_tokens = 0
        cache_creation_input_tokens = cache_read_input_tokens = 0
        metrics = StreamMetrics(started=started)
        response_operational: dict = {}

        def finalize_tool_block(index: int) -> None:
            block = blocks.get(index)
            if not block or block.get("type") != "tool_use":
                return
            raw_input = partial_tool_json.get(index, "")
            if not raw_input.strip():
                block["input"] = block.get("input") or {}
                return
            try:
                parsed = _json.loads(raw_input)
                block["input"] = parsed if isinstance(parsed, dict) else {}
            except (TypeError, ValueError):
                block["input"] = block.get("input") or {}

        try:
            async with self._client.stream(
                "POST",
                self.API_URL,
                json=payload,
                headers={"content-type": "application/json", **self._headers(), "accept": "text/event-stream"},
            ) as response:
                response_operational = {"headers": operational_headers(response.headers)}
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    detalhe = await read_stream_body(response)
                    raise classify_http_error(
                        provider_kind="anthropic",
                        provider_label="Anthropic",
                        model=model,
                        status_code=response.status_code,
                        headers=response.headers,
                        body=detalhe,
                    ) from exc

                event_name = None
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        event_name = line[len("event:"):].strip()
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = _json.loads(line[len("data:"):].strip())

                    if event_name == "message_start":
                        usage = data.get("message", {}).get("usage", {})
                        input_tokens = usage.get("input_tokens", input_tokens)
                        cache_creation_input_tokens = usage.get("cache_creation_input_tokens", 0)
                        cache_read_input_tokens = usage.get("cache_read_input_tokens", 0)
                        continue

                    if event_name == "content_block_start":
                        index = int(data.get("index", len(blocks)))
                        block = dict(data.get("content_block") or {})
                        blocks[index] = block
                        if block.get("type") == "tool_use":
                            partial_tool_json[index] = ""
                        elif block.get("type") == "text":
                            piece = block.get("text", "") or ""
                            if piece:
                                metrics.record(piece)
                                text_parts.append(piece)
                                on_delta(piece)
                        elif block.get("type") == "thinking":
                            piece = block.get("thinking", "") or ""
                            if piece:
                                thinking_parts.append(piece)
                                if on_reasoning_delta:
                                    on_reasoning_delta(piece)
                        continue

                    if event_name == "content_block_delta":
                        index = int(data.get("index", 0))
                        delta = data.get("delta", {}) or {}
                        delta_type = delta.get("type")
                        block = blocks.setdefault(index, {})

                        if delta_type == "text_delta":
                            piece = delta.get("text", "") or ""
                            if piece:
                                block["type"] = block.get("type") or "text"
                                block["text"] = (block.get("text") or "") + piece
                                metrics.record(piece)
                                text_parts.append(piece)
                                on_delta(piece)
                        elif delta_type == "thinking_delta":
                            piece = delta.get("thinking", "") or ""
                            if piece:
                                block["type"] = block.get("type") or "thinking"
                                block["thinking"] = (block.get("thinking") or "") + piece
                                thinking_parts.append(piece)
                                if on_reasoning_delta:
                                    on_reasoning_delta(piece)
                        elif delta_type == "signature_delta":
                            piece = delta.get("signature", "") or ""
                            if piece:
                                block["signature"] = (block.get("signature") or "") + piece
                        elif delta_type == "input_json_delta":
                            partial_tool_json[index] = partial_tool_json.get(index, "") + (delta.get("partial_json", "") or "")
                        continue

                    if event_name == "content_block_stop":
                        finalize_tool_block(int(data.get("index", 0)))
                        continue

                    if event_name == "message_delta":
                        usage = data.get("usage", {}) or {}
                        output_tokens = usage.get("output_tokens", output_tokens)

        except RuntimeError:
            raise
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar a Anthropic API (stream): {exc}") from exc

        for index in list(partial_tool_json):
            finalize_tool_block(index)

        assistant_blocks = [blocks[index] for index in sorted(blocks)]
        tool_calls = [
            ToolCall(
                call_id=str(block.get("id") or ""),
                name=str(block.get("name") or ""),
                arguments=block.get("input") if isinstance(block.get("input"), dict) else {},
            )
            for block in assistant_blocks
            if block.get("type") == "tool_use" and block.get("name")
        ]

        return ExecutionResult(
            content="".join(text_parts),
            tokens=input_tokens + output_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=time.monotonic() - started,
            provider="anthropic",
            model=model,
            metadata={
                "raw_usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_creation_input_tokens": cache_creation_input_tokens,
                    "cache_read_input_tokens": cache_read_input_tokens,
                },
                **metrics.as_dict(output_tokens),
                "cache_creation_input_tokens": cache_creation_input_tokens,
                "cache_read_input_tokens": cache_read_input_tokens,
                "provider_operational": response_operational,
                "attachment_results": [r.to_dict() for r in attachment_results],
                "provider_state": {"anthropic_content": assistant_blocks},
            },
            reasoning="".join(thinking_parts) or None,
            tool_calls=tool_calls,
        )


