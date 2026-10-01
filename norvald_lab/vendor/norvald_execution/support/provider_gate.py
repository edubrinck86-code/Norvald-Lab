"""Controle adaptativo de concorrência por conexão de provider.

Uma leva pode ter vários especialistas, tool loops e retries. Permitir um
número fixo alto de streams simultâneos cria rajadas que atingem RPM/RPS de
providers gratuitos antes mesmo de o provider poder sinalizar o limite.

O gate começa conservador por família, reduz imediatamente ao observar 429 e
sobe gradualmente após uma sequência de sucessos. A decisão continua sendo por
CONEXÃO, não global.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import math
import random
import time
from typing import Awaitable, Callable, Dict, Optional, TypeVar

from norvald_lab.vendor.norvald_execution.support.rate_limit import ProviderRateLimited

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Teto absoluto de segurança. Não é mais a concorrência efetiva.
MAX_CONCURRENT_PER_PROVIDER = 8
MAX_RETRIES = 2
BACKOFF_BASE_SECONDS = 2.0
SUCCESS_GROWTH_THRESHOLD = 8

# (inicial, máximo adaptativo)
_KIND_LIMITS: dict[str, tuple[int, int]] = {
    "openrouter": (3, 6),
    "cohere": (2, 4),
    "gemini": (3, 6),
    "zai": (2, 4),
    "z.ai": (2, 4),
    "zai-coding": (2, 4),
    "mistral": (4, 8),
    "nvidia": (1, 3),
    "anthropic": (4, 8),
    "openai": (4, 8),
    "xai": (3, 6),
    "cerebras": (3, 6),
    "meta": (3, 6),
    "ollama": (6, 8),
}
_DEFAULT_LIMITS = (3, 6)


@dataclass
class _ProviderState:
    kind: str
    limit: int
    max_limit: int
    active: int = 0
    success_streak: int = 0
    last_limited_at: float | None = None
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)


class ProviderGate:
    def __init__(self, max_concurrent: int = MAX_CONCURRENT_PER_PROVIDER):
        self._absolute_max = max(1, int(max_concurrent))
        self._blocked_until: Dict[str, float] = {}
        self._states: Dict[str, _ProviderState] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _normalized_kind(kind: str) -> str:
        return (kind or "").strip().lower()

    def _profile(self, kind: str) -> tuple[int, int]:
        initial, maximum = _KIND_LIMITS.get(self._normalized_kind(kind), _DEFAULT_LIMITS)
        return min(initial, self._absolute_max), min(maximum, self._absolute_max)

    async def _state_for(self, provider: str, kind: str) -> _ProviderState:
        async with self._lock:
            state = self._states.get(provider)
            if state is None:
                initial, maximum = self._profile(kind)
                state = _ProviderState(
                    kind=self._normalized_kind(kind),
                    limit=max(1, initial),
                    max_limit=max(1, maximum),
                )
                self._states[provider] = state
            elif kind and not state.kind:
                state.kind = self._normalized_kind(kind)
            return state

    def _espera_restante(self, provider: str) -> float:
        return max(0.0, self._blocked_until.get(provider, 0.0) - time.monotonic())

    def _bloquear(self, provider: str, segundos: float) -> None:
        ate = time.monotonic() + max(0.0, segundos)
        self._blocked_until[provider] = max(self._blocked_until.get(provider, 0.0), ate)

    async def _acquire(self, state: _ProviderState) -> None:
        async with state.condition:
            while state.active >= state.limit:
                await state.condition.wait()
            state.active += 1

    async def _release(self, state: _ProviderState) -> None:
        async with state.condition:
            state.active = max(0, state.active - 1)
            state.condition.notify_all()

    async def _on_rate_limit(self, state: _ProviderState) -> None:
        async with state.condition:
            old_limit = state.limit
            state.limit = max(1, math.ceil(state.limit / 2))
            state.success_streak = 0
            state.last_limited_at = time.time()
            state.condition.notify_all()
        if state.limit != old_limit:
            logger.info(
                "Provider gate reduziu concorrência %d -> %d após 429 (%s).",
                old_limit,
                state.limit,
                state.kind or "custom",
            )

    async def _on_success(self, state: _ProviderState) -> None:
        async with state.condition:
            state.success_streak += 1
            if state.success_streak < SUCCESS_GROWTH_THRESHOLD or state.limit >= state.max_limit:
                return
            old_limit = state.limit
            state.limit = min(state.max_limit, state.limit + 1)
            state.success_streak = 0
            state.condition.notify_all()
        logger.info(
            "Provider gate elevou concorrência %d -> %d após estabilidade (%s).",
            old_limit,
            state.limit,
            state.kind or "custom",
        )

    def snapshot(self, provider: str) -> dict:
        state = self._states.get(provider)
        if state is None:
            return {
                "adaptive": True,
                "active": 0,
                "limit": None,
                "max_limit": None,
                "blocked_seconds": round(self._espera_restante(provider), 3),
                "success_streak": 0,
                "last_limited_at": None,
            }
        return {
            "adaptive": True,
            "kind": state.kind,
            "active": state.active,
            "limit": state.limit,
            "max_limit": state.max_limit,
            "blocked_seconds": round(self._espera_restante(provider), 3),
            "success_streak": state.success_streak,
            "last_limited_at": state.last_limited_at,
        }

    async def run(
        self,
        provider: str,
        operacao: Callable[[], Awaitable[T]],
        *,
        provider_kind: str = "",
        on_retry: Optional[Callable[[int, float, ProviderRateLimited], None]] = None,
    ) -> T:
        chave = provider or "desconhecido"
        state = await self._state_for(chave, provider_kind)

        for tentativa in range(MAX_RETRIES + 1):
            restante = self._espera_restante(chave)
            if restante > 0:
                await asyncio.sleep(restante)

            await self._acquire(state)
            try:
                result = await operacao()
            except ProviderRateLimited as limite:
                await self._on_rate_limit(state)
                if tentativa >= MAX_RETRIES:
                    self._bloquear(chave, limite.retry_after or BACKOFF_BASE_SECONDS)
                    raise

                espera = limite.retry_after or (
                    BACKOFF_BASE_SECONDS * (2**tentativa) + random.uniform(0, 0.5)
                )
                self._bloquear(chave, espera)
                if on_retry:
                    on_retry(tentativa + 1, espera, limite)
                logger.info(
                    "%s limitou a taxa; nova tentativa em %.1fs (%d de %d).",
                    chave,
                    espera,
                    tentativa + 1,
                    MAX_RETRIES,
                )
            else:
                await self._on_success(state)
                return result
            finally:
                await self._release(state)

        raise AssertionError("inalcançável")


_gate = ProviderGate()


def provider_gate() -> ProviderGate:
    return _gate

