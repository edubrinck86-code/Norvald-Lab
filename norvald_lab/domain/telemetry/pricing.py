from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from norvald_lab.domain.telemetry.provider_usage import ProviderUsage

# Versão da tabela embutida. Todo cálculo registra qual versão usou, para
# que uma atualização de preço não altere o custo histórico já gravado —
# o custo é um fato do momento da execução, não uma função do preço de
# hoje.
BUILTIN_PRICE_TABLE_VERSION = "builtin-2026-08"

# Preço por milhão de tokens, em USD. Fica fora do executor de propósito:
# o adapter do provider não deve conter regra comercial. Uma tabela
# externa em NORVALD_PRICING_PATH sobrescreve esta sem tocar em código.
_BUILTIN_PRICES: Dict[str, Dict[str, float]] = {
    "claude-opus-4": {"input": 15.0, "output": 75.0, "cached_input": 1.5, "cache_write": 18.75},
    "claude-sonnet": {"input": 3.0, "output": 15.0, "cached_input": 0.3, "cache_write": 3.75},
    "claude-haiku": {"input": 0.8, "output": 4.0, "cached_input": 0.08, "cache_write": 1.0},
    "gpt-5": {"input": 1.25, "output": 10.0, "cached_input": 0.125},
    "gpt-4o": {"input": 2.5, "output": 10.0, "cached_input": 1.25},
    "gemini-2-5-pro": {"input": 1.25, "output": 10.0, "cached_input": 0.31},
    "gemini-2-5-flash": {"input": 0.3, "output": 2.5, "cached_input": 0.075},
}


@dataclass(frozen=True)
class ProviderCost:
    """Custo derivado do usage por uma tabela de preços identificada.

    `None` em `total_cost` significa que não foi possível precificar —
    modelo fora da tabela, ou usage não reportado. Zero seria afirmar
    que a chamada foi gratuita, o que é uma afirmação diferente.
    """

    input_cost: Optional[float] = None
    output_cost: Optional[float] = None
    cache_cost: Optional[float] = None
    reasoning_cost: Optional[float] = None
    total_cost: Optional[float] = None
    currency: str = "USD"
    price_table_version: Optional[str] = None
    priced: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "cache_cost": self.cache_cost,
            "reasoning_cost": self.reasoning_cost,
            "total_cost": self.total_cost,
            "currency": self.currency,
            "price_table_version": self.price_table_version,
            "priced": self.priced,
            "reason": self.reason,
        }


class PriceTable:
    """Resolve `provider + model -> preços`, com versão declarada."""

    def __init__(self, prices: Dict[str, Dict[str, float]] | None = None, version: str | None = None):
        self._prices = prices if prices is not None else dict(_BUILTIN_PRICES)
        self._version = version or BUILTIN_PRICE_TABLE_VERSION

    @property
    def version(self) -> str:
        return self._version

    @classmethod
    def load(cls) -> "PriceTable":
        """Carrega de NORVALD_PRICING_PATH quando definido.

        O arquivo externo permite atualizar preços sem alterar o código
        nem o executor, que é o ponto: preço é decisão comercial e muda
        numa cadência que não é a do software.
        """
        path = os.environ.get("NORVALD_PRICING_PATH")
        if not path or not os.path.exists(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return cls(payload.get("prices") or {}, payload.get("version") or f"file:{os.path.basename(path)}")
        except (OSError, ValueError):
            return cls()

    def resolve(self, model: str) -> Optional[Dict[str, float]]:
        """Casa pelo prefixo mais específico declarado.

        Os identificadores carregam data e sufixo de release
        (`claude-sonnet-5-20260114`), então casar por igualdade exigiria
        reescrever a tabela a cada lançamento.
        """
        lowered = (model or "").lower()
        matches = [(key, value) for key, value in self._prices.items() if key in lowered]
        if not matches:
            return None
        return max(matches, key=lambda item: len(item[0]))[1]


def price_usage(usage: ProviderUsage, table: PriceTable | None = None) -> ProviderCost:
    """Transforma usage em custo sem tocar na execução."""
    table = table or PriceTable.load()

    if not usage.measured:
        return ProviderCost(
            currency="USD",
            price_table_version=table.version,
            priced=False,
            reason="O provider não reportou tokens nesta chamada.",
        )

    prices = table.resolve(usage.model)
    if prices is None:
        return ProviderCost(
            currency="USD",
            price_table_version=table.version,
            priced=False,
            reason=f"Sem preço declarado para '{usage.model}' nesta tabela.",
        )

    million = 1_000_000.0
    cached = usage.cached_input_tokens or 0
    # Tokens lidos do cache já vêm contados no input pelos providers;
    # cobrá-los duas vezes inflaria o custo.
    billable_input = max(0, (usage.input_tokens or 0) - cached)

    input_cost = billable_input * prices.get("input", 0.0) / million
    output_cost = (usage.output_tokens or 0) * prices.get("output", 0.0) / million
    cache_cost = (
        cached * prices.get("cached_input", 0.0) / million
        + (usage.cache_write_tokens or 0) * prices.get("cache_write", 0.0) / million
    )
    # Reasoning tokens já são faturados como saída em todos os providers
    # que os reportam; a linha existe para exibição, não soma de novo.
    reasoning_cost = (
        (usage.reasoning_tokens or 0) * prices.get("output", 0.0) / million
        if usage.reasoning_tokens is not None
        else None
    )

    return ProviderCost(
        input_cost=round(input_cost, 6),
        output_cost=round(output_cost, 6),
        cache_cost=round(cache_cost, 6),
        reasoning_cost=round(reasoning_cost, 6) if reasoning_cost is not None else None,
        total_cost=round(input_cost + output_cost + cache_cost, 6),
        currency="USD",
        price_table_version=table.version,
        priced=True,
    )

