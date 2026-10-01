import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.models import normalize_model
from norvald_lab.settings import LocalSettings, credential_env
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo
from norvald_lab.vendor.norvald_execution.providers import openai_compatible_provider as transport

KEY = 'LOCAL-TEST-CREDENTIAL-DO-NOT-PUBLISH'


def test_settings_persist_without_returning_secrets_and_bind_to_address(tmp_path, monkeypatch):
    store = LocalSettings(tmp_path)
    store.save_connection('openrouter', {'api_key': KEY})
    assert KEY not in json.dumps(store.public())
    assert store.path.stat().st_mode & 0o777 == 0o600
    assert store.directory.stat().st_mode & 0o777 == 0o700
    assert LocalSettings(tmp_path).resolve('openrouter') == KEY
    assert not store.resolve('openrouter', base_url='https://other.invalid/v1')
    monkeypatch.setenv('LEGACY_KEY', 'environment-key')
    assert store.resolve('openrouter', 'LEGACY_KEY') == 'environment-key'
    store.save_connection('openrouter', {'base_url': ''})
    assert store.resolve('openrouter') == KEY  # blank editor preserves existing key
    store.delete_key('openrouter')
    assert not store.resolve('openrouter')
    with pytest.raises(ValueError):
        store.save_connection('openai', {'base_url': 'https://user:pass@example.invalid/v1?key=abc'})


@pytest.mark.parametrize('metadata,expected', [
    ({}, (None, None, None)),
    ({'supported_parameters': ['tools', 'reasoning'], 'pricing': {'prompt': '0', 'completion': '0'}}, (True, True, True)),
    ({'supported_parameters': [], 'pricing': {'prompt': '0', 'completion': '0', 'request': '0.1'}}, (False, False, False)),
    ({'pricing': {'prompt': None, 'completion': '0'}}, (None, None, None)),
    ({'pricing': {'prompt': 'NaN', 'completion': '0'}}, (None, None, None)),
    ({'capabilities': {'thinking': {'supported': True}}}, (None, True, None)),
])
def test_capabilities_and_prices_are_only_declared(metadata, expected):
    model = normalize_model(ModelInfo('model', 'Model', raw_metadata=metadata), 'openrouter')
    assert (model['tools'], model['reasoning'], model['free']) == expected


def test_catalog_excludes_gemini_embeddings_and_marks_dynamic_router():
    m = normalize_model(ModelInfo('embedding', 'Embedding', raw_metadata={'supportedGenerationMethods': ['embedContent']}), 'gemini')
    assert not m['usable']
    m = normalize_model(ModelInfo('text', 'Text', raw_metadata={'supportedGenerationMethods': ['generateContent'], 'thinking': True}), 'gemini')
    assert m['usable'] and m['reasoning'] is True
    assert normalize_model(ModelInfo('openrouter/free', 'Free'), 'openrouter')['dynamic_router']
    assert normalize_model(ModelInfo('local', 'Local'), 'ollama')['free'] is None


def test_ui_saved_key_catalog_and_real_adapter_with_tools_without_external_requests(tmp_path, monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        assert request.headers['authorization'] == 'Bearer ' + KEY
        if request.url.path.endswith('/models'):
            return httpx.Response(200, json={'data': [{'id': 'mock/free', 'name': 'Mock gratuito', 'supported_parameters': ['tools', 'reasoning'], 'pricing': {'prompt': '0', 'completion': '0'}}]})
        if request.url.path.endswith('/key'):
            return httpx.Response(200, json={'data': {'label': 'mock'}})
        if request.url.path.endswith('/chat/completions'):
            payload = json.loads(request.content)
            assert payload['model'] == 'mock/free' and payload['reasoning']['effort'] == 'high'
            assert payload['tools']
            if not any(m['role'] == 'tool' for m in payload['messages']):
                message = {'content': '', 'tool_calls': [{'id': 'call-1', 'type': 'function', 'function': {'name': 'read_document', 'arguments': json.dumps({'document_id': 'texto-demo'})}}]}
            else:
                message = {'content': '## Registro observado\n\nResposta literal preservada.', 'reasoning': 'Trace disponibilizado pelo transporte simulado.'}
            return httpx.Response(200, json={'id': 'request-mock', 'choices': [{'message': message}], 'usage': {'prompt_tokens': 12, 'completion_tokens': 3}})
        raise AssertionError(str(request.url))
    monkeypatch.setattr(transport, 'build_client', lambda **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False))
    with TestClient(create_app(tmp_path)) as client:
        assert not client.get('/health').json()['live_enabled']
        response = client.put('/api/settings/connections/openrouter', json={'api_key': KEY})
        assert response.status_code == 200 and KEY not in response.text
        assert response.headers['cache-control'] == 'no-store'
        assert client.put('/api/settings/execution', json={'live_enabled': True}, headers={'Origin': 'https://other.invalid'}).status_code == 403
        assert client.put('/api/settings/execution', json={'live_enabled': True}).status_code == 200
        assert client.post('/api/settings/connections/openrouter/test').json()['ok']
        catalog = client.post('/api/models', json={'kind': 'openrouter'}).json()
        assert catalog['models'][0]['free'] and catalog['models'][0]['tools'] and catalog['models'][0]['reasoning']
        assert all(r.method == 'GET' for r in requests)  # no inference when configuring
        spec = demo_spec('stored-credential')
        spec['mode'] = 'live'
        spec['providers'] = {'simulador': {'kind': 'openrouter', 'credential_env': credential_env('openrouter')}}
        spec['condition'].update(tools='corpus', max_tool_calls=2, max_tool_iterations=3)
        for p in spec['participants']:
            p.update(model='mock/free', reasoning_effort='high')
        assert client.post('/api/experiments', json=spec).status_code == 202
        async def wait():
            await asyncio.gather(*set(client.app.state.jobs.values()))
        client.portal.call(wait)
        observed = client.get('/api/experiments/stored-credential/observe').json()
        assert observed['status'] == 'complete', observed
        assert observed['integrity']['valid'] and not observed['provisional']
        assert all(r['result']['reasoning'].startswith('Trace') for r in observed['records'])
        assert any(e['event'].startswith('tool.') for e in observed['events'])
        assert KEY not in json.dumps(observed)
        assert all(KEY not in p.read_text() for p in (tmp_path / 'experiments').rglob('*') if p.is_file())
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/health').json()['live_enabled']
        assert client.get('/api/settings').json()['connections'][0]['has_key']


@pytest.mark.asyncio
async def test_provider_error_secret_is_redacted_in_raw_events_and_result(tmp_path, monkeypatch):
    store = LocalSettings(tmp_path)
    store.save_connection('openrouter', {'api_key': KEY})
    def handler(request):
        store.delete_key('openrouter')  # the in-flight adapter still holds this key
        raise ValueError('Transport failure ?key=' + KEY + ' Bearer ' + KEY)
    monkeypatch.setattr(transport, 'build_client', lambda **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False))
    from norvald_lab.runner import ExperimentRunner
    runner = ExperimentRunner(tmp_path)
    spec = demo_spec('redacted-failure')
    spec['mode'] = 'live'
    spec['providers'] = {'simulador': {'kind': 'openrouter', 'credential_env': credential_env('openrouter')}}
    result = await runner.run(runner.prepare(spec), allow_live=True, monitor_capacity=False)
    assert result['status'] == 'incomplete'
    contents = '\n'.join(p.read_text() for p in (tmp_path / 'experiments').rglob('*') if p.is_file())
    assert KEY not in contents and '[API_KEY_REDACTED]' in contents
