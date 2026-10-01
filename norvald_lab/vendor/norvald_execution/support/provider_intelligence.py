"""Inteligência operacional de providers e modelos.

Catálogo responde "este modelo existe". Esta camada responde outra pergunta:
"o que sabemos, com esta conexão, sobre conseguir usá-lo agora?".

Nenhuma sondagem paga é disparada. O estado combina:
- health da conexão;
- dados operacionais que o provider expõe sem inferência (ex.: OpenRouter);
- sucessos/erros observados nas execuções reais do Studio;
- headers e códigos estruturados devolvidos pelos providers.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
import time
from typing import Any, Deque, Dict, Optional

from norvald_lab.vendor.norvald_execution.support.provider_errors import ProviderAPIError
from norvald_lab.vendor.norvald_execution.support.rate_limit import ProviderRateLimited


_RUNTIME_WINDOW_SECONDS = 15 * 60
_PROBE_TTL_SECONDS = 90.0
_ACCOUNT_TTL_SECONDS = 120.0


def _now() -> float:
    return time.time()


@dataclass
class RuntimeObservation:
    ok: bool
    occurred_at: float
    category: str
    http_status: int | None = None
    provider_code: str | None = None
    message: str = ""
    retry_after: float | None = None
    reset_at: str | None = None
    scope: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "occurred_at": self.occurred_at,
            "category": self.category,
            "http_status": self.http_status,
            "provider_code": self.provider_code,
            "message": self.message,
            "retry_after": self.retry_after,
            "reset_at": self.reset_at,
            "scope": self.scope,
            "request_id": self.request_id,
            "metadata": self.metadata,
        }


class ProviderIntelligenceCache:
    def __init__(self):
        self._runtime: Dict[tuple[str, str], Deque[RuntimeObservation]] = defaultdict(
            lambda: deque(maxlen=12)
        )
        self._model_probes: dict[tuple[str, str], tuple[float, dict]] = {}
        self._account_probes: dict[str, tuple[float, dict]] = {}
        self._connection_kinds: dict[str, str] = {}

    def record_success(
        self,
        connection_name: str,
        provider_kind: str,
        model: str,
        metadata: Optional[dict] = None,
    ) -> None:
        if not connection_name or not model:
            return
        self._connection_kinds[connection_name] = provider_kind or ""
        metadata = dict(metadata or {})
        request_id = metadata.get("request_id")
        operational = metadata.get("provider_operational")
        self._runtime[(connection_name, model)].append(
            RuntimeObservation(
                ok=True,
                occurred_at=_now(),
                category="success",
                request_id=str(request_id) if request_id else None,
                metadata=operational if isinstance(operational, dict) else {},
            )
        )

    def record_failure(
        self,
        connection_name: str,
        provider_kind: str,
        model: str,
        exc: Exception,
    ) -> None:
        if not connection_name or not model:
            return
        self._connection_kinds[connection_name] = provider_kind or ""

        if isinstance(exc, ProviderRateLimited):
            observation = RuntimeObservation(
                ok=False,
                occurred_at=_now(),
                category=exc.category or "rate_limit",
                http_status=429,
                provider_code=exc.provider_code,
                message=exc.detail or str(exc),
                retry_after=exc.retry_after,
                reset_at=exc.reset_at,
                scope=exc.scope,
                request_id=exc.request_id,
                metadata=dict(exc.metadata or {}),
            )
        elif isinstance(exc, ProviderAPIError):
            observation = RuntimeObservation(
                ok=False,
                occurred_at=_now(),
                category=exc.category,
                http_status=exc.http_status,
                provider_code=exc.provider_code,
                message=exc.message or str(exc),
                retry_after=exc.retry_after,
                reset_at=exc.reset_at,
                scope=exc.scope,
                request_id=exc.request_id,
                metadata=dict(exc.metadata or {}),
            )
        else:
            observation = RuntimeObservation(
                ok=False,
                occurred_at=_now(),
                category="execution_error",
                message=str(exc)[:1200],
            )
        self._runtime[(connection_name, model)].append(observation)

    def runtime_snapshot(self, connection_name: str, model: str) -> dict:
        observations = list(self._runtime.get((connection_name, model), ()))
        now = _now()
        recent = [item for item in observations if now - item.occurred_at <= _RUNTIME_WINDOW_SECONDS]
        successes = sum(1 for item in recent if item.ok)
        failures = len(recent) - successes
        failure_categories: dict[str, int] = {}
        for item in recent:
            if item.ok:
                continue
            failure_categories[item.category] = failure_categories.get(item.category, 0) + 1
        latest = recent[-1] if recent else None
        return {
            "window_seconds": _RUNTIME_WINDOW_SECONDS,
            "observations": len(recent),
            "successes": successes,
            "failures": failures,
            "failure_categories": failure_categories,
            "success_rate": round(successes / len(recent), 4) if recent else None,
            "last": latest.to_dict() if latest else None,
        }

    def put_model_probe(self, connection_name: str, model: str, payload: dict) -> None:
        self._model_probes[(connection_name, model)] = (time.monotonic(), dict(payload or {}))

    def get_model_probe(self, connection_name: str, model: str) -> dict | None:
        cached = self._model_probes.get((connection_name, model))
        if cached is None:
            return None
        if time.monotonic() - cached[0] > _PROBE_TTL_SECONDS:
            return None
        return dict(cached[1])

    def put_account_probe(self, connection_name: str, payload: dict) -> None:
        self._account_probes[connection_name] = (time.monotonic(), dict(payload or {}))

    def get_account_probe(self, connection_name: str) -> dict | None:
        cached = self._account_probes.get(connection_name)
        if cached is None:
            return None
        if time.monotonic() - cached[0] > _ACCOUNT_TTL_SECONDS:
            return None
        return dict(cached[1])

    @staticmethod
    def _state_from_runtime(runtime: dict) -> tuple[str, str]:
        last = runtime.get("last")
        if not isinstance(last, dict):
            return "unknown", "Sem execução recente deste modelo."

        if last.get("ok"):
            failures = int(runtime.get("failures") or 0)
            categories = runtime.get("failure_categories") or {}
            if failures:
                if any(
                    key in categories
                    for key in ("rate_limit", "request_rate_limit", "token_rate_limit", "trial_rate_limit")
                ):
                    return "degraded", "O modelo respondeu, mas sofreu limitação de taxa recentemente."
                return "degraded", "O modelo respondeu, mas houve falhas recentes na mesma janela."
            return "available", "Última execução real do Studio foi bem-sucedida."

        category = str(last.get("category") or "")
        if category in {
            "rate_limit",
            "request_rate_limit",
            "token_rate_limit",
            "trial_rate_limit",
            "usage_window_exhausted",
            "period_quota_exhausted",
            "daily_quota_exhausted",
        }:
            return "rate_limited", "A última execução atingiu um limite de uso/quota."
        if category in {
            "billing",
            "billing_or_package",
            "plan_expired",
            "enterprise_plan_expired",
            "model_not_in_plan",
            "wrong_product_endpoint",
            "authentication",
            "permission",
            "no_compatible_endpoint",
        }:
            return "unavailable", "A última execução encontrou uma restrição não transitória."
        if category in {"provider_overloaded", "upstream_error", "timeout"}:
            return "degraded", "O provider/endpoint apresentou falha transitória."
        return "degraded", "A última execução real falhou."

    @staticmethod
    def _state_from_probe(probe: dict | None) -> tuple[str, str] | None:
        if not isinstance(probe, dict):
            return None
        state = probe.get("availability")
        if isinstance(state, dict):
            value = str(state.get("state") or "")
            if value in {"available", "degraded", "rate_limited", "unavailable", "unknown"}:
                return value, str(state.get("reason") or "Estado informado pelo provider.")
        return None

    @staticmethod
    def _state_from_catalog(
        descriptor: Any | None,
        provider_kind: str,
        connection_status: str | None,
    ) -> tuple[str, str] | None:
        if descriptor is None:
            return None

        flags = {
            str(value).strip().lower()
            for value in (getattr(descriptor, "flags", None) or [])
            if str(value).strip()
        }
        if flags & {"deprecated", "archived", "disabled", "retired"}:
            return "unavailable", "O catálogo marca este modelo como descontinuado ou indisponível."

        execution_support = str(
            getattr(descriptor, "execution_support", "unknown") or "unknown"
        ).lower()
        if execution_support == "unsupported":
            return (
                "unavailable",
                getattr(descriptor, "execution_reason", None)
                or "O catálogo declara que este modelo não é compatível com execução conversacional.",
            )

        # Para estes providers o catálogo usado pelo Studio é autenticado e
        # publica evidência de que o modelo é executável. Isso é uma evidência
        # mais fraca que uma inferência real, mas suficiente para verde com
        # origem explícita "catalog". OpenRouter/NVIDIA ficam fora porque o
        # catálogo pode existir mesmo quando a rota concreta não é utilizável.
        trusted_catalog_kinds = {
            "anthropic",
            "cohere",
            "gemini",
            "mistral",
            "openai",
            "xai",
            "cerebras",
            "zai",
            "zai-coding",
            "ollama",
        }
        kind = (provider_kind or "").strip().lower()
        if (
            connection_status == "online"
            and execution_support == "supported"
            and kind in trusted_catalog_kinds
        ):
            return (
                "available",
                "Conexão online e catálogo autenticado declaram este modelo como executável.",
            )
        return None


    def availability(
        self,
        connection_name: str,
        model: str,
        *,
        connection_status: str | None = None,
        descriptor: Any | None = None,
        provider_kind: str = "",
    ) -> dict:
        probe = self.get_model_probe(connection_name, model)
        probe_state = self._state_from_probe(probe)
        runtime = self.runtime_snapshot(connection_name, model)
        runtime_state, runtime_reason = self._state_from_runtime(runtime)

        # Restrição explícita recente do runtime vence um "uptime" genérico:
        # a chave concreta do usuário acabou de provar que não consegue usar.
        if runtime_state in {"rate_limited", "unavailable"}:
            state, reason = runtime_state, runtime_reason
            source = "runtime"
        elif probe_state and probe_state[0] != "unknown":
            state, reason = probe_state
            source = "provider_probe"
            if runtime_state == "degraded" and state == "available":
                state = "degraded"
                reason = runtime_reason
                source = "runtime"
        elif runtime_state != "unknown":
            state, reason = runtime_state, runtime_reason
            source = "runtime"
        elif connection_status == "rate_limited":
            state, reason, source = "rate_limited", "A conexão está limitada pelo provider.", "connection"
        elif connection_status == "offline":
            state, reason, source = "unavailable", "A conexão não está operacional.", "connection"
        else:
            catalog_state = self._state_from_catalog(
                descriptor,
                provider_kind,
                connection_status,
            )
            if catalog_state is not None:
                state, reason = catalog_state
                source = "catalog"
            else:
                # Modelo listado sem evidência operacional suficiente.
                state, reason, source = "unknown", "Modelo listado, mas ainda sem evidência operacional específica.", "catalog"

        return {
            "state": state,
            "reason": reason,
            "source": source,
            "runtime": runtime,
            "checked_at": _now(),
        }

    def invalidate_connection(self, connection_name: str) -> None:
        self._account_probes.pop(connection_name, None)
        for key in [key for key in self._model_probes if key[0] == connection_name]:
            self._model_probes.pop(key, None)
        for key in [key for key in self._runtime if key[0] == connection_name]:
            self._runtime.pop(key, None)


provider_intelligence_cache = ProviderIntelligenceCache()

