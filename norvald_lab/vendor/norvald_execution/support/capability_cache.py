"""Capabilities do catálogo, por (kind, model_id).

Mesmo padrão e mesma motivação do `pricing_cache`: quem descobre modelos
(`model_discovery.discover_models`) alimenta este cache de passagem, e
quem precisa do dado depois lê daqui sem tocar na rede.

Existe porque a rota de capabilities da deliberação roda em polling de
2s — chamar `list_models()` ali seria uma requisição a cada dois
segundos, por participante. Aqui o dado vem de graça da descoberta que
já acontece quando o usuário abre o navegador de modelos.

Cache vazio devolve `None`, não `False`: "ainda não descobrimos" é
diferente de "o modelo não tem". A UI mostra os dois de forma distinta.
"""

import threading
from typing import Dict, List, Optional, Tuple

_lock = threading.Lock()
_capabilities: Dict[Tuple[str, str], List[str]] = {}
_connection_capabilities: Dict[Tuple[str, str], List[str]] = {}


def update(kind: str, model_id: str, capabilities: Optional[List[str]]) -> None:
    if not model_id:
        return
    with _lock:
        _capabilities[(kind or "", model_id)] = [c.lower() for c in (capabilities or [])]


def update_connection(provider_name: str, model_id: str, capabilities: Optional[List[str]]) -> None:
    if not provider_name or not model_id:
        return
    with _lock:
        _connection_capabilities[(provider_name, model_id)] = [c.lower() for c in (capabilities or [])]


def get(kind: str, model_id: str) -> Optional[List[str]]:
    with _lock:
        return _capabilities.get((kind or "", model_id or ""))


def get_connection(provider_name: str, model_id: str) -> Optional[List[str]]:
    with _lock:
        return _connection_capabilities.get((provider_name or "", model_id or ""))


def supports_connection(provider_name: str, model_id: str, capability: str) -> Optional[bool]:
    caps = get_connection(provider_name, model_id)
    if caps is None:
        return None
    return capability.lower() in caps


def supports(kind: str, model_id: str, capability: str) -> Optional[bool]:
    """`None` = não descoberto ainda; a UI não pode dizer "não tem"."""
    caps = get(kind, model_id)
    if caps is None:
        return None
    return capability.lower() in caps


def invalidate_connection(provider_name: str) -> None:
    with _lock:
        stale = [key for key in _connection_capabilities if key[0] == provider_name]
        for key in stale:
            _connection_capabilities.pop(key, None)

