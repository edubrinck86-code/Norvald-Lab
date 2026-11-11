"""Ordem sorteada dos pares em E (TESE-002 §4.1), criada em 11/11/2026.

Antes desta data o Lab mostrava os pares sempre na ordem do spec, e um
efeito de posição ficava misturado com a identidade do participante.
"""

import json

import pytest

from norvald_lab.application.arof.peer_order import PEER_ORDER_METHOD, draw_peer_order, reorder_by_author
from norvald_lab.runner import ExperimentRunner
from test_lab import demo_spec, derive_spec


def test_draw_is_reproducible_and_a_permutation():
    peers = ["p1", "p2", "p3", "p4"]
    first = draw_peer_order(peers, experiment_id="e-q01", repetition_index=1, participant_id="p2")
    again = draw_peer_order(peers, experiment_id="e-q01", repetition_index=1, participant_id="p2")
    assert first == again and sorted(first) == peers
    draws = {tuple(draw_peer_order(peers, experiment_id=f"e-q{n:02d}", repetition_index=1, participant_id="p1")) for n in range(1, 45)}
    assert len(draws) > 1  # a ordem varia entre perguntas; não é fixa


def test_reorder_keeps_options_first_and_inner_order():
    context = {"question": "q", "items": [
        {"id": "option-a", "author_id": None}, {"id": "x1", "author_id": "p1"}, {"id": "x2", "author_id": "p1"},
        {"id": "y1", "author_id": "p2"}], "relations": [
        {"source_id": "x1", "author_id": "p1"}, {"source_id": "y1", "author_id": "p2"}]}
    out = reorder_by_author(context, ["p2", "p1"])
    assert [i["id"] for i in out["items"]] == ["option-a", "y1", "x1", "x2"]
    assert [r["source_id"] for r in out["relations"]] == ["y1", "x1"]
    assert [i["id"] for i in context["items"]] == ["option-a", "x1", "x2", "y1"]  # não muta a entrada


@pytest.mark.asyncio
async def test_exposed_requests_follow_the_recorded_order(tmp_path):
    runner = ExperimentRunner(tmp_path)
    spec = demo_spec("b1")
    spec["repetitions"] = 2
    await runner.run(runner.prepare(spec), monitor_capacity=False)
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "e", "exposed"))
    again = runner.prepare(derive_spec(tmp_path, "b1", "e", "exposed"))
    orders = []
    for request, twin in zip(map(json.loads, prepared.requests_json), map(json.loads, again.requests_json)):
        meta = request["context"]["metadata"]
        assert meta["peer_order_method"] == PEER_ORDER_METHOD
        assert meta["peer_order"] == twin["context"]["metadata"]["peer_order"]  # reproduzível
        assert sorted(meta["peer_order"]) == sorted(p["id"] for p in spec["participants"])
        wc = json.loads(request["context"]["working_context"])
        shown = list(dict.fromkeys(i["author_id"] for i in wc["items"] if i["author_id"]))
        assert shown == meta["peer_order"]  # o que foi mostrado é o que foi gravado
        orders.append(tuple(meta["peer_order"]))
    assert len(set(orders)) > 1
    assert all(audit["peer_order"] for audit in json.loads(prepared.seed_audits_json))


@pytest.mark.asyncio
async def test_self_condition_has_no_peer_order(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec("b1")), monitor_capacity=False)
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "b3", "self"))
    for request in map(json.loads, prepared.requests_json):
        meta = request["context"]["metadata"]
        assert meta["peer_order"] == [] and meta["peer_order_method"] is None
