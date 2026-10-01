from __future__ import annotations

import asyncio
import random
from typing import Awaitable, Callable, Optional, TypeVar

import httpx

from norvald_lab.vendor.norvald_execution.support.provider_errors import ProviderAPIError

T = TypeVar("T")

# Só estes. 429 é limite de taxa; 500, 502, 503 e 504 são falhas do lado
# do provider. Um 400 é payload inválido e um 401 é credencial errada —
# repetir os dois só gasta tempo e dinheiro para receber o mesmo erro.
RETRIABLE_STATUS = frozenset({429, 500, 502, 503, 504})

MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 0.5
MAX_DELAY_SECONDS = 8.0


def _retry_after(response: Optional[httpx.Response]) -> Optional[float]:
    """Respeita o `Retry-After` quando o provider o envia.

    O provider sabe melhor que nós quando estará livre; ignorar o
    cabeçalho e usar o backoff próprio costuma significar bater na porta
    cedo demais e gastar mais uma tentativa à toa.
    """
    if response is None:
        return None
    raw = response.headers.get("retry-after")
    if not raw:
        return None
    try:
        return min(float(raw), MAX_DELAY_SECONDS)
    except ValueError:
        return None


def _delay_for(attempt: int, response: Optional[httpx.Response]) -> float:
    hinted = _retry_after(response)
    if hinted is not None:
        return hinted
    # Exponencial com jitter. Sem o jitter, cinco especialistas que
    # tomam 429 ao mesmo tempo voltam juntos e tomam 429 de novo — a
    # leva inteira sincronizada no mesmo instante de retentativa.
    delay = min(BASE_DELAY_SECONDS * (2 ** attempt), MAX_DELAY_SECONDS)
    return delay * (0.5 + random.random() * 0.5)


def is_retriable(exc: BaseException) -> bool:
    if isinstance(exc, ProviderAPIError):
        return bool(exc.retryable)
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRIABLE_STATUS
    # Timeout e queda de conexão são transitórios por definição. Erros de
    # protocolo e de leitura de resposta não são.
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError))


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = MAX_ATTEMPTS,
    on_retry: Optional[Callable[[int, float, BaseException], None]] = None,
) -> T:
    """Repete falhas transitórias, e só elas.

    Antes não havia retentativa alguma: um 429 momentâneo — comum quando
    cinco especialistas chamam o mesmo provider ao mesmo tempo — matava o
    turno, e o participante entrava como `FAILED` numa rodada que teria
    funcionado meio segundo depois.

    Deliberadamente não repete o que já foi transmitido: uma chamada em
    streaming que falhou depois de emitir texto seria reiniciada do zero,
    duplicando o que o usuário já viu. Quem chama decide, passando
    `max_attempts=1` nesse caso.
    """
    last: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001 - reclassificado logo abaixo
            if not is_retriable(exc) or attempt == max_attempts - 1:
                raise
            last = exc
            response = exc.response if isinstance(exc, httpx.HTTPStatusError) else None
            delay = _delay_for(attempt, response)
            if on_retry:
                on_retry(attempt + 1, delay, exc)
            await asyncio.sleep(delay)
    # Inalcançável: o laço ou retorna ou levanta.
    raise last if last else RuntimeError("Retry sem tentativas")

