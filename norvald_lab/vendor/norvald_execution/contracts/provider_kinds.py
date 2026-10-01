"""Catálogo estático dos tipos de Provider suportados.

Somente dados: nomes de kind, base_url e endpoint de validação de
credencial. Fica em `core` porque tanto a orquestração (que constrói os
Providers) quanto a configuração (que valida o kind gravado em Settings)
precisam do mesmo catálogo — mantê-lo em `orchestrator` criava o ciclo
infrastructure <-> orchestrator.
"""

from typing import Dict, Optional, TypedDict

# "kind" identifica QUAL API chamar. O NOME da conexão em StudioSettings
# continua livre - são coisas diferentes: kind = "com quem eu falo",
# nome = "como eu chamo essa conexão".
#
# Só existem classes de Provider separadas quando o protocolo HTTP em si
# é diferente (AnthropicProvider: auth própria e /v1/messages;
# GeminiProvider: chave via query param e formato contents/parts próprio;
# OllamaProvider: sem auth, endpoints locais). "openai" e "openrouter"
# falam o mesmo protocolo de execução (chat/completions + models, Bearer
# token) e por isso reaproveitam a mesma classe (OpenAICompatibleProvider),
# variando base_url e, quando necessário, o endpoint usado pra validar a
# credencial de verdade (ver auth_check_path abaixo e detect_provider).
#
# Cada Provider é responsável por descobrir seus próprios modelos via
# list_models(); o Studio nunca conhece uma lista fixa de modelos.


class _ProviderConfig(TypedDict):
    base_url: str
    auth_check_path: Optional[str]
    # Achado em produção, 2026-09-14: adicionei Cerebras/Mistral/NVIDIA
    # com auth_check_path=None assumindo "list_models() já autentica",
    # por analogia com xAI/Meta/OpenAI — sem testar nenhum deles de
    # verdade. Confirmado depois, no fórum oficial da própria NVIDIA,
    # que o /v1/models dela NÃO valida a chave (só /v1/chat/completions
    # valida) — exatamente o mesmo risco que o comentário de OpenRouter
    # logo abaixo já tinha identificado e resolvido corretamente, antes
    # de mim, com um auth_check_path real. Resultado: no auto-detect
    # (detect_provider), QUALQUER credencial de QUALQUER provider
    # "passava" como NVIDIA, contaminando a detecção de outras
    # conexões (relatado por Eduardo: cadastrar Cohere fazia aparecer
    # Nvidia e Z.AI).
    #
    # `auto_detect_safe=False` tira o kind da lista de candidatos do
    # auto-detect sem tirar o provider do catálogo — ele continua
    # funcionando normalmente quando o `kind` é escolhido explicitamente
    # (dropdown manual ou URL customizada). Só False para o que nunca
    # foi empiricamente verificado — não é suposição de que está
    # quebrado, é honestidade sobre não ter sido testado.
    auto_detect_safe: bool


OPENAI_COMPATIBLE_CONFIG: Dict[str, _ProviderConfig] = {
    # A OpenAI exige chave válida até pra listar modelos — comportamento
    # amplamente conhecido e testado por terceiros, não suposição minha.
    "openai": {"base_url": "https://api.openai.com/v1", "auth_check_path": None, "auto_detect_safe": True},
    # A OpenRouter expõe /models PUBLICAMENTE, sem checar a chave — se
    # usássemos list_models() pra validar, qualquer credencial (de
    # qualquer outro provider, ou lixo nenhum) "passaria" como
    # OpenRouter. /key é o endpoint documentado que exige um Bearer
    # válido e é o que usamos pra confirmar a credencial.
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "auth_check_path": "/key", "auto_detect_safe": True},
    # xAI (Grok): endpoint OpenAI-compatible — nunca testado
    # empiricamente se /v1/models valida a chave de verdade.
    "xai": {"base_url": "https://api.x.ai/v1", "auth_check_path": None, "auto_detect_safe": False},
    # Meta (Llama API): mesma ressalva — nunca testado empiricamente.
    "meta": {"base_url": "https://api.llama.com/compat/v1", "auth_check_path": None, "auto_detect_safe": False},
    # Cerebras: nunca testado empiricamente.
    "cerebras": {"base_url": "https://api.cerebras.ai/v1", "auth_check_path": None, "auto_detect_safe": False},
    # Mistral: nunca testado empiricamente.
    "mistral": {"base_url": "https://api.mistral.ai/v1", "auth_check_path": None, "auto_detect_safe": False},
    # Cohere oferece uma Compatibility API OpenAI-compatible. O catálogo
    # rico continua sendo o /v1/models nativo e é consultado pelo adapter
    # com a mesma chave, sem trocar o protocolo de execução.
    "cohere": {"base_url": "https://api.cohere.ai/compatibility/v1", "auth_check_path": None, "auto_detect_safe": False},
    # Z.AI oferece Chat Completions compatível com OpenAI em /api/paas/v4.
    # O catálogo OpenAI-compatible é enxuto; parâmetros documentados no
    # contrato são normalizados separadamente e identificados como tal.
    "zai": {"base_url": "https://api.z.ai/api/paas/v4", "auth_check_path": None, "auto_detect_safe": False},
    # Coding Plan usa um produto/quota diferente do endpoint geral.
    # Mantê-lo como kind separado evita que uma chave válida seja testada
    # eternamente no produto errado e retorne 1315/429.
    "zai-coding": {"base_url": "https://api.z.ai/api/coding/paas/v4", "auth_check_path": None, "auto_detect_safe": False},
    # NVIDIA NIM: CONFIRMADO que /v1/models não valida a chave (fórum
    # oficial da NVIDIA, "works for /v1/models but fails for chat") —
    # não é suspeita, é caso provado.
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "auth_check_path": None, "auto_detect_safe": False},
}

SUPPORTED_KINDS = ["anthropic", "gemini", "ollama", *sorted(OPENAI_COMPATIBLE_CONFIG)]

