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
