import json
import time
from dataclasses import replace
from typing import List, Optional, Tuple
from urllib.parse import quote, urlsplit

import httpx

from norvald_lab.vendor.norvald_execution.providers.stream_errors import read_stream_body
from norvald_lab.vendor.norvald_execution.contracts.attachment_contracts import (
    ATTACHMENT_KIND_IMAGE,
    AttachmentResult,
)
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.support.http_client import build_client
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.contracts.provider_model_profiles import canonical_provider_kind
from norvald_lab.vendor.norvald_execution.support.provider_errors import classify_http_error, operational_headers
from norvald_lab.vendor.norvald_execution.contracts.prompt_prefix import system_text
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.support.stream_metrics import StreamMetrics
from norvald_lab.vendor.norvald_execution.contracts.tool_catalog_guard import sanitize_name as _safe_tool_name, valid_tools
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall


def _content_text(value) -> tuple[str, str]:
    """Separa resposta final e reasoning em formatos OpenAI-compatible.

    Mistral usa chunks estruturados quando reasoning está ativo; outros
    providers normalmente devolvem string + reasoning_content separado.
    """
    if isinstance(value, str):
        return value, ""
    if not isinstance(value, list):
        return "", ""

    text_parts: list[str] = []
    reasoning_parts: list[str] = []
    for item in value:
        if isinstance(item, str):
            text_parts.append(item)
            continue
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "").lower()
        if item_type in {"text", "output_text"}:
            text = item.get("text")
            if isinstance(text, str):
                text_parts.append(text)
            continue
        if item_type in {"thinking", "reasoning"}:
            thinking = item.get("thinking") or item.get("reasoning") or item.get("content")
            if isinstance(thinking, str):
                reasoning_parts.append(thinking)
            elif isinstance(thinking, list):
                for inner in thinking:
                    if isinstance(inner, str):
                        reasoning_parts.append(inner)
                    elif isinstance(inner, dict) and isinstance(inner.get("text"), str):
                        reasoning_parts.append(inner["text"])
    return "".join(text_parts), "".join(reasoning_parts)


