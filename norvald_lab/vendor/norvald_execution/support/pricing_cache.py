"""
Cache de preço por modelo.

O preço por token vem do próprio catálogo do provider (hoje, só
OpenRouter/OpenAI publicam `pricing` no `/models` — Anthropic, Gemini e
Ollama não expõem isso ali, e não fabricamos número nenhum pra eles: o
custo dessas chamadas fica genuinamente desconhecido, não zero).

Esse preço só é conhecido quando alguém pede a lista de modelos de um
provider (`GET /api/settings/providers/{name}/models` — chamado ao
configurar uma deliberação, e pelo health-check do Dashboard). Este
módulo guarda o último preço visto por `(kind, model_id)`, pra que
`agent_orchestrator.py` — que só tem `kind` e `model_id` disponíveis no
momento da chamada, nunca o catálogo inteiro — consiga calcular custo
real sem precisar rechamar o provider a cada execução.

`kind` (não o nome da conexão) é a chave certa: é isso que
`ExecutionResult.provider` carrega (ver cada Provider._label/"provider="
em orchestrator/providers/*.py) e é isso que telemetry_events.provider
armazena — preço de um modelo na OpenRouter é o mesmo não importa qual
das suas contas OpenRouter fez a chamada.
"""
import threading
from typing import Dict, Optional, Tuple

_lock = threading.Lock()
_prices: Dict[Tuple[str, str], Tuple[Optional[float], Optional[float]]] = {}


def update(kind: str, model_id: str, price_input_per_million: Optional[float], price_output_per_million: Optional[float]) -> None:
    if not kind or not model_id:
        return
    if price_input_per_million is None and price_output_per_million is None:
        return
    with _lock:
        _prices[(kind, model_id)] = (price_input_per_million, price_output_per_million)


def get(kind: str, model_id: str) -> Optional[Tuple[Optional[float], Optional[float]]]:
    with _lock:
        return _prices.get((kind or "", model_id or ""))


def estimate_cost(kind: str, model_id: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """Devolve `None` quando o preço não é conhecido — nunca um
    número inventado. `None` é o sinal correto de 'sem dado', e é
    assim que o Dashboard já trata custo ausente (mostra "—")."""
    prices = get(kind, model_id)
    if prices is None:
        return None
    price_input, price_output = prices
    if price_input is None and price_output is None:
        return None
    total = 0.0
    if price_input is not None:
        total += (input_tokens / 1_000_000) * price_input
    if price_output is not None:
        total += (output_tokens / 1_000_000) * price_output
    return round(total, 8)

