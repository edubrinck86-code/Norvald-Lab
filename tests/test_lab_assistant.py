"""An incident chat may explain and propose, but spending requires review and consent."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry

BAD = 'Resposta incompleta sem bloco.'
GOOD = 'Resposta ajustada\n<<CONTRIBUTION>>\n' + json.dumps({
    'knowledge': [{'local_id': 'k1', 'type': 'claim', 'content': 'Argumento preservado'}],
    'relations': []}) + '\n<<END_CONTRIBUTION>>'


class StubProvider(LLMProvider):
    def __init__(self, content):
        self.content, self.requests = content, []

    async def execute(self, request, model):
        self.requests.append((request, model))
        return ExecutionResult(content=self.content, tokens=22, duration_seconds=0,
                               provider='openrouter', model=model)

    async def list_models(self):
        return []


def registry(spec, provider, *, name):
    instance = AgentRegistry()
    instance.register_provider(name, provider, kind='openrouter')
    for p in spec['participants']:
        instance.register_agent(p['id'], name, p['model'])
    return instance


async def source(root):
    spec = demo_spec('assistant-origin')
    spec['mode'] = 'live'
    spec['providers'] = {'router': {'kind': 'openrouter'}}
    for idx, p in enumerate(spec['participants']):
        p.update(provider='router', model='lab-participant', sampling={'max_tokens': 64 + idx})
    runner = ExperimentRunner(root)
    provider = StubProvider(BAD)
    await runner.run(runner.prepare(spec), registry=registry(spec, provider, name='router'),
                     allow_live=True, monitor_capacity=False)


def settle(client):
    async def wait():
        await asyncio.gather(*list(client.app.state.adjustment_jobs.values()))
    client.portal.call(wait)


@pytest.mark.asyncio
async def test_assistant_chat_planned_once_and_raw_integrity(tmp_path, monkeypatch):
    await source(tmp_path)
    originals = {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
    operator = StubProvider('Falta o bloco CONTRIBUTION; conferir prévia antes de corrigir.')
    adjusted = StubProvider(GOOD)
    monkeypatch.setattr('norvald_lab.lab_assistant.build_registry',
                        lambda spec, **kw: registry(spec, operator, name='operator'))
    monkeypatch.setattr('norvald_lab.adjustments.build_registry',
                        lambda spec, **kw: registry(spec, adjusted, name='router'))
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        assert client.post('/api/experiments/assistant-origin/criteria/reconcile').status_code == 200
        issue = next(item for item in client.get('/api/criteria/incidents').json()
                     if item['criterion_id'] == 'arof.contribution.fully_valid')
        base = '/api/assistant/incidents/' + issue['id']
        assert client.get(base + '/conversation').json()['messages'] == []
        assert client.post(base + '/message', json={'text': 'Por que falhou?'}).status_code == 422
        assert client.put('/api/assistant/settings', json={
            'kind': 'openrouter', 'model': 'operator-chosen'}).status_code == 200
        assert operator.requests == []
        spoken = client.post(base + '/message', json={'text': 'Por que falhou?'})
        assert spoken.status_code == 200
        assert 'CONTRIBUTION' in spoken.json()['answer']
        assert len(spoken.json()['messages']) == 2
        request, model = operator.requests[0]
        assert model == 'operator-chosen' and request.allow_tools
        assert {tool.name for tool in request.tools} == {
            'list_operations', 'describe_operation', 'call_operation'}
        assert issue['criterion_id'] in request.context.working_context
        assert operator.requests[0][0].agent_id == 'lab-assistant'
        assert client.get(base + '/conversation').json()['messages'] == spoken.json()['messages']

        planned = client.post(base + '/adjustment/plan',
                              json={'instruction': 'Conferir o formato', 'max_tokens': 1500})
        assert planned.status_code == 200, planned.text
        proposal = planned.json()
        plan_id = proposal['plan']['id']
        assert proposal['requires_approval'] is False
        assert proposal['plan']['status'] == 'planned'
        assert 'Conferir o formato' in proposal['preview']['request']['instructions']
        assert adjusted.requests == []
        assert client.post('/api/assistant/plans/' + plan_id + '/execute',
                           json={}, headers={'Origin': 'https://other.invalid'}).status_code == 403
        accepted = client.post('/api/assistant/plans/' + plan_id + '/execute', json={})
        assert accepted.status_code == 202, accepted.text
        assert accepted.json()['new_execution'] is True
        assert not accepted.json()['result']['independent_sample']
        settle(client)
        assert len(adjusted.requests) == 1
        duplicate = client.post('/api/assistant/plans/' + plan_id + '/execute', json={})
        assert duplicate.status_code == 202
        assert duplicate.json()['new_execution'] is False
        assert len(adjusted.requests) == 1
        fresh = client.get('/api/criteria/incidents/' + issue['id']).json()
        assert fresh['recovery']['original_still_unmet']
        assert any(item['criterion_status'] == 'met_in_adjustment'
                   for item in fresh['recovery']['revalidations'])
        assert 'assistant.adjustment_requested' in [step['event'] for step in fresh['history']]
        assert originals == {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
        assert verify_experiment(tmp_path, 'assistant-origin')['valid']
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        assert len(client.get(base + '/conversation').json()['messages']) == 2


@pytest.mark.asyncio
async def test_assistant_refuses_spend_when_disabled_or_untrusted(tmp_path):
    await source(tmp_path)
    with TestClient(create_app(tmp_path)) as client:
        client.post('/api/experiments/assistant-origin/criteria/reconcile')
        issue = client.get('/api/criteria/incidents').json()[0]
        base = '/api/assistant/incidents/' + issue['id']
        assert client.post(base + '/message', json={'text': 'oi'}).status_code == 403
        proposal = client.post(base + '/adjustment/plan', json={})
        assert proposal.status_code == 200  # Planning stays available without live calls.
        assert client.post('/api/assistant/plans/' + proposal.json()['plan']['id'] + '/execute',
                           json={}).status_code == 403
        assert client.put('/api/assistant/settings', json={'kind': 'invalid', 'model': 'm'}).status_code == 422
        assert client.get('/api/assistant/settings', headers={'Origin': 'https://elsewhere.invalid'}).status_code == 403
        assert client.get(base + '/conversation', headers={'Origin': 'https://elsewhere.invalid'}).status_code == 403
        assert not (tmp_path / 'observer' / 'lab_assistant.sqlite3').exists()


@pytest.mark.asyncio
async def test_assistant_can_read_catalogue_without_mutating_experiment(tmp_path, monkeypatch):
    from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall

    await source(tmp_path)
    originals = {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}

    class ToolProvider(StubProvider):
        async def execute(self, request, model):
            self.requests.append((request, model))
            if not request.tool_exchanges:
                return ExecutionResult(content='', tokens=3, duration_seconds=0,
                                       provider='openrouter', model=model,
                                       tool_calls=[ToolCall(call_id='t1',
                                           name='list_operations', arguments={})])
            exchange = request.tool_exchanges[0]
            assert exchange.results[0].is_error is False
            assert 'lab.experiments.list' in exchange.results[0].content
            assert 'lab.experiment.start' not in exchange.results[0].content
            return ExecutionResult(content='As consultas disponíveis estão listadas.',
                                   tokens=5, duration_seconds=0,
                                   provider='openrouter', model=model)

    operator = ToolProvider('unused')
    monkeypatch.setattr('norvald_lab.lab_assistant.build_registry',
                        lambda spec, **kw: registry(spec, operator, name='operator'))
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        client.post('/api/experiments/assistant-origin/criteria/reconcile')
        issue = client.get('/api/criteria/incidents').json()[0]
        assert client.put('/api/assistant/settings', json={
            'kind': 'openrouter', 'model': 'operator-chosen'}).status_code == 200
        response = client.post('/api/assistant/incidents/' + issue['id'] + '/message',
                               json={'text': 'Quais consultas você tem?'})
        assert response.status_code == 200, response.text
        assert len(operator.requests) == 2
        assert operator.requests[0][0].allow_tools
        assert len(operator.requests[1][0].tool_exchanges) == 1
        assert len(client.get('/api/assistant/incidents/' + issue['id'] + '/conversation').json()['messages']) == 2
    assert originals == {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}


@pytest.mark.asyncio
async def test_repeated_model_tools_trigger_emergency_without_quota(tmp_path, monkeypatch):
    from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall

    await source(tmp_path)

    class RepeatingProvider(StubProvider):
        async def execute(self, request, model):
            self.requests.append((request, model))
            return ExecutionResult(content='', tokens=2, duration_seconds=0,
                                   provider='openrouter', model=model,
                                   tool_calls=[ToolCall(call_id='t' + str(len(self.requests)),
                                       name='list_operations', arguments={})])

    operator = RepeatingProvider('unused')
    monkeypatch.setattr('norvald_lab.lab_assistant.build_registry',
                        lambda spec, **kw: registry(spec, operator, name='operator'))
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        client.post('/api/experiments/assistant-origin/criteria/reconcile')
        issue = client.get('/api/criteria/incidents').json()[0]
        client.put('/api/assistant/settings', json={
            'kind': 'openrouter', 'model': 'operator-chosen'})
        response = client.post('/api/assistant/incidents/' + issue['id'] + '/message',
                               json={'text': 'Verifique o catálogo.'})
        assert response.status_code in {423, 502}
        assert client.get('/api/assistant/emergency').json()['stopped'] is True
        assert len(operator.requests) == 4
        assert client.post('/api/assistant/emergency/resume', json={}).json()['stopped'] is False
