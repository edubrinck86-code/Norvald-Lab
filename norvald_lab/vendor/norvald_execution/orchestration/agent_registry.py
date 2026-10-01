from dataclasses import dataclass
from typing import Dict, Tuple

from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider


@dataclass
class AgentBinding:
    provider_name: str
    model: str


class AgentRegistry:
    """Mapeia agent_id -> (provider, modelo) e nome de provider -> instância.

    Cumpre o papel de "AgentRegistry" e "ProviderRegistry" numa única
    estrutura: são a mesma tabela de resolução vista por dois ângulos
    (por agente e por provider), então mantê-las juntas evita duas
    classes fazendo a mesma coisa.
    """

    def __init__(self) -> None:
        self._bindings: Dict[str, AgentBinding] = {}
        self._providers: Dict[str, LLMProvider] = {}
        self._provider_kinds: Dict[str, str] = {}

    def register_provider(self, provider_name: str, provider: LLMProvider, kind: str | None = None) -> None:
        self._providers[provider_name] = provider
        self._provider_kinds[provider_name] = (kind or getattr(provider, "kind", "") or "").strip()

    def unregister_provider(self, provider_name: str) -> None:
        self._providers.pop(provider_name, None)
        self._provider_kinds.pop(provider_name, None)
        stale_agents = [
            agent_id
            for agent_id, binding in self._bindings.items()
            if binding.provider_name == provider_name
        ]
        for agent_id in stale_agents:
            self._bindings.pop(agent_id, None)

    def provider_names(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())

    def get_provider(self, provider_name: str) -> LLMProvider:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Provider '{provider_name}' não registrado.")
        return provider

    def register_agent(self, agent_id: str, provider_name: str, model: str) -> None:
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' não registrado.")
        self._bindings[agent_id] = AgentBinding(provider_name=provider_name, model=model)

    def resolve(self, agent_id: str) -> Tuple[LLMProvider, str]:
        binding = self._bindings.get(agent_id)
        if binding is None:
            raise ValueError(f"Agente '{agent_id}' não registrado.")
        provider = self._providers[binding.provider_name]
        return provider, binding.model

    def provider_kind_for(self, agent_id: str) -> str:
        """Família do provider ligado a este agente.

        A política de amostragem depende da família (a Anthropic recusa
        temperatura junto de top_p; a OpenAI aceita), e o nome da
        conexão é escolhido pelo usuário — não serve para inferir isso.
        """
        binding = self._bindings.get(agent_id)
        if binding is None:
            return ""
        return self._provider_kinds.get(binding.provider_name, "")

    def provider_name_for(self, agent_id: str) -> str:
        binding = self._bindings.get(agent_id)
        if binding is None:
            raise ValueError(f"Agente '{agent_id}' não registrado.")
        return binding.provider_name

