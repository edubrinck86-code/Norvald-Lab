"""reasoning_effort "default" (11/11/2026, preparação da coleta do Δ_herd).

O TESE-002 §3 pede o raciocínio no padrão de cada provider, registrado.
"off" não servia: no OpenRouter não envia nada, mas no Mistral e no Cohere
vira "none" e desliga o raciocínio, deixando o painel desigual.
"""

from types import SimpleNamespace

import pytest

from norvald_lab.config import validate_spec
from norvald_lab.vendor.norvald_execution.contracts.sampling import SamplingParams, resolve_sampling
from norvald_lab.vendor.norvald_execution.providers.openai_compatible_provider import OpenAICompatibleProvider
from test_lab import demo_spec

REASONING_KEYS = {"reasoning", "reasoning_effort", "thinking"}


@pytest.mark.parametrize("kind", ["openrouter", "mistral", "cohere", "zai", "openai"])
def test_default_sends_no_reasoning_field(kind):
    provider = OpenAICompatibleProvider("https://example.invalid/v1", "chave-de-teste", provider_label=kind)
    payload = {}
    provider._apply_reasoning(payload, SimpleNamespace(reasoning_effort="default"), "glm-5.3" if kind == "zai" else "modelo")
    assert not REASONING_KEYS & set(payload)


def test_off_is_not_uniform_which_is_why_default_exists():
    sent = {}
    for kind in ("openrouter", "mistral", "cohere"):
        payload = {}
        OpenAICompatibleProvider("https://example.invalid/v1", "chave-de-teste", provider_label=kind)._apply_reasoning(payload, SimpleNamespace(reasoning_effort="off"), "modelo")
        sent[kind] = payload
    assert sent["openrouter"] == {}
    assert sent["mistral"] == {"reasoning_effort": "none"}
    assert sent["cohere"] == {"reasoning_effort": "none"}


def test_default_keeps_requested_sampling():
    resolved = resolve_sampling(SamplingParams(temperature=0.7, top_p=1.0, max_tokens=800), provider_kind="mistral", model="mistral-small-2603", reasoning_effort="default")
    assert (resolved.temperature, resolved.top_p, resolved.max_tokens) == (0.7, 1.0, 800)


def test_spec_accepts_default():
    spec = demo_spec("b1")
    for participant in spec["participants"]:
        participant["reasoning_effort"] = "default"
    validate_spec(spec)
