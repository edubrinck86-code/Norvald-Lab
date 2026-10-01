import time
import urllib.parse
from typing import List, Tuple

import httpx

from norvald_lab.vendor.norvald_execution.providers.stream_errors import read_stream_body
from norvald_lab.vendor.norvald_execution.support.http_client import build_client
from norvald_lab.vendor.norvald_execution.support.stream_metrics import StreamMetrics

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall
from norvald_lab.vendor.norvald_execution.contracts.tool_catalog_guard import prune_schema, valid_tools
from norvald_lab.vendor.norvald_execution.contracts.attachment_contracts import ATTACHMENT_KIND_DOCUMENT, ATTACHMENT_KIND_IMAGE, AttachmentResult
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.contracts.prompt_prefix import _system_parts
from norvald_lab.vendor.norvald_execution.support.provider_errors import classify_http_error, operational_headers

#: O Gemini aceita um subconjunto do OpenAPI, não JSON Schema completo.
_GEMINI_ALLOWED_KEYS = {
    "type", "format", "description", "nullable", "enum",
    "items", "properties", "required", "example",
    "anyOf", "minimum", "maximum", "minItems", "maxItems",
}


def _gemini_schema(schema):
    return prune_schema(schema, _GEMINI_ALLOWED_KEYS)


def _normalize_model_name(model: str) -> str:
    """Aceita tanto o id cru quanto o nome REST ``models/<id>``.

    A listagem do Gemini devolve ``models/<id>``, enquanto o Studio normalmente
    persiste apenas o id. Normalizar aqui torna o adapter tolerante aos dois
    formatos e evita montar ``/models/models/...``.
    """
    normalized = (model or "").strip()
    if normalized.startswith("models/"):
        normalized = normalized[len("models/"):]
    return normalized


