"""Limite de taxa do provider.

Um 429 não é falha do especialista nem da deliberação: é o provider
dizendo que há chamadas demais no momento. Tratá-lo como erro genérico
faz o turno virar contribuição vazia, e a rodada segue como se aquele
participante não tivesse o que dizer.

O que ele precisa ser é um estado explícito, distinguível de "o modelo
não respondeu" e de "o modelo respondeu mal".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional


@dataclass
class ProviderRateLimited(Exception):
    """O provider recusou por limite de taxa.

    `retry_after` vem do cabeçalho quando o provider o informa. Respeitar
    o valor dado é melhor que estimar: um backoff cego pode tentar cedo
    demais — e consumir outra vez a cota — ou tarde demais, atrasando a
    rodada sem motivo.
    """

    provider: str
    model: str = ""
    retry_after: Optional[float] = None
    detail: str = ""
    category: str = "rate_limit"
    provider_code: str | None = None
    scope: str = "account"
    reset_at: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        labels = {
            "rate_limit": "limite de taxa",
            "request_rate_limit": "limite de requisições",
            "token_rate_limit": "limite de tokens",
            "trial_rate_limit": "limite da chave trial",
            "quota_exhausted": "quota esgotada",
        }
        motivo = labels.get(self.category, self.category.replace("_", " "))
        quando = (
            f" Tentar novamente em {self.retry_after:.0f}s."
            if self.retry_after
            else ""
        )
        detalhe = f" {self.detail.strip()[:300]}" if self.detail.strip() else ""
        return (
            f"{self.provider} recusou por {motivo}"
            + (f" ({self.model})" if self.model else "")
            + "."
            + detalhe
            + quando
        )


def parse_retry_after(valor: Optional[str]) -> Optional[float]:
    """O `Retry-After` em segundos, quando vier em formato utilizável.

    O cabeçalho aceita segundos ou data HTTP. Só o primeiro é tratado: a
    data exigiria confiar no relógio do servidor contra o nosso, e um
    desvio de fuso transformaria a espera em horas.

    Valor ausente ou ilegível devolve `None`, e quem chama cai no
    backoff — que é o comportamento correto, não uma falha.
    """
    if not valor:
        return None
    raw = str(valor).strip()
    try:
        segundos = float(raw)
    except (TypeError, ValueError):
        try:
            target = parsedate_to_datetime(raw)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            segundos = (target - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None
    if segundos < 0:
        return 0.0
    # Teto de um minuto: esperar mais que isso dentro de uma rodada
    # bloquearia a leva inteira. O valor literal continua preservado no
    # Provider Intelligence quando o provider informa um reset maior.
    return min(segundos, 60.0)

