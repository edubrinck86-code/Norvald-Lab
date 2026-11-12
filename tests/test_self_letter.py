"""Controle B3L (12/11/2026): o participante vê só a opção que escolheu em B1.

Reproduz o controle de Hao et al. (2026, Tabela 30), que mostra a letra da
resposta anterior sem o raciocínio. Nenhum texto, fundamento ou confiança da
contribuição pode chegar ao prompt.
"""
import json

import pytest

from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.runner import ExperimentRunner


@pytest.mark.asyncio
async def test_self_letter_shows_only_the_own_selected_option(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec('source')), monitor_capacity=False)
    spec = derive_spec(tmp_path, 'source', 'letter', 'self_letter')
    assert spec['condition']['id'] == 'B3L'
    prepared = runner.prepare(spec)
    full = runner.prepare(derive_spec(tmp_path, 'source', 'self-full', 'self'))
    for letter, own in zip((json.loads(r) for r in prepared.requests_json), (json.loads(r) for r in full.requests_json)):
        context = json.loads(letter['context']['working_context'])
        assert context['own_previous_answer']['selects'] in (['option-a'], ['option-b'])
        # Nenhum item ou relação de autor: o WC é o mesmo de B1, só com as opções.
        assert all(not item.get('author_id') for item in context['items'])
        assert all(not rel.get('author_id') for rel in context['relations'])
        assert 'peer_positions' not in context
        # O B3 completo mostra a contribuição; o B3L não mostra nenhum item dela.
        own_items = [i for i in json.loads(own['context']['working_context'])['items'] if i.get('author_id')]
        assert own_items and all(i['content'] not in letter['wave_instructions'] for i in own_items)
        assert len(letter['context']['metadata']['source_observation_ids']) == 1
        assert 'Reconsider' in letter['instructions'] or 'Reconsidere' in letter['instructions']
