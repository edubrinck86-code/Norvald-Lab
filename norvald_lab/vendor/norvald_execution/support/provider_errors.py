"""Normalização de erros operacionais de providers.

HTTP status sozinho não diz o que aconteceu. Em especial, 429 pode significar
limite transitório, quota diária esgotada, saldo, plano incompatível ou
sobrecarga. Este módulo preserva a informação estruturada que a API realmente
devolve e converte apenas categorias que conseguimos sustentar.

O resultado alimenta retry, Provider Intelligence e a UI. Nunca inclui headers
de autenticação/cookies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping, Optional

from norvald_lab.vendor.norvald_execution.support.rate_limit import ProviderRateLimited, parse_retry_after


_OPERATIONAL_HEADER_NAMES = {
    "retry-after",
    "x-request-id",
    "request-id",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
    "x-ratelimit-reset-input-tokens",
    "x-ratelimit-reset-output-tokens",
    "anthropic-ratelimit-requests-limit",
    "anthropic-ratelimit-requests-remaining",
    "anthropic-ratelimit-requests-reset",
    "anthropic-ratelimit-tokens-limit",
    "anthropic-ratelimit-tokens-remaining",
    "anthropic-ratelimit-tokens-reset",
}


def operational_headers(headers: Mapping[str, Any] | None) -> dict[str, str]:
    if not headers:
        return {}
    result: dict[str, str] = {}
    for key, value in headers.items():
        normalized = str(key).lower()
        if normalized in _OPERATIONAL_HEADER_NAMES or normalized.startswith("x-ratelimit-"):
            result[normalized] = str(value)
    return result


def _safe_json(raw: str | bytes | None) -> dict:
    if not raw:
        return {}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


def _message_from(payload: dict, fallback: str) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        for key in ("message", "detail", "description"):
            if error.get(key):
                return str(error[key])
    if isinstance(error, str) and error:
        return error
    for key in ("message", "detail", "error_description"):
        if payload.get(key):
            return str(payload[key])
    return fallback.strip()[:1200]


def _provider_code(payload: dict) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict):
        for key in ("code", "type", "status"):
            value = error.get(key)
            if value not in (None, ""):
                return str(value)
    for key in ("code", "type", "status"):
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _request_id(headers: Mapping[str, Any] | None, payload: dict) -> str | None:
    safe = operational_headers(headers)
    for key in ("x-request-id", "request-id"):
        if safe.get(key):
            return safe[key]
    for key in ("request_id", "requestId", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _reset_from_message(message: str) -> str | None:
    # Z.AI inclui next_flush_time já renderizado na mensagem. Não tentamos
    # adivinhar timezone/formato; preservamos o trecho literal como reset_at.
    patterns = (
        r"resets? at\s+([^.;]+)",
        r"reset at\s+([^.;]+)",
        r"will reset at\s+([^.;]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


@dataclass
class ProviderAPIError(Exception):
    provider: str
    model: str = ""
    http_status: int | None = None
    category: str = "provider_error"
    message: str = ""
    provider_code: str | None = None
    retryable: bool = False
    retry_after: float | None = None
    reset_at: str | None = None
    scope: str = "request"
    request_id: str | None = None
    limit: float | int | None = None
    remaining: float | int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        prefix = self.provider + (f" ({self.model})" if self.model else "")
        detail = self.message.strip() or self.category.replace("_", " ")
        retry = f" Tentar novamente em {self.retry_after:.0f}s." if self.retry_after else ""
        return f"{prefix}: {detail}.{retry}"


_ZAI_CATEGORY_BY_CODE = {
    "1113": ("billing_or_package", False, "account"),
    "1302": ("rate_limit", True, "account"),
    "1305": ("provider_overloaded", True, "provider"),
    "1308": ("usage_window_exhausted", False, "account"),
    "1309": ("plan_expired", False, "account"),
    "1310": ("period_quota_exhausted", False, "account"),
    "1311": ("model_not_in_plan", False, "model"),
    "1313": ("fair_use_restriction", False, "account"),
    "1314": ("enterprise_plan_expired", False, "account"),
    "1315": ("wrong_product_endpoint", False, "connection"),
    "1316": ("usage_window_exhausted", False, "account"),
    "1317": ("usage_window_exhausted", False, "account"),
    "1318": ("spend_limit", False, "account"),
    "1319": ("spend_limit", False, "account"),
    "1320": ("spend_limit", False, "account"),
    "1321": ("spend_limit", False, "account"),
}


def _gemini_details(payload: dict) -> tuple[str | None, str | None, dict]:
    error = payload.get("error")
    details = error.get("details") if isinstance(error, dict) else None
    if not isinstance(details, list):
        return None, None, {}

    category = None
    retry_delay = None
    metadata: dict[str, Any] = {}
    violations: list[dict] = []
    for item in details:
        if not isinstance(item, dict):
            continue
        type_name = str(item.get("@type") or "")
        if type_name.endswith("RetryInfo") and item.get("retryDelay"):
            retry_delay = str(item["retryDelay"])
        if type_name.endswith("QuotaFailure"):
            raw_violations = item.get("violations")
            if isinstance(raw_violations, list):
                violations.extend(v for v in raw_violations if isinstance(v, dict))
    if violations:
        category = "quota_exhausted"
        metadata["quota_violations"] = violations
    if retry_delay:
        metadata["retry_delay"] = retry_delay
    return category, retry_delay, metadata


def _cohere_429_category(message: str) -> tuple[str, str]:
    lower = message.lower()
    if "token rate limit" in lower or "tokens per minute" in lower:
        return "token_rate_limit", "model"
    if "per minute request limit" in lower or "calls / minute" in lower or "requests per minute" in lower:
        return "request_rate_limit", "model"
    if "trial" in lower:
        return "trial_rate_limit", "account"
    return "rate_limit", "account"


def _mistral_429_category(message: str) -> tuple[str, bool, str]:
    lower = message.lower()
    if any(token in lower for token in ("budget", "spend", "billing", "payment")):
        return "spend_limit", False, "account"
    if "token" in lower and ("minute" in lower or "rate" in lower):
        return "token_rate_limit", True, "model"
    return "rate_limit", True, "account"


def classify_http_error(
    *,
    provider_kind: str,
    provider_label: str,
    model: str,
    status_code: int,
    headers: Mapping[str, Any] | None,
    body: str | bytes | None,
) -> Exception:
    """Transforma uma resposta HTTP em erro operacional estruturado."""
    kind = (provider_kind or provider_label or "").strip().lower()
    payload = _safe_json(body)
    message = _message_from(payload, body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body or ""))
    code = _provider_code(payload)
    safe_headers = operational_headers(headers)
    retry_after = parse_retry_after(safe_headers.get("retry-after"))
    request_id = _request_id(headers, payload)
    reset_at = _reset_from_message(message)
    metadata: dict[str, Any] = {"headers": safe_headers}
    if payload:
        # O corpo pode conter detalhes operacionais úteis, mas nunca a chave
        # porque ela não faz parte da resposta do provider.
        metadata["provider_error"] = payload

    category = "provider_error"
    retryable = status_code in {408, 429, 500, 502, 503, 504, 524, 529}
    scope = "provider"

    lower_message = message.lower()
    if kind == "openrouter" and "no endpoints found" in lower_message:
        category = "no_compatible_endpoint"
        retryable = False
        scope = "model"
        if "tool use" in lower_message or "tools" in lower_message:
            metadata["missing_requirement"] = "tools"
        elif "image input" in lower_message or "image" in lower_message:
            metadata["missing_requirement"] = "image"
        elif "data policy" in lower_message:
            metadata["missing_requirement"] = "data_policy"
        return ProviderAPIError(
            provider=provider_label,
            model=model,
            http_status=status_code,
            category=category,
            message=message[:1200],
            provider_code=code,
            retryable=False,
            retry_after=retry_after,
            reset_at=reset_at,
            scope=scope,
            request_id=request_id,
            metadata=metadata,
        )

    if status_code in {401, 403}:
        category = "authentication" if status_code == 401 else "permission"
        retryable = False
        scope = "connection"
    elif status_code == 402:
        category = "billing"
        retryable = False
        scope = "account"
    elif status_code == 404:
        category = "model_or_endpoint_not_found"
        retryable = False
        scope = "model"
    elif status_code in {408, 524}:
        category = "timeout"
        scope = "provider"
    elif status_code in {500, 502, 503, 504, 529}:
        category = "provider_overloaded" if status_code in {503, 529} else "upstream_error"
        scope = "provider"

    if kind in {"zai", "z.ai", "z-ai", "zhipu", "zhipuai"} and code in _ZAI_CATEGORY_BY_CODE:
        category, retryable, scope = _ZAI_CATEGORY_BY_CODE[code]
        if retryable and category == "rate_limit":
            return ProviderRateLimited(
                provider=provider_label,
                model=model,
                retry_after=retry_after,
                detail=message[:800],
                category=category,
                provider_code=code,
                scope=scope,
                reset_at=reset_at,
                request_id=request_id,
                metadata=metadata,
            )
        return ProviderAPIError(
            provider=provider_label,
            model=model,
            http_status=status_code,
            category=category,
            message=message[:1200],
            provider_code=code,
            retryable=retryable,
            retry_after=retry_after,
            reset_at=reset_at,
            scope=scope,
            request_id=request_id,
            metadata=metadata,
        )

    if kind == "gemini" and status_code == 429:
        detail_category, retry_delay, extra = _gemini_details(payload)
        metadata.update(extra)
        category = detail_category or "rate_limit"
        if retry_delay and retry_after is None:
            match = re.fullmatch(r"([0-9.]+)s", retry_delay.strip())
            if match:
                retry_after = float(match.group(1))

        violations = extra.get("quota_violations") if isinstance(extra, dict) else None
        daily_quota = False
        if isinstance(violations, list):
            for violation in violations:
                if not isinstance(violation, dict):
                    continue
                haystack = " ".join(
                    str(violation.get(key) or "")
                    for key in ("quotaId", "quotaMetric", "description", "subject")
                ).lower()
                if any(token in haystack for token in ("perday", "per_day", "daily", "requestsperday")):
                    daily_quota = True
                    break
        if daily_quota and retry_after is None:
            return ProviderAPIError(
                provider=provider_label,
                model=model,
                http_status=429,
                category="daily_quota_exhausted",
                message=message[:1200],
                provider_code=code,
                retryable=False,
                scope="project",
                request_id=request_id,
                metadata=metadata,
            )

        # RPM/TPM e quotas com RetryInfo são transitórias.
        return ProviderRateLimited(
            provider=provider_label,
            model=model,
            retry_after=retry_after,
            detail=message[:800],
            category=category,
            provider_code=code,
            scope="project",
            reset_at=reset_at,
            request_id=request_id,
            metadata=metadata,
        )

    if kind == "cohere" and status_code == 429:
        category, scope = _cohere_429_category(message)
        return ProviderRateLimited(
            provider=provider_label,
            model=model,
            retry_after=retry_after,
            detail=message[:800],
            category=category,
            provider_code=code,
            scope=scope,
            request_id=request_id,
            metadata=metadata,
        )

    if kind == "mistral" and status_code == 429:
        category, retryable, scope = _mistral_429_category(message)
        if retryable:
            return ProviderRateLimited(
                provider=provider_label,
                model=model,
                retry_after=retry_after,
                detail=message[:800],
                category=category,
                provider_code=code,
                scope=scope,
                request_id=request_id,
                metadata=metadata,
            )
        return ProviderAPIError(
            provider=provider_label,
            model=model,
            http_status=status_code,
            category=category,
            message=message[:1200],
            provider_code=code,
            retryable=False,
            retry_after=retry_after,
            reset_at=reset_at,
            scope=scope,
            request_id=request_id,
            metadata=metadata,
        )

    if status_code == 429:
        # OpenRouter/OpenAI/NVIDIA/xAI/custom: 429 sem código mais específico
        # é tratado como limite transitório, preservando headers e corpo.
        return ProviderRateLimited(
            provider=provider_label,
            model=model,
            retry_after=retry_after,
            detail=message[:800],
            category="rate_limit",
            provider_code=code,
            scope="account",
            reset_at=reset_at,
            request_id=request_id,
            metadata=metadata,
        )

    return ProviderAPIError(
        provider=provider_label,
        model=model,
        http_status=status_code,
        category=category,
        message=message[:1200],
        provider_code=code,
        retryable=retryable,
        retry_after=retry_after,
        reset_at=reset_at,
        scope=scope,
        request_id=request_id,
        metadata=metadata,
    )

