"""B3T (estudo do formato, 12/11/2026): o mesmo conteúdo de B3, em texto corrido.

O participante vê a própria contribuição de B1 inteira, mas como texto, sem
itens nem relações de autor no contexto. O teste garante que todo conteúdo e
toda confiança do B3 aparecem no texto, e que nada dos pares chega.
"""
import json

import pytest

from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.runner import ExperimentRunner


@pytest.mark.asyncio
async def test_self_text_shows_the_same_content_as_b3_only_as_text(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec('source')), monitor_capacity=False)
    spec = derive_spec(tmp_path, 'source', 'texto', 'self_text')
    assert spec['condition']['id'] == 'B3T'
    text = runner.prepare(spec)
    full = runner.prepare(derive_spec(tmp_path, 'source', 'self-full', 'self'))
    for t, own in zip((json.loads(r) for r in text.requests_json), (json.loads(r) for r in full.requests_json)):
        context = json.loads(t['context']['working_context'])
        rendered = context['own_previous_answer']['text']
        # Nenhum item ou relação de autor: a estrutura sumiu do contexto.
        assert all(not item.get('author_id') for item in context['items'])
        assert all(not rel.get('author_id') for rel in context['relations'])
        assert 'peer_positions' not in context
        # Todo conteúdo e confiança do B3 está no texto, e a opção escolhida também.
        b3 = json.loads(own['context']['working_context'])
        me = t['agent_id']
        own_items = [i for i in b3['items'] if i.get('author_id') == me]
        assert own_items
        for item in own_items:
            assert item['content'] in rendered
            if item.get('confidence'):
                assert item['confidence'] in rendered
        for rel in b3['relations']:
            if rel.get('author_id') == me and rel['relation_type'] == 'selects':
                assert rel['target_id'] in rendered
        # Nada dos pares: só a própria observação de origem.
        others = [i['content'] for i in b3['items'] if i.get('author_id') and i.get('author_id') != me]
        assert all(c not in rendered for c in others)
        assert len(t['context']['metadata']['source_observation_ids']) == 1
        assert 'Reconsider' in t['instructions'] or 'Reconsidere' in t['instructions']


def test_self_text_is_written_in_the_language_of_the_round():
    """12/11/2026: a 1ª versão escrevia em português dentro de prompts em inglês."""
    from norvald_lab.own_text import render_own_text
    snap = {"items": [{"id": "i1", "author_id": "a", "content": "X", "confidence": "high"}],
            "relations": [{"author_id": "a", "relation_type": "selects", "source_id": "i1", "target_id": "option-b"}]}
    en = render_own_text(snap, "a", "en")
    assert en.startswith("In the previous round") and "Point 1: X (confidence: high)" in en and "you chose option-b" in en
    assert "Na rodada" not in en and "confiança" not in en
    pt = render_own_text(snap, "a", "pt-BR")
    assert pt.startswith("Na rodada anterior") and "você escolheu option-b" in pt