def _safe_json(raw) -> dict:
    try:
        parsed = json.loads(raw or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


class OpenAICompatibleProvider(LLMProvider):
    kind = "openai"
    ATTACHMENT_CAPABILITIES = frozenset({ATTACHMENT_KIND_IMAGE})
    _REASONING_EFFORT_MAP = {"low": "low", "medium": "medium", "high": "high"}

    def __init__(self, base_url: str, api_key: str, provider_label: str = "openai-compatible", auth_check_path: str | None = None):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._label = provider_label
        self._catalog_kind = canonical_provider_kind(provider_label)
        self._auth_check_path = auth_check_path
        # 60s, não 120s: prefere falhar rápido a segurar a rodada inteira
        # esperando um provider congestionado — este é o adaptador usado
        # pelo OpenRouter, onde modelos gratuitos/experimentais sofrem
        # fila de capacidade compartilhada nos horários de pico. Provider
        # lento demais é sinal de trocar de modelo, não de esperar mais —
        # os dois níveis de retry (with_retry, provider_gate) já cobrem
        # lentidão transitória; isto só limita o pior caso por chamada.
        self._client = build_client(timeout=60.0)
        self.SUPPORTS_REASONING_OUTPUT = provider_label == "openrouter"
        self.SUPPORTS_TOOL_USE = True

    def _headers(self) -> dict:
        return {"content-type": "application/json", "authorization": f"Bearer {self._api_key}"}

    async def test_connection(self) -> bool:
        if not self._auth_check_path:
            return await super().test_connection()
        try:
            response = await self._client.get(f"{self._base_url}{self._auth_check_path}", headers=self._headers(), timeout=30.0)
            if response.status_code in (401, 403):
                return False
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                return False
            raise classify_http_error(
                provider_kind=self._catalog_kind,
                provider_label=self._label,
                model="",
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao validar credencial ({self._label}): {exc}") from exc

    async def account_intelligence(self) -> dict:
        if self._catalog_kind == "openrouter":
            try:
                response = await self._client.get(
                    f"{self._base_url}/key",
                    headers=self._headers(),
                    timeout=20.0,
                )
                response.raise_for_status()
                raw = response.json()
                data = raw.get("data") if isinstance(raw, dict) else {}
                data = data if isinstance(data, dict) else {}
                return {
                    "source": "provider_api",
                    "kind": "openrouter_key",
                    "is_free_tier": data.get("is_free_tier"),
                    "is_management_key": data.get("is_management_key"),
                    "is_provisioning_key": data.get("is_provisioning_key"),
                    "label": data.get("label"),
                    "limit": data.get("limit"),
                    "limit_remaining": data.get("limit_remaining"),
                    "limit_reset": data.get("limit_reset"),
                    "usage": data.get("usage"),
                    "usage_daily": data.get("usage_daily"),
                    "usage_weekly": data.get("usage_weekly"),
                    "usage_monthly": data.get("usage_monthly"),
                    "byok_usage": data.get("byok_usage"),
                    "byok_usage_daily": data.get("byok_usage_daily"),
                    "byok_usage_weekly": data.get("byok_usage_weekly"),
                    "byok_usage_monthly": data.get("byok_usage_monthly"),
                    "include_byok_in_limit": data.get("include_byok_in_limit"),
                    "expires_at": data.get("expires_at"),
                    "operational_headers": operational_headers(response.headers),
                }
            except httpx.HTTPStatusError as exc:
                raise classify_http_error(
                    provider_kind=self._catalog_kind,
                    provider_label=self._label,
                    model="",
                    status_code=exc.response.status_code,
                    headers=exc.response.headers,
                    body=exc.response.text,
                ) from exc

        if self._catalog_kind == "cohere":
            parsed = urlsplit(self._base_url)
            if parsed.hostname in {"api.cohere.ai", "api.cohere.com"}:
                try:
                    response = await self._client.post(
                        f"{parsed.scheme}://{parsed.netloc}/v1/check-api-key",
                        headers=self._headers(),
                        timeout=20.0,
                    )
                    response.raise_for_status()
                    raw = response.json()
                    return {
                        "source": "provider_api",
                        "kind": "cohere_key",
                        "valid": bool(raw.get("valid")),
                        "organization_id": raw.get("organization_id"),
                        "owner_id": raw.get("owner_id"),
                        "operational_headers": operational_headers(response.headers),
                    }
                except httpx.HTTPStatusError as exc:
                    raise classify_http_error(
                        provider_kind=self._catalog_kind,
                        provider_label=self._label,
                        model="",
                        status_code=exc.response.status_code,
                        headers=exc.response.headers,
                        body=exc.response.text,
                    ) from exc
        return {}

    async def model_intelligence(self, model: str) -> dict:
        if self._catalog_kind != "openrouter" or "/" not in (model or ""):
            return {}
        author, slug = model.split("/", 1)
        try:
            response = await self._client.get(
                f"{self._base_url}/models/{quote(author, safe='')}/{quote(slug, safe='')}/endpoints",
                headers=self._headers(),
                timeout=20.0,
            )
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind=self._catalog_kind,
                provider_label=self._label,
                model=model,
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc

        data = raw.get("data") if isinstance(raw, dict) else {}
        data = data if isinstance(data, dict) else {}
        endpoints = data.get("endpoints")
        endpoints = endpoints if isinstance(endpoints, list) else []

        normalized_endpoints = []
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            pricing = endpoint.get("pricing")
            pricing = pricing if isinstance(pricing, dict) else {}
            prompt_price = pricing.get("prompt")
            completion_price = pricing.get("completion")
            try:
                is_free = float(prompt_price or 0) == 0 and float(completion_price or 0) == 0
            except (TypeError, ValueError):
                is_free = False
            normalized_endpoints.append({
                "name": endpoint.get("name"),
                "provider_name": endpoint.get("provider_name"),
                "tag": endpoint.get("tag"),
                "status": endpoint.get("status"),
                "context_length": endpoint.get("context_length"),
                "max_prompt_tokens": endpoint.get("max_prompt_tokens"),
                "max_completion_tokens": endpoint.get("max_completion_tokens"),
                "supported_parameters": endpoint.get("supported_parameters") or [],
                "quantization": endpoint.get("quantization"),
                "supports_implicit_caching": endpoint.get("supports_implicit_caching"),
                "uptime_last_5m": endpoint.get("uptime_last_5m"),
                "uptime_last_30m": endpoint.get("uptime_last_30m"),
                "uptime_last_1d": endpoint.get("uptime_last_1d"),
                "latency_last_30m": endpoint.get("latency_last_30m"),
                "throughput_last_30m": endpoint.get("throughput_last_30m"),
                "pricing": pricing,
                "is_free": is_free,
            })

        def _best(field: str):
            values = [
                float(item[field])
                for item in normalized_endpoints
                if isinstance(item.get(field), (int, float))
            ]
            return max(values) if values else None

        uptime_5m = _best("uptime_last_5m")
        uptime_30m = _best("uptime_last_30m")
        uptime_1d = _best("uptime_last_1d")
        if not normalized_endpoints:
            state, reason = "unavailable", "OpenRouter não retornou endpoints para este modelo."
        elif uptime_5m is None:
            state, reason = "unknown", "OpenRouter retornou endpoints, mas sem uptime recente."
        elif uptime_5m >= 95:
            state, reason = "available", f"Melhor endpoint com {uptime_5m:.1f}% de uptime nos últimos 5 min."
        elif uptime_5m > 0:
            state, reason = "degraded", f"Melhor endpoint com apenas {uptime_5m:.1f}% de uptime nos últimos 5 min."
        else:
            state, reason = "unavailable", "Nenhum endpoint reportou uptime nos últimos 5 min."

        def _supports(item: dict, *names: str) -> bool:
            supported = {str(value).lower() for value in (item.get("supported_parameters") or [])}
            return any(name in supported for name in names)

        free_endpoints = [item for item in normalized_endpoints if item.get("is_free")]
        tool_endpoints = [item for item in normalized_endpoints if _supports(item, "tools", "tool_choice")]
        reasoning_endpoints = [item for item in normalized_endpoints if _supports(item, "reasoning", "reasoning_effort")]
        structured_endpoints = [
            item for item in normalized_endpoints
            if _supports(item, "response_format", "structured_outputs", "structured_output")
        ]

        return {
            "source": "provider_api",
            "kind": "openrouter_endpoints",
            "availability": {"state": state, "reason": reason},
            "endpoint_count": len(normalized_endpoints),
            "free_endpoint_count": len(free_endpoints),
            "tool_endpoint_count": len(tool_endpoints),
            "free_tool_endpoint_count": sum(1 for item in free_endpoints if item in tool_endpoints),
            "reasoning_endpoint_count": len(reasoning_endpoints),
            "structured_endpoint_count": len(structured_endpoints),
            "best_uptime_5m": uptime_5m,
            "best_uptime_30m": uptime_30m,
            "best_uptime_1d": uptime_1d,
            "architecture": data.get("architecture"),
            "description": data.get("description"),
            "endpoints": normalized_endpoints,
            "operational_headers": operational_headers(response.headers),
        }

    async def generation_intelligence(self, generation_id: str) -> dict:
        if self._catalog_kind != "openrouter" or not generation_id:
            return {}
        try:
            response = await self._client.get(
                f"{self._base_url}/generation",
                params={"id": generation_id},
                headers=self._headers(),
                timeout=20.0,
            )
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind=self._catalog_kind,
                provider_label=self._label,
                model="",
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        data = raw.get("data") if isinstance(raw, dict) else {}
        data = data if isinstance(data, dict) else {}
        keep = {
            "id", "model", "provider_name", "upstream_id", "service_tier",
            "router", "latency", "generation_time", "finish_reason",
            "native_finish_reason", "tokens_prompt", "tokens_completion",
            "native_tokens_prompt", "native_tokens_completion",
            "native_tokens_reasoning", "native_tokens_cached", "total_cost",
            "upstream_inference_cost", "is_byok", "data_region", "streamed",
            "provider_responses", "created_at", "request_id",
        }
        return {
            "source": "provider_api",
            "kind": "openrouter_generation",
            **{key: value for key, value in data.items() if key in keep},
        }

    async def _list_cohere_models(self) -> List[ModelInfo]:
        """Usa o catálogo nativo, que é muito mais rico que /compatibility/v1/models.

        Só fazemos o salto para o catálogo nativo quando a conexão aponta para
        o host oficial. Vaults/custom endpoints continuam no caminho genérico,
        porque não é seguro assumir que compartilham o catálogo global.
        """
        parsed = urlsplit(self._base_url)
        if parsed.hostname not in {"api.cohere.ai", "api.cohere.com"}:
            return []

        catalog_url = f"{parsed.scheme}://{parsed.netloc}/v1/models"
        models: List[ModelInfo] = []
        page_token = ""
        for _ in range(20):
            params = {"page_size": 1000}
            if page_token:
                params["page_token"] = page_token
            response = await self._client.get(
                catalog_url,
                headers=self._headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            raw = response.json()
            for item in raw.get("models", []) or []:
                model_id = str(item.get("name") or "").strip()
                if not model_id:
                    continue
                metadata = {
                    key: value
                    for key, value in item.items()
                    if key != "name" and value is not None
                }
                models.append(
                    ModelInfo(
                        id=model_id,
                        display_name=model_id,
                        vendor="cohere",
                        raw_metadata=metadata,
                    )
                )
            page_token = str(raw.get("next_page_token") or "").strip()
            if not page_token:
                break
        return models

    async def list_models(self) -> List[ModelInfo]:
        if self._catalog_kind == "cohere":
            try:
                native = await self._list_cohere_models()
                if native:
                    return native
            except httpx.HTTPStatusError as exc:
                # 401/403 no catálogo nativo são validação real da chave;
                # outros erros podem cair no endpoint compatível.
                if exc.response.status_code in (401, 403):
                    raise RuntimeError(
                        f"Cohere retornou {exc.response.status_code} ao listar modelos: {exc.response.text}"
                    ) from exc
            except httpx.HTTPError:
                pass

        catalog_path = "/language-models" if self._catalog_kind == "xai" else "/models"
        try:
            response = await self._client.get(f"{self._base_url}{catalog_path}", headers=self._headers(), timeout=30.0)
            if self._catalog_kind == "xai" and response.status_code == 404:
                response = await self._client.get(f"{self._base_url}/models", headers=self._headers(), timeout=30.0)
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind=self._catalog_kind,
                provider_label=self._label,
                model="",
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao listar modelos ({self._label}): {exc}") from exc
        models = []
        # O padrão OpenAI de /v1/models só garante id/object/created/
        # owned_by — qualquer campo a mais (context_length, capabilities,
        # max_context_length, pricing, architecture...) é extensão
        # própria de cada provider, sem nome padronizado entre eles.
        # Captura genérica: guarda TUDO que vier a mais, não uma lista
        # fixa de nomes já conhecidos — um provider novo nunca perde
        # dado por eu não ter previsto o nome do campo. Só não vira
        # capability/context_window reconhecido até alguém ensinar o
        # significado daquele campo específico em model_taxonomy.py —
        # isso a captura genérica sozinha não resolve, porque não existe
        # padrão a adivinhar (Eduardo, 2026-09-14).
        _BASELINE_MODEL_FIELDS = {"id", "object"}
        catalog_items = raw.get("models", []) if self._catalog_kind == "xai" and isinstance(raw.get("models"), list) else raw.get("data", [])
        for m in catalog_items:
            model_id = m["id"]
            raw_metadata = {
                key: value
                for key, value in m.items()
                if key not in _BASELINE_MODEL_FIELDS
                and key != "name"
                and value is not None
                and (not isinstance(value, dict) or value)
            }
            models.append(ModelInfo(id=model_id, display_name=m.get("name", model_id), vendor=model_id.split("/", 1)[0] if "/" in model_id else self._label, raw_metadata=raw_metadata))
        return models

    def _build_user_content(self, request: ExecutionRequest) -> Tuple[object, List[AttachmentResult]]:
        text = request.user_message or ""
        if not request.attachments:
            return text, []
        supported, results = self.classify_attachments(request.attachments)
        parts: list = [{"type": "text", "text": text}]
        for att in supported:
            parts.append({"type": "image_url", "image_url": {"url": f"data:{att.mime_type};base64,{att.data_base64}"}})
            results.append(AttachmentResult(identifier=att.identifier, filename=att.filename, mime_type=att.mime_type, status="sent"))
        return parts, results

    @staticmethod
    def _effort(request: ExecutionRequest) -> str:
        return str(getattr(request, "reasoning_effort", "off") or "off").strip().lower()

    def _apply_reasoning(self, payload: dict, request: ExecutionRequest, model: str) -> None:
        """Traduz o controle canônico para o contrato de cada provider.

        A UI pode exibir a mesma intenção, mas o wire format não é comum:
        OpenRouter usa `reasoning: {effort}`, Mistral usa
        `reasoning_effort`, Cohere Compatibility reduz a none/high e
        Z.AI separa thinking on/off de reasoning_effort.
        """
        effort = self._effort(request)
        # "default" (11/11/2026, coleta do Δ_herd): não mandar nenhum campo de
        # raciocínio, para que cada provider use o próprio padrão (TESE-002 §3).
        # Motivo: "off" não é uniforme — no OpenRouter não envia nada, mas no
        # Mistral e no Cohere vira "none" e desliga o raciocínio.
        if effort == "default":
            return
        kind = self._catalog_kind
        model_key = (model or "").strip().lower()

        if kind == "openrouter":
            mapped = {
                "minimal": "low",
                "low": "low",
                "medium": "medium",
                "high": "high",
                "xhigh": "high",
                "max": "high",
            }.get(effort)
            if mapped:
                payload["reasoning"] = {"effort": mapped}
            return

        if kind == "mistral":
            if effort == "off":
                effort = "none"
            if effort in {"none", "minimal", "low", "medium", "high", "xhigh"}:
                payload["reasoning_effort"] = effort
            return

        if kind == "cohere":
            payload["reasoning_effort"] = (
                "none" if effort in {"off", "none", "minimal"} else "high"
            )
            return

        if kind == "zai":
            supports_thinking = model_key.startswith(
                ("glm-4.5", "glm-4.6", "glm-4.7", "glm-5")
            )
            if not supports_thinking:
                return

            forced_thinking = model_key.startswith("glm-5.3")
            enabled = forced_thinking or effort not in {"off", "none"}
            payload["thinking"] = {"type": "enabled" if enabled else "disabled"}

            if model_key.startswith("glm-5.3"):
                payload["reasoning_effort"] = (
                    effort if effort in {"low", "high", "max"} else "max"
                )
            elif model_key.startswith("glm-5.2") and enabled:
                if effort in {"minimal", "low", "medium", "high", "xhigh", "max"}:
                    payload["reasoning_effort"] = effort
            return

    @staticmethod
    def _tool_messages(request: ExecutionRequest) -> list:
        messages = []
        for exchange in request.tool_exchanges:
            messages.append({
                "role": "assistant",
                "content": exchange.assistant_text or None,
                "tool_calls": [{
                    "id": call.call_id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": json.dumps(call.arguments, ensure_ascii=False)},
                } for call in exchange.calls],
            })
            messages.extend({"role": "tool", "tool_call_id": result.call_id, "content": result.content} for result in exchange.results)
        return messages

    def _tool_payload(self, request: ExecutionRequest) -> list:
        saneadas = [replace(tool, name=_safe_tool_name(tool.name)) for tool in request.tools]
        aceitos, _ = valid_tools(saneadas, provider_label=self._label)
        return [{"type": "function", "function": {"name": tool.name, "description": tool.description, "parameters": tool.parameters}} for tool in aceitos]

    def _base_payload(self, request: ExecutionRequest, model: str, *, stream: bool = False) -> dict:
        user_content, _ = self._build_user_content(request)
        payload = {"model": model, "messages": [_system_message(request, model), {"role": "user", "content": user_content}]}
        _apply_sampling(payload, request)
        if request.tools:
            payload["tools"] = self._tool_payload(request)
        if request.tool_exchanges:
            payload["messages"].extend(self._tool_messages(request))
        self._apply_reasoning(payload, request, model)
        _apply_routing(payload, request)
        if stream:
            payload["stream"] = True
            if self._catalog_kind not in {"mistral", "cohere", "zai"}:
                payload["stream_options"] = {"include_usage": True}
        return payload

    async def execute(self, request: ExecutionRequest, model: str) -> ExecutionResult:
        user_content, attachment_results = self._build_user_content(request)
        payload = {"model": model, "messages": [_system_message(request, model), {"role": "user", "content": user_content}]}
        _apply_sampling(payload, request)
        if request.tools:
            payload["tools"] = self._tool_payload(request)
        if request.tool_exchanges:
            payload["messages"].extend(self._tool_messages(request))
        self._apply_reasoning(payload, request, model)
        _apply_routing(payload, request)
        started = time.monotonic()
        try:
            response = await self._client.post(f"{self._base_url}/chat/completions", json=payload, headers=self._headers())
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(
                provider_kind=self._catalog_kind,
                provider_label=self._label,
                model=model,
                status_code=exc.response.status_code,
                headers=exc.response.headers,
                body=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar {self._label}: {exc}") from exc
        duration = time.monotonic() - started
        message = raw.get("choices", [{}])[0].get("message", {})
        _check_routing(request, raw.get("provider"))
        content, content_reasoning = _content_text(message.get("content", "") or "")
        reasoning = (
            message.get("reasoning")
            or message.get("reasoning_content")
            or content_reasoning
            or None
        )
        tool_calls = [ToolCall(call_id=c.get("id", ""), name=c.get("function", {}).get("name", ""), arguments=_safe_json(c.get("function", {}).get("arguments"))) for c in (message.get("tool_calls") or [])]
        usage = raw.get("usage", {})
        return ExecutionResult(content=content, tokens=usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0), input_tokens=usage.get("prompt_tokens", 0), output_tokens=usage.get("completion_tokens", 0), duration_seconds=duration, provider=self._label, model=model, metadata={"raw_usage": dict(usage), "request_id": raw.get("id"), "service_tier": raw.get("service_tier"), "provider_operational": {"headers": operational_headers(response.headers), "provider": raw.get("provider"), "service_tier": raw.get("service_tier")}, "attachment_results": [r.to_dict() for r in attachment_results]}, reasoning=reasoning, tool_calls=tool_calls)

    async def execute_stream(self, request: ExecutionRequest, model: str, on_delta, on_reasoning_delta=None) -> ExecutionResult:
        import json as _json
        _, attachment_results = self._build_user_content(request)
        payload = self._base_payload(request, model, stream=True)
        started = time.monotonic()
        text_parts: list = []
        reasoning_parts: list = []
        metrics = StreamMetrics(started=started)
        chamadas: dict = {}
        input_tokens = output_tokens = 0
        response_operational: dict = {}
        generation_id: str | None = None
        routed_provider: str | None = None
        service_tier: str | None = None
        try:
            async with self._client.stream("POST", f"{self._base_url}/chat/completions", json=payload, headers=self._headers()) as response:
                response_operational = {"headers": operational_headers(response.headers)}
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    # O corpo precisa ser lido do stream antes de virar
                    # mensagem: em `stream()` ele ainda não chegou quando
                    # `raise_for_status` dispara.
                    # `aread` quando o transporte a oferece; `text`
                    # quando o corpo já veio. Sem o fallback, um
                    # transporte que não implemente a leitura assíncrona
                    # troca o erro do provider por um AttributeError, e o
                    # motivo real da falha se perde.
                    detalhe = await read_stream_body(response)
                    raise classify_http_error(
                        provider_kind=self._catalog_kind,
                        provider_label=self._label,
                        model=model,
                        status_code=response.status_code,
                        headers=response.headers,
                        body=detalhe,
                    ) from exc
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw_data = line[len("data:"):].strip()
                    if raw_data == "[DONE]":
                        break
                    data = _json.loads(raw_data)
                    if generation_id is None and data.get("id"):
                        generation_id = str(data.get("id"))
                    if routed_provider is None and data.get("provider"):
                        routed_provider = str(data.get("provider"))
                    if service_tier is None and data.get("service_tier"):
                        service_tier = str(data.get("service_tier"))
                    usage = data.get("usage")
                    if usage:
                        input_tokens = usage.get("prompt_tokens", input_tokens)
                        output_tokens = usage.get("completion_tokens", output_tokens)
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    piece, structured_reasoning = _content_text(delta.get("content") or "")
                    if piece:
                        metrics.record(piece)
                        text_parts.append(piece)
                        on_delta(piece)
                    reasoning_piece = (
                        delta.get("reasoning")
                        or delta.get("reasoning_content")
                        or structured_reasoning
                        or ""
                    )
                    if reasoning_piece:
                        reasoning_parts.append(reasoning_piece)
                        if on_reasoning_delta is not None:
                            on_reasoning_delta(reasoning_piece)
                    for fragmento in delta.get("tool_calls") or []:
                        indice = fragmento.get("index", 0)
                        atual = chamadas.setdefault(indice, {"id": "", "name": "", "arguments": ""})
                        if fragmento.get("id"):
                            atual["id"] = fragmento["id"]
                        funcao = fragmento.get("function") or {}
                        if funcao.get("name"):
                            atual["name"] = funcao["name"]
                        if funcao.get("arguments"):
                            atual["arguments"] += funcao["arguments"]
        except RuntimeError:
            raise
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de rede ao chamar {self._label} (stream): {exc}") from exc
        _check_routing(request, routed_provider)
        tool_calls = [ToolCall(call_id=item["id"], name=item["name"], arguments=_safe_json(item["arguments"])) for _, item in sorted(chamadas.items()) if item["name"]]
        return ExecutionResult(content="".join(text_parts), tokens=input_tokens + output_tokens, input_tokens=input_tokens, output_tokens=output_tokens, duration_seconds=time.monotonic() - started, provider=self._label, model=model, metadata={"raw_usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens}, **metrics.as_dict(output_tokens), "request_id": generation_id, "service_tier": service_tier, "provider_operational": {**response_operational, "provider": routed_provider, "service_tier": service_tier}, "attachment_results": [r.to_dict() for r in attachment_results]}, reasoning="".join(reasoning_parts) or None, tool_calls=tool_calls)


def _apply_routing(payload: dict, request) -> None:
    """Fixa a empresa que serve o modelo (OpenRouter `provider.order`), sem plano B."""
    upstream = getattr(request, "upstream_provider", None)
    if upstream:
        payload["provider"] = {"order": [upstream], "allow_fallbacks": False}


def _check_routing(request, served_by) -> None:
    """Recusa a resposta servida por outra empresa: o dado não seria do modelo fixado."""
    upstream = getattr(request, "upstream_provider", None)
    if upstream and served_by and str(served_by).lower() != upstream.lower():
        raise RuntimeError(f"Fornecedor fixado {upstream}, mas a resposta veio de {served_by}.")


def _system_message(request, model: str) -> dict:
    text = system_text(request)
    if "claude" not in (model or "").lower():
        return {"role": "system", "content": text}
    blocks = []
    if request.shared_instructions:
        blocks.append({"type": "text", "text": request.shared_instructions, "cache_control": {"type": "ephemeral"}})
    if request.wave_instructions:
        blocks.append({"type": "text", "text": request.wave_instructions, "cache_control": {"type": "ephemeral"}})
    if not blocks:
        return {"role": "system", "content": [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]}
    blocks.append({"type": "text", "text": request.instructions})
    return {"role": "system", "content": blocks}


def _apply_sampling(payload: dict, request) -> None:
    sampling = getattr(request, "sampling", None)
    if not sampling:
        return
    if sampling.temperature is not None:
        payload["temperature"] = sampling.temperature
    if sampling.top_p is not None:
        payload["top_p"] = sampling.top_p
    if sampling.max_tokens is not None:
        payload["max_tokens"] = sampling.max_tokens

