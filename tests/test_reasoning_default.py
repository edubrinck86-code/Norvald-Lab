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


def test_reasoning_drops_sampling_unless_the_spec_keeps_it():
    # 11/11/2026: os quatro modelos do painel aceitam temperatura com raciocínio
    # ligado; o TESE-002 §3 exige a mesma temperatura em todos.
    params = SamplingParams(temperature=0.7, top_p=1.0, max_tokens=4096)
    dropped = resolve_sampling(params, provider_kind="openrouter", model="qwen/qwen3.8-27b", reasoning_effort="medium")
    kept = resolve_sampling(params, provider_kind="openrouter", model="qwen/qwen3.8-27b", reasoning_effort="medium", keep_sampling_with_reasoning=True)
    assert (dropped.temperature, dropped.top_p) == (None, None)
    assert (kept.temperature, kept.top_p, kept.max_tokens) == (0.7, 1.0, 4096)


def test_spec_flag_reaches_the_request(tmp_path):
    import json
    from norvald_lab.runner import ExperimentRunner
    spec = demo_spec("b1")
    for participant in spec["participants"]:
        participant.update(reasoning_effort="medium", sampling_with_reasoning=True, sampling={"temperature": 0.7, "top_p": 1.0})
    prepared = ExperimentRunner(tmp_path).prepare(spec)
    assert all(json.loads(r)["sampling"]["temperature"] == 0.7 for r in prepared.requests_json)
    spec["participants"][0]["sampling_with_reasoning"] = "sim"
    with pytest.raises(ValueError, match="sampling_with_reasoning"):
        validate_spec(spec)