class GeminiProvider(LLMProvider):
    kind = "gemini"
    ATTACHMENT_CAPABILITIES = frozenset({ATTACHMENT_KIND_IMAGE, ATTACHMENT_KIND_DOCUMENT})
    SUPPORTS_REASONING_OUTPUT = True
    SUPPORTS_TOOL_USE = True
    _REASONING_BUDGET_TOKENS = {"low": 2000, "medium": 8000, "high": 16000}
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str):
        self._api_key = api_key
        # 60s, não 120s: prefere falhar rápido a segurar a rodada inteira
        # esperando um provider congestionado. Provider gratuito/lento
        # demais é sinal de trocar de modelo, não de esperar mais — os
        # dois níveis de retry (with_retry, provider_gate) já cobrem
        # lentidão transitória; isto só limita o pior caso por chamada.
        self._client = build_client(timeout=60.0)

    def _url(self, path: str) -> str:
        separator = "&" if "?" in path else "?"
        return f"{self.BASE_URL}{path}{separator}key={urllib.parse.quote(self._api_key)}"

    async def list_models(self) -> List[ModelInfo]:
        models: List[ModelInfo] = []
        page_token = ""
        try:
            for _ in range(20):
                path = "/models?pageSize=100"
                if page_token:
                    path += "&pageToken=" + urllib.parse.quote(page_token)
                response = await self._client.get(self._url(path), timeout=30.0)
                response.raise_for_status()
                raw = response.json()
                for item in raw.get("models", []):
                    full_name = item.get("name", "")
                    model_id = full_name.split("/", 1)[1] if "/" in full_name else full_name
                    metadata = {
                        key: value
                        for key, value in item.items()
                        if key not in {"name", "displayName"} and value is not None
                    }
                    models.append(
                        ModelInfo(
                            id=model_id,
                            display_name=item.get("displayName", model_id),
                            vendor="Google",
                            raw_metadata=metadata,
                        )
                    )
                page_token = str(raw.get("nextPageToken") or "")
                if not page_token:
                    break
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind="gemini",
                provider_label="Gemini",
                model="",
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao listar modelos do Gemini: {exc}") from exc
        return models

    @staticmethod
    def _tool_contents(request: ExecutionRequest) -> list:
        contents = []
        for exchange in request.tool_exchanges:
            model_parts = []
            if exchange.assistant_text: model_parts.append({"text": exchange.assistant_text})
            for call in exchange.calls:
                part = {"functionCall": {"name": call.name, "args": call.arguments}}
                if call.thought_signature: part["thoughtSignature"] = call.thought_signature
                model_parts.append(part)
            contents.append({"role": "model", "parts": model_parts})
            contents.append({"role": "user", "parts": [{"functionResponse": {"name": result.name, "response": {"content": result.content}}} for result in exchange.results]})
        return contents

    def _build_user_parts(self, request: ExecutionRequest) -> Tuple[list, List[AttachmentResult]]:
        parts = [{"text": request.user_message or ""}]
        if not request.attachments: return parts, []
        supported, results = self.classify_attachments(request.attachments)
        for att in supported:
            parts.append({"inline_data": {"mime_type": att.mime_type, "data": att.data_base64}})
            results.append(AttachmentResult(identifier=att.identifier, filename=att.filename, mime_type=att.mime_type, status="sent"))
        return parts, results

    def _build_payload(self, request: ExecutionRequest) -> tuple:
        user_parts, attachment_results = self._build_user_parts(request)
        payload = {"contents": [{"role": "user", "parts": user_parts}], "systemInstruction": {"parts": _system_parts(request)}}
        generation_config: dict = {}
        sampling = request.sampling
        if sampling:
            if sampling.temperature is not None:
                generation_config["temperature"] = sampling.temperature
            if sampling.top_p is not None:
                generation_config["topP"] = sampling.top_p
            if sampling.max_tokens is not None:
                generation_config["maxOutputTokens"] = sampling.max_tokens
        if request.tools:
            aceitos, _ = valid_tools(request.tools, provider_label="Gemini")
            if aceitos:
                payload["tools"] = [{"functionDeclarations": [{"name": tool.name, "description": tool.description, "parameters": _gemini_schema(tool.parameters)} for tool in aceitos]}]
        if request.tool_exchanges:
            payload["contents"].extend(self._tool_contents(request))
        budget = self._REASONING_BUDGET_TOKENS.get(request.reasoning_effort)
        if budget:
            generation_config["thinkingConfig"] = {"thinkingBudget": budget, "includeThoughts": True}
        if generation_config:
            payload["generationConfig"] = generation_config
        return payload, attachment_results

    @staticmethod
    def _parse_parts(parts: list) -> tuple:
        content = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        reasoning = "".join(p.get("text", "") for p in parts if p.get("thought"))
        tool_calls = [ToolCall(call_id=p["functionCall"].get("name", ""), name=p["functionCall"].get("name", ""), arguments=p["functionCall"].get("args") or {}, thought_signature=p.get("thoughtSignature")) for p in parts if p.get("functionCall")]
        return content, reasoning, tool_calls

    async def execute(self, request: ExecutionRequest, model: str) -> ExecutionResult:
        model = _normalize_model_name(model)
        payload, attachment_results = self._build_payload(request)
        started = time.monotonic()
        try:
            response = await self._client.post(self._url(f"/models/{model}:generateContent"), json=payload, headers={"content-type": "application/json"})
            response.raise_for_status(); raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind="gemini",
                provider_label="Gemini",
                model=model,
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar o Gemini: {exc}") from exc
        duration = time.monotonic() - started
        candidates = raw.get("candidates", []); parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        content = "".join(p.get("text", "") for p in parts if not p.get("thought")); reasoning = "".join(p.get("text", "") for p in parts if p.get("thought")) or None
        tool_calls = [ToolCall(call_id=p["functionCall"].get("name", ""), name=p["functionCall"].get("name", ""), arguments=p["functionCall"].get("args") or {}, thought_signature=p.get("thoughtSignature")) for p in parts if p.get("functionCall")]
        usage = raw.get("usageMetadata", {}); tokens = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)
        return ExecutionResult(content=content, tokens=tokens, input_tokens=usage.get("promptTokenCount", 0), output_tokens=usage.get("candidatesTokenCount", 0), duration_seconds=duration, provider="gemini", model=model, metadata={"raw_usage": dict(usage), "provider_operational": {"headers": operational_headers(response.headers)}, "attachment_results": [r.to_dict() for r in attachment_results]}, reasoning=reasoning, tool_calls=tool_calls)

    async def execute_stream(self, request: ExecutionRequest, model: str, on_delta, on_reasoning_delta=None) -> ExecutionResult:
        import json as _json

        model = _normalize_model_name(model)
        payload, attachment_results = self._build_payload(request)
        started = time.monotonic()
        metrics = StreamMetrics(started=started)
        text_parts: list = []
        thought_parts: list = []
        tool_calls: list = []
        usage: dict = {}
        response_operational: dict = {}

        try:
            async with self._client.stream(
                "POST",
                self._url(f"/models/{model}:streamGenerateContent") + "&alt=sse",
                json=payload,
                headers={"content-type": "application/json"},
            ) as response:
                response_operational = {"headers": operational_headers(response.headers)}
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw_data = line[len("data:"):].strip()
                    if not raw_data:
                        continue
                    data = _json.loads(raw_data)
                    if data.get("usageMetadata"):
                        usage = data["usageMetadata"]
                    candidates = data.get("candidates") or []
                    if not candidates:
                        continue
                    for part in candidates[0].get("content", {}).get("parts", []) or []:
                        if part.get("functionCall"):
                            tool_calls.append(ToolCall(call_id=part["functionCall"].get("name", ""), name=part["functionCall"].get("name", ""), arguments=part["functionCall"].get("args") or {}, thought_signature=part.get("thoughtSignature")))
                            continue
                        piece = part.get("text") or ""
                        if not piece:
                            continue
                        if part.get("thought"):
                            thought_parts.append(piece)
                            if on_reasoning_delta:
                                on_reasoning_delta(piece)
                            continue
                        metrics.record(piece)
                        text_parts.append(piece)
                        on_delta(piece)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                # Alguns modelos/versões da API podem aceitar generateContent
                # mas não expor streamGenerateContent.
                try:
                    return await self.execute(request, model)
                except Exception as fallback_exc:
                    raise RuntimeError(
                        f"Gemini API retornou 404 durante streaming e o fallback "
                        f"generateContent também falhou: {fallback_exc}. "
                        f"Resposta do streaming: {await read_stream_body(exc.response)}"
                    ) from fallback_exc

            detalhe = await read_stream_body(exc.response)
            raise classify_http_error(
                provider_kind="gemini",
                provider_label="Gemini",
                model=model,
                status_code=status,
                headers=exc.response.headers,
                body=detalhe,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar o Gemini: {exc}") from exc

        duration = time.monotonic() - started
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        return ExecutionResult(content="".join(text_parts), tokens=input_tokens + output_tokens, input_tokens=input_tokens, output_tokens=output_tokens, duration_seconds=duration, provider="gemini", model=model, metadata={"raw_usage": dict(usage), **metrics.as_dict(output_tokens), "provider_operational": response_operational, "attachment_results": [r.to_dict() for r in attachment_results]}, reasoning="".join(thought_parts) or None, tool_calls=tool_calls)

