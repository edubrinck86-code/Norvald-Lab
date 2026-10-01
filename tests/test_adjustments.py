import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from norvald_lab.adjustments import AdjustmentStore
from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry

VALID = 'Resposta ajustada\n<<CONTRIBUTION>>\n' + json.dumps({'knowledge': [{'local_id': 'k1', 'type': 'claim', 'content': 'Argumento preservado'}], 'relations': []}) + '\n<<END_CONTRIBUTION>>'
BAD = 'Resposta incompleta\n<<CONTRIBUTION>>\n{"knowledge":['


class FakeProvider(LLMProvider):
    def __init__(self):
        self.calls = []
    async def list_models(self):
        return []
    async def execute(self, request, model):
        self.calls.append(request)
        content = BAD if request.sampling.max_tokens == 64 else VALID
        return ExecutionResult(content=content, tokens=10, duration_seconds=0, provider='openrouter', model=model)


def registry_for(spec, provider):
    registry = AgentRegistry()
    registry.register_provider('router', provider, kind='openrouter')
    for p in spec['participants']:
        registry.register_agent(p['id'], 'router', p['model'])
    return registry


async def source(root):
    spec = demo_spec('source')
    spec['mode'] = 'live'
    spec['providers'] = {'router': {'kind': 'openrouter'}}
    for i, p in enumerate(spec['participants']):
        p.update(provider='router', model='test-model', sampling={'max_tokens': 64 if i == 0 else 128})
    runner = ExperimentRunner(root)
    await runner.run(runner.prepare(spec), registry=registry_for(spec, FakeProvider()), allow_live=True, monitor_capacity=False)
    from norvald_lab.observer import snapshot
    return snapshot(root, 'source', 'complete')


