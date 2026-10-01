import json

import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from test_adjustments import source


def test_production_starts_clean_and_cannot_execute_demonstration(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        template = client.get('/api/experiment-template').json()
        assert template['mode'] == 'live' and template['documents'] == []
        assert template['working_context']['items'] == [] and not template['task']['objective']
        assert all(not p['model'] for p in template['participants'])
        assert client.get('/api/demo-template').status_code == 404
        assert client.post('/api/demo').status_code == 404
        assert client.post('/api/experiments', json=demo_spec('forbidden')).status_code == 422
        assert client.get('/api/experiments').json() == []


@pytest.mark.asyncio
async def test_selection_exclusion_restore_and_edit_preserve_raw_and_notes(tmp_path):
    observed = await source(tmp_path)
    original = {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
    with TestClient(create_app(tmp_path)) as client:
        anchor = {'experiment_id': 'source', 'observation_id': observed['records'][0]['observation_id'], 'excerpt': 'Resposta incompleta'}
        assert client.post('/api/notes', json={'title': 'Minha nota', 'content': 'Observação', 'anchor': anchor}).status_code == 201
        edited = client.get('/api/experiments/source/editable-copy').json()
        assert edited['experiment_id'] != 'source'
        assert edited['condition']['exposure'] == 'blind' and 'prior_experiment' not in edited['condition']
        assert edited['participants'] == observed['spec']['participants']
        assert edited['documents'] == observed['spec']['documents'] and edited['task'] == observed['spec']['task']
        assert client.delete('/api/experiments/source').status_code == 204
        assert client.get('/api/experiments').json() == []
        assert client.get('/api/experiments?include_deleted=true').json()[0]['deleted']
        assert client.get('/api/notes').json()[0]['anchor'] == anchor
        assert client.get('/api/experiments/source/observe').json()['integrity']['valid']
        assert client.post('/api/experiments/source/restore').status_code == 204
        assert len(client.get('/api/experiments').json()) == 1
        assert client.delete('/api/experiments/absent').status_code == 404
    assert original == {str(p): p.read_bytes() for p in (tmp_path / 'experiments').rglob('*') if p.is_file()}
