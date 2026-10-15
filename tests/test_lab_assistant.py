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
        assert model == 'operator-chosen' and not request.allow_tools
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
