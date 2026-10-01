"""Fumaça do C2: os quatro providers se constroem pelo kind, respeitam o
contrato e continuam sem saber que existe um Studio."""
import pytest

from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.contracts.provider_kinds import SUPPORTED_KINDS
from norvald_lab.vendor.norvald_execution.providers.anthropic_provider import AnthropicProvider
from norvald_lab.vendor.norvald_execution.providers.gemini_provider import GeminiProvider
from norvald_lab.vendor.norvald_execution.providers.llm_providers import build_provider
from norvald_lab.vendor.norvald_execution.providers.ollama_provider import OllamaProvider
from norvald_lab.vendor.norvald_execution.providers.openai_compatible_provider import OpenAICompatibleProvider


@pytest.mark.parametrize("kind,classe", [
    ("anthropic", AnthropicProvider),
    ("gemini", GeminiProvider),
    ("ollama", OllamaProvider),
])
def test_kind_conhecido_constroi_o_provider(kind, classe):
    provider = build_provider(kind, "credencial-qualquer")
    assert isinstance(provider, classe)
    assert isinstance(provider, LLMProvider)


def test_kind_desconhecido_e_recusado():
    with pytest.raises(ValueError):
        build_provider("provider-que-nao-existe", "credencial")


def test_kinds_suportados_cobrem_os_providers_presentes():
    assert {"anthropic", "gemini", "ollama"} <= set(SUPPORTED_KINDS)


def test_compativel_com_openai_aceita_base_url_propria():
    provider = build_provider("openai", "credencial", base_url="https://exemplo.invalido/v1")
    assert isinstance(provider, OpenAICompatibleProvider)


def test_todo_provider_expoe_execucao():
    for classe in (AnthropicProvider, GeminiProvider, OllamaProvider, OpenAICompatibleProvider):
        assert hasattr(classe, "execute")