@pytest.mark.asyncio
async def test_adjustment_calls_only_one_participant_and_preserves_original_and_pairs(tmp_path, monkeypatch):
    observed = await source(tmp_path)
    record = observed['records'][0]
    original = {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
    provider = FakeProvider()
    monkeypatch.setattr('norvald_lab.adjustments.build_registry', lambda spec, **kw: registry_for(spec, provider))
    store = AdjustmentStore(tmp_path)
    saved, spec = store.prepare('source', {'observation_id': record['observation_id'], 'instruction': 'Feche o JSON e preserve os argumentos', 'max_tokens': 2048})
    await store.run(saved, spec)
    assert len(provider.calls) == 1
    request = provider.calls[0]
    assert request.agent_id == record['participant_id']
    assert BAD in request.user_message and 'Feche o JSON' in request.instructions
    assert request.sampling.max_tokens == 2048
    assert request.context.working_context == observed['requests'][0]['context']['working_context']
    adjusted = store.list('source')[0]
    assert adjusted['status'] == 'complete' and adjusted['check']['usable']
    assert not adjusted['independent_sample']
    assert adjusted['record']['result']['content'] == VALID
    saved2, spec2 = store.prepare('source', {'observation_id': record['observation_id'], 'instruction': 'Desenvolva o argumento', 'parent_id': saved['id'], 'max_tokens': 3000})
    await store.run(saved2, spec2)
    assert len(provider.calls) == 2 and VALID in provider.calls[1].user_message
    assert saved2['diagnostic']['code'] == 'usable'
    assert 'Código: usable.' in provider.calls[1].instructions
    assert saved['instruction'] in provider.calls[1].instructions
    assert original == {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
    assert verify_experiment(tmp_path, 'source')['valid']
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        refused = client.post('/api/derive', json={'source_id': 'source', 'experiment_id': 'derived', 'exposure': 'exposed'})
        assert refused.status_code == 422  # repair is not silently treated as a blind sample
    # A damaged adjustment is blocked independently of the valid source.
    (store.directory('source') / saved['id'] / 'result.json').write_text('{}')
    assert next(a for a in store.list('source') if a['id'] == saved['id'])['status'] == 'altered'
    assert verify_experiment(tmp_path, 'source')['valid']


@pytest.mark.asyncio
async def test_adjustment_api_authorization_failure_recovery_and_restart(tmp_path, monkeypatch):
    observed = await source(tmp_path)
    obsid = observed['records'][0]['observation_id']
    provider = FakeProvider()
    monkeypatch.setattr('norvald_lab.adjustments.build_registry', lambda spec, **kw: registry_for(spec, provider))
    with TestClient(create_app(tmp_path)) as client:
        assert client.post('/api/adjustments/source', json={'observation_id': obsid, 'instruction': 'Corrija'}).status_code == 403
        client.put('/api/settings/execution', json={'live_enabled': True})
        assert client.post('/api/adjustments/source', headers={'origin': 'https://elsewhere.invalid'}, json={'observation_id': obsid, 'instruction': 'Corrija'}).status_code == 403
        for invalid in [{'instruction': ''}, {'instruction': 'Corrija', 'max_tokens': 0}, {'instruction': 'Corrija', 'max_tokens': True}, {'instruction': 'Corrija', 'observation_id': 'ausente'}, {'instruction': 'Corrija', 'parent_id': '../bad'}]:
            assert client.post('/api/adjustments/source', json={'observation_id': obsid} | invalid).status_code == 422
        # First explicit attempt still fails validation; a new explicit attempt can fix it.
        result = client.post('/api/adjustments/source', json={'observation_id': obsid, 'instruction': 'Corrija', 'max_tokens': 64})
        assert result.status_code == 202
        async def wait():
            await asyncio.gather(*list(client.app.state.adjustment_jobs.values()))
        client.portal.call(wait)
        attempt = client.get('/api/adjustments/source').json()[0]
        assert attempt['status'] == 'complete' and not attempt['check']['usable']
        assert client.post('/api/adjustments/source', json={'observation_id': obsid, 'instruction': 'Corrija com mais espaço', 'max_tokens': 2000, 'parent_id': attempt['id']}).status_code == 202
        client.portal.call(wait)
        assert len(provider.calls) == 2
    with TestClient(create_app(tmp_path)) as client:
        attempts = client.get('/api/adjustments/source').json()
        assert len(attempts) == 2 and any(a['check']['usable'] for a in attempts)
        assert client.get('/api/experiments/source/verify').json()['valid']


@pytest.mark.asyncio
async def test_failed_transport_is_saved_and_secret_redacted(tmp_path, monkeypatch):
    observed = await source(tmp_path)
    provider = FakeProvider()
    provider._api_key = 'secret-only-for-test'
    async def fail(request, model):
        raise ValueError('Falha com ' + provider._api_key)
    provider.execute = fail
    monkeypatch.setattr('norvald_lab.adjustments.build_registry', lambda spec, **kw: registry_for(spec, provider))
    store = AdjustmentStore(tmp_path)
    saved, spec = store.prepare('source', {'observation_id': observed['records'][0]['observation_id'], 'instruction': 'Corrija'})
    await store.run(saved, spec)
    result = store.list('source')[0]
    assert result['status'] == 'failed' and '[API_KEY_REDACTED]' in result['error']
    assert provider._api_key not in json.dumps(result)


@pytest.mark.asyncio
async def test_diagnosis_preview_is_read_only_and_reaches_actual_provider_payload(tmp_path, monkeypatch):
    import httpx
    from norvald_lab.settings import LocalSettings
    from norvald_lab.vendor.norvald_execution.providers import openai_compatible_provider as transport
    observed = await source(tmp_path)
    obsid = observed['records'][0]['observation_id']
    calls = []
    def handler(request):
        if request.url.path.endswith('/chat/completions'):
            calls.append(json.loads(request.content))
            return httpx.Response(200, json={'id': 'test-adjustment', 'choices': [{'message': {'content': VALID}}], 'usage': {'prompt_tokens': 12, 'completion_tokens': 6}})
        return httpx.Response(200, json={'data': []})
    monkeypatch.setattr(transport, 'build_client', lambda **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False))
    LocalSettings(tmp_path).save_connection('openrouter', {'api_key': 'fake-key'})
    payload = {'observation_id': obsid, 'instruction': 'Ajuste isto', 'max_tokens': 2048}
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        preview = client.post('/api/adjustments/source/preview', json=payload)
        assert preview.status_code == 200
        saved = preview.json()
        assert saved['diagnostic']['code'] == 'unclosed_block'
        assert BAD in saved['request']['user_message']
        assert 'não foi encontrado' in saved['request']['instructions']
        assert 'O diagnóstico não comprova' in saved['request']['instructions']
        assert not (tmp_path / 'observer/adjustments').exists() and not calls
        assert client.post('/api/adjustments/source', json=payload).status_code == 202
        async def wait():
            await asyncio.gather(*list(client.app.state.adjustment_jobs.values()))
        client.portal.call(wait)
        assert len(calls) == 1
        system = calls[0]['messages'][0]['content']
        if isinstance(system, list):
            system = '\n\n'.join(part['text'] for part in system)
        assert saved['request']['instructions'] in system
        assert saved['request']['shared_instructions'] in system
        assert saved['request']['wave_instructions'] in system
        assert calls[0]['messages'][1]['content'] == saved['request']['user_message']
        assert calls[0]['max_tokens'] == 2048
        assert saved['instruction'] in system
        assert client.get('/api/experiments/source/verify').json()['valid']


def test_diagnostic_identifies_json_location_missing_field_and_rejected_part():
    from norvald_lab.adjustment_prompt import adjustment_diagnostic, diagnostic_instructions
    from norvald_lab.domain.deliberation.working_context import WorkingContext
    request = {'context': {'working_context': json.dumps(WorkingContext().to_dict())}}
    def diagnose(content, error=None):
        return adjustment_diagnostic({'participant_id': 'p1', 'result': {'content': content}, 'error': error}, request)
    json_error = diagnose('<<CONTRIBUTION>>\n{"knowledge": [}\n<<END_CONTRIBUTION>>')
    assert json_error['code'] == 'invalid_json' and 'linha 1, coluna 16' in json_error['details'][0]
    schema = diagnose('<<CONTRIBUTION>>' + json.dumps({'knowledge': [{'type': 'claim', 'content': 'Argumento'}], 'relations': []}) + '<<END_CONTRIBUTION>>')
    assert 'knowledge[0].local_id: campo obrigatório ausente.' in schema['details']
    rejected = diagnose('<<CONTRIBUTION>>' + json.dumps({'knowledge': [{'local_id': 'k1', 'type': 'evidence', 'content': 'Argumento'}], 'relations': []}) + '<<END_CONTRIBUTION>>')
    text = diagnostic_instructions(rejected, previous_limit=64, new_limit=64)
    assert 'knowledge / k1: tipo semântico não declarável' in text
    assert 'Tipos declaráveis' in text and 'O limite de saída não foi aumentado' in text
    failure = diagnose('', {'type': 'TimeoutError', 'message': 'Tempo esgotado'})
    assert failure['code'] == 'execution_failed'
    assert 'Tempo esgotado' in diagnostic_instructions(failure, previous_limit=None, new_limit=2000)
