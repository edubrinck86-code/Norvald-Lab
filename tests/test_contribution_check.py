import json

import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.contribution_check import check_contribution
from norvald_lab.domain.deliberation.working_context import WorkingContext
from norvald_lab.runner import ExperimentRunner
from norvald_lab.runtime import DemoProvider
from norvald_lab.storage import verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry


def block(payload):
    return 'Texto literal\n<<CONTRIBUTION>>\n' + json.dumps(payload) + '\n<<END_CONTRIBUTION>>'


@pytest.mark.parametrize('content,code', [
    ('Resposta em prosa.', 'missing_block'),
    ('', 'empty_response'),
    ('Resposta\n<<CONTRIBUTION>>\n{"knowledge":[', 'unclosed_block'),
    ('<<CONTRIBUTION>>{invalid}<<END_CONTRIBUTION>>', 'invalid_json'),
    (block({'knowledge': [], 'relations': []}), 'empty_knowledge'),
    (block({'knowledge': 'claim', 'relations': []}), 'invalid_schema'),
    (block({'knowledge': [{'type': 'claim', 'content': 'Texto'}]}), 'invalid_schema'),
    (block({'knowledge': [{'local_id': 'k1', 'type': 'evidence', 'content': 'Texto'}]}), 'rejected_knowledge'),
])
def test_diagnostics_do_not_infer_or_repair_structure(content, code):
    result = check_contribution(content, 'p1', WorkingContext())
    assert not result['usable'] and result['code'] == code
    assert result['accepted_items'] == 0


def test_fenced_json_is_accepted_by_existing_parser_and_diagnostics():
    content = block({'knowledge': [{'local_id': 'k1', 'type': 'claim', 'content': 'Texto literal'}], 'relations': []})
    content = content.replace('<<CONTRIBUTION>>\n', '<<CONTRIBUTION>>\n```json\n').replace('\n<<END_CONTRIBUTION>>', '\n```\n<<END_CONTRIBUTION>>')
    check = check_contribution(content, 'p1', WorkingContext())
    assert check['usable'] and check['declared_items'] == check['accepted_items'] == 1


@pytest.mark.asyncio
async def test_origin_diagnostic_identifies_participant_and_repetition_without_modifying_dataset(tmp_path):
    class Mixed(DemoProvider):
        async def execute(self, request, model):
            if request.agent_id == 'analista-1':
                return await super().execute(request, model)
            content = 'Resposta natural preservada.' if request.agent_id == 'analista-2' else 'Texto\n<<CONTRIBUTION>>\n{"knowledge":['
            return ExecutionResult(content=content, tokens=0, duration_seconds=0, provider='demo', model=model)
    spec = demo_spec('source-format')
    spec['repetitions'] = 2
    registry = AgentRegistry()
    registry.register_provider('simulador', Mixed(), kind='demo')
    for p in spec['participants']:
        registry.register_agent(p['id'], 'simulador', p['model'])
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(spec), registry=registry, monitor_capacity=False)
    before = {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        observed = client.get('/api/experiments/source-format/observe').json()
        assert observed['status'] == 'complete' and observed['integrity']['valid']
        checks = observed['contribution_checks']
        assert len(checks) == 6
        assert {c['code'] for c in checks if c['participant_id'] == 'analista-2'} == {'missing_block'}
        assert {c['code'] for c in checks if c['participant_id'] == 'analista-3'} == {'unclosed_block'}
        assert {c['run_id'] for c in checks} == {'r0001', 'r0002'}
        assert all(c['usable'] for c in checks if c['participant_id'] == 'analista-1')
        refused = client.post('/api/derive', json={'source_id': 'source-format', 'experiment_id': 'derived-format', 'exposure': 'exposed'})
        assert refused.status_code == 422
        message = refused.json()['detail']
        assert 'Analista 2' in message and 'Analista 3' in message and 'repetição 1' in message
        assert 'CONTRIBUTION' in message and 'permanece salva' in message
    assert not (tmp_path / 'experiments/derived-format').exists()
    assert before == {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
    assert verify_experiment(tmp_path, 'source-format')['valid']
