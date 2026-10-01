from typing import List, Optional, Tuple
import re

from norvald_lab.vendor.norvald_execution.contracts.provider_kinds import OPENAI_COMPATIBLE_CONFIG, SUPPORTED_KINDS
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.contracts.provider_model_profiles import canonical_provider_kind
from norvald_lab.vendor.norvald_execution.providers.anthropic_provider import AnthropicProvider
from norvald_lab.vendor.norvald_execution.providers.gemini_provider import GeminiProvider
from norvald_lab.vendor.norvald_execution.providers.ollama_provider import OllamaProvider
from norvald_lab.vendor.norvald_execution.providers.openai_compatible_provider import OpenAICompatibleProvider


def build_provider(kind: str, credential: str, base_url: Optional[str] = None) -> LLMProvider:
    """`credential` é a API key para providers autenticados (anthropic,
    gemini, openai, openrouter) ou a base_url do servidor para providers
    locais sem chave (ollama).

    `base_url` explícito ignora o catálogo estático por completo — é o
    caminho para o usuário cadastrar qualquer API OpenAI-compatible nova
    (Eduardo, 2026-09-14: "se eu tiver uma 100 API eu vou ter que mexer
    no código toda vez") sem editar OPENAI_COMPATIBLE_CONFIG nem
    reiniciar o backend. `kind` vira só rótulo/nome de roteamento nesse
    caso — nunca precisa estar em SUPPORTED_KINDS. Quando `base_url` não
    é passado, o comportamento é idêntico ao de antes (kind precisa
    estar num dos catálogos conhecidos).
    """
    raw_kind = (kind or "").strip().lower()
    canonical_kind = canonical_provider_kind(raw_kind)
    if base_url:
        return OpenAICompatibleProvider(
            base_url,
            credential,
            provider_label=raw_kind or canonical_kind,
            auth_check_path=None,
        )
    if canonical_kind == "anthropic":
        return AnthropicProvider(credential)
    if canonical_kind == "gemini":
        return GeminiProvider(credential)
    if canonical_kind == "ollama":
        return OllamaProvider(credential)

    # O modo/produto pode ter endpoint próprio (ex.: zai-coding) mesmo
    # compartilhando a mesma família de metadata/runtime.
    config_kind = raw_kind if raw_kind in OPENAI_COMPATIBLE_CONFIG else canonical_kind
    if config_kind in OPENAI_COMPATIBLE_CONFIG:
        cfg = OPENAI_COMPATIBLE_CONFIG[config_kind]
        return OpenAICompatibleProvider(
            cfg["base_url"],
            credential,
            provider_label=raw_kind or canonical_kind,
            auth_check_path=cfg["auth_check_path"],
        )
    raise ValueError(f"Kind de provider não suportado: '{kind}'.")


_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


async def detect_provider(credential: str) -> Optional[Tuple[str, LLMProvider, List[ModelInfo]]]:
    """Identifica automaticamente qual provider está por trás de uma
    credencial, testando contra os kinds marcados `auto_detect_safe` no
    catálogo (ver provider_kinds.py) — não todos os suportados.

    Achado em produção, 2026-09-14: `test_connection()` sem
    `auth_check_path` próprio cai no fallback padrão (list_models() não
    lançar erro = sucesso) — fraco o bastante para alguns providers
    (confirmado para NVIDIA, cujo /v1/models não valida a chave, só
    /v1/chat/completions valida) aceitarem QUALQUER credencial, de
    qualquer outro provider. Testar esses contra o auto-detect
    contaminava a detecção de outras conexões (Eduardo: cadastrar Cohere
    fazia aparecer Nvidia e Z.AI). `auto_detect_safe=False` continua
    disponível via kind explícito (dropdown manual ou URL customizada)
    — só sai do palpite automático até alguém verificar de verdade que
    o endpoint de listagem daquele provider rejeita credencial errada.

    Uma URL (http(s)://...) só é testada contra Ollama, o único
    provider sem autenticação por chave. Qualquer outra coisa passa por
    todos os kinds seguros, um de cada vez, até um aceitar a credencial
    de fato. Retorna None se nenhum aceitar — quem chama deve então
    pedir ao usuário para escolher manualmente.
    """
    credential = credential.strip()
    if _URL_PATTERN.match(credential):
        candidates = ["ollama"]
    else:
        unsafe = {k for k, cfg in OPENAI_COMPATIBLE_CONFIG.items() if not cfg["auto_detect_safe"]}
        candidates = [k for k in SUPPORTED_KINDS if k != "ollama" and k not in unsafe]
    for kind in candidates:
        provider = build_provider(kind, credential)
        try:
            if not await provider.test_connection():
                continue
        except Exception:
            continue
        try:
            models = await provider.list_models()
        except Exception:
            models = []
        return kind, provider, models
    return None

