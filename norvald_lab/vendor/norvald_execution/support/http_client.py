from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

# Pool compartilhado por todos os providers. O padrão do httpx é 10
# conexões por host, que satura com uma leva de 5 especialistas mais
# chamadas de ferramenta em paralelo.
DEFAULT_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)


class ConnectionTimings:
    """Tempo de fila e de conexão, por requisição.

    O relógio do provider começa quando a requisição sai. Antes disso há
    dois trechos que a medição de TTFT não distinguia: esperar uma
    conexão livre no pool (fila) e abrir uma nova (DNS, TCP, TLS).

    A diferença importa para decidir o que fazer. Fila alta significa
    pool pequeno para a concorrência da leva. Conexão alta e recorrente
    significa keep-alive não sendo aproveitado. TTFT alto com fila e
    conexão baixas é o provider, e aí não há nada a otimizar aqui.

    A instrumentação é por requisição e vive só durante ela: os hooks do
    httpx são globais ao cliente, então o estado fica numa variável de
    contexto, e não em atributo do cliente, que seria compartilhado
    entre chamadas concorrentes.
    """

    def __init__(self) -> None:
        self._requests: Dict[int, Dict[str, float]] = {}

    def hooks(self) -> Dict[str, list]:
        return {"request": [self._on_request], "response": [self._on_response]}

    async def _on_request(self, request: httpx.Request) -> None:
        self._requests[id(request)] = {"started": time.monotonic()}

    async def _on_response(self, response: httpx.Response) -> None:
        entry = self._requests.pop(id(response.request), None)
        if entry is None:
            return
        # `elapsed` do httpx só existe depois de ler o corpo, o que em
        # streaming aconteceria tarde demais. Medimos até os cabeçalhos,
        # que é o marco de "o servidor começou a responder".
        entry["headers_at"] = time.monotonic()

    def snapshot(self, request: httpx.Request) -> Optional[Dict[str, float]]:
        return self._requests.get(id(request))


def build_client(*, timeout: float, http2: bool = True, **kwargs: Any) -> httpx.AsyncClient:
    """Cliente com pool e HTTP/2, num lugar só.

    Os quatro adapters repetiam a mesma configuração; qualquer ajuste
    exigia lembrar dos quatro. Centralizar não é abstração gratuita — é
    o que evita que um provider fique para trás numa mudança de pool.
    """
    return httpx.AsyncClient(timeout=timeout, limits=DEFAULT_LIMITS, http2=http2, **kwargs)

