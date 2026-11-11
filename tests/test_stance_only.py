"""Quinta condição, EP (exposta só pela posição), criada em 11/11/2026.

Por quê: o Eduardo aprovou uma 5ª condição para separar o peso da posição dos
pares do peso da justificativa, como a condição stance-only de Hao et al. 2026
(arXiv 2606.00820). Em EP o participante vê a própria contribuição inteira
(como em B3) e, de cada par, só a opção escolhida. As condições se aninham:
B3 ⊂ EP ⊂ E.
"""

import hashlib
import json
import re

import pytest

from norvald_lab.application.arof.peer_order import PEER_ORDER_METHOD
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.config import validate_spec
from norvald_lab.herd.batch import HerdBatch
from norvald_lab.herd.schedule import DERIVED_CONDITIONS, protocol_order
from norvald_lab.runner import ExperimentRunner
from norvald_lab import runtime
from norvald_lab.storage import read_verified_records
from test_herd_batch import BANK_EN, PANEL
from test_language_en import english_spec

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# Calculados ANTES da mudança (11/11/2026), sobre B1 demo → B3 e E, com os UUIDs
# (aleatórios a cada coleta) trocados por <uuid> e sem a impressão digital da condição.
# Se mudarem, uma condição que já existia passou a gerar outro request.
ANTES = {
    "pt-b3": "c5f15521fbd3cc313310ec2fbf8ffcda5ebedc6d7e93ce08f4998837430d359b",
    "pt-e": "8e1f037268c081a3468d9bde05d97118afce8822bf18cfe8853142e4aa8ab920",
    "en-b3": "c32099163ab4d6f3dbb9ffb3f9c234f9253368b577e078fde89e6eaf73f4307a",
    "en-e": "1a973545f22b7276affc9369ba309aa056a3df01a91b943e5546ce6f66a1afa7",
}

# Justificativa e confiança distintas por participante, para detectar vazamento entre eles.
CONFIDENCE = {"analista-1": "alta", "analista-2": "baixa", "analista-3": "média", "analyst-1": "high", "analyst-2": "low", "analyst-3": "medium"}


@pytest.fixture
def distinct_answers(monkeypatch):
    """O DemoProvider dá o mesmo texto a todos; aqui cada um escreve algo que só ele diz."""
    original = runtime.DemoProvider.execute

    async def execute(self, request, model):
        result = await original(self, request, model)
        agent = request.agent_id
        text = result.content
        text = text.replace("Escolha simulada", f"SEGREDO-{agent}-justificativa").replace("Simulated choice", f"SEGREDO-{agent}-justification")
        text = re.sub(r'"confidence": "[^"]*"', f'"confidence": "{CONFIDENCE[agent]}"', text)
        result.content = text
        return result

    monkeypatch.setattr(runtime.DemoProvider, "execute", execute)


def normalized_hash(prepared):
    requests = []
    for raw in prepared.requests_json:
        request = json.loads(raw)
        del request["context"]["metadata"]["condition_fingerprint"]
        requests.append(json.dumps(request, sort_keys=True))
    return hashlib.sha256(UUID.sub("<uuid>", "\n".join(requests)).encode()).hexdigest()


async def collect(tmp_path, spec):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(spec), monitor_capacity=False)
    return runner


def requests_of(prepared):
    return {json.loads(r)["agent_id"]: json.loads(r) for r in prepared.requests_json}


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["pt", "en"])
async def test_existing_conditions_generate_the_same_requests_as_before(tmp_path, language):
    runner = await collect(tmp_path, english_spec("b1") if language == "en" else demo_spec("b1"))
    assert normalized_hash(runner.prepare(derive_spec(tmp_path, "b1", "b3", "self"))) == ANTES[f"{language}-b3"]
    assert normalized_hash(runner.prepare(derive_spec(tmp_path, "b1", "e", "exposed"))) == ANTES[f"{language}-e"]


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["pt", "en"])
async def test_stance_shows_each_peer_option_and_nothing_else_of_the_peer(tmp_path, distinct_answers, language):
    spec = english_spec("b1") if language == "en" else demo_spec("b1")
    runner = await collect(tmp_path, spec)
    ids = [p["id"] for p in spec["participants"]]
    chosen = {}
    for raw in (r.payload for r in read_verified_records(tmp_path, "b1")):
        chosen[raw["participant_id"]] = re.search(r'"target": "(option-[ab])"', raw["result"]["content"]).group(1)
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "ep", "stance"))
    for agent, request in requests_of(prepared).items():
        text = request["wave_instructions"]
        wc = json.loads(request["context"]["working_context"])
        peers = [i for i in ids if i != agent]
        assert {p["author_id"]: p["selects"] for p in wc["peer_positions"]} == {p: [chosen[p]] for p in peers}
        assert [p["author_id"] for p in wc["peer_positions"]] == [p for p in request["context"]["metadata"]["peer_order"] if p != agent]
        for peer in peers:
            assert f"SEGREDO-{peer}" not in text and f"SEGREDO-{peer}" not in json.dumps(request)  # nenhuma palavra do par
            assert CONFIDENCE[peer] not in text.replace("peer_positions", "")
        # a própria contribuição entra inteira, como em B3
        assert f"SEGREDO-{agent}-" in text and CONFIDENCE[agent] in text
        # nenhum item nem relação de par no grafo: só opções, âncoras e os itens do próprio participante
        assert {i["author_id"] for i in wc["items"]} <= {None, agent}
        assert {r["author_id"] for r in wc["relations"]} == {agent}
        assert request["context"]["metadata"]["lab_exposure_mode"] == "stance"
        assert request["context"]["metadata"]["peer_exposure_mode"] == "stance"


@pytest.mark.asyncio
async def test_stance_own_part_is_the_same_as_b3_and_reconsider_text_is_shared(tmp_path, distinct_answers):
    runner = await collect(tmp_path, demo_spec("b1"))
    b3 = requests_of(runner.prepare(derive_spec(tmp_path, "b1", "b3", "self")))
    ep = requests_of(runner.prepare(derive_spec(tmp_path, "b1", "ep", "stance")))
    for agent in b3:
        own3 = json.loads(b3[agent]["context"]["working_context"])
        own_ep = json.loads(ep[agent]["context"]["working_context"])
        # ids das contribuições são UUIDs novos a cada preparo; o conteúdo e a estrutura são os mesmos
        strip = lambda wc: UUID.sub("<uuid>", json.dumps({k: wc[k] for k in ("question", "items", "relations")}, sort_keys=True))
        assert strip(own3) == strip(own_ep)
        assert b3[agent]["instructions"] == ep[agent]["instructions"]  # mesmo "Reconsidere" de B3 e E
        assert "Reconsidere" in ep[agent]["instructions"]


@pytest.mark.asyncio
async def test_stance_peer_order_is_recorded_and_equals_exposed(tmp_path):
    spec = demo_spec("b1")
    spec["repetitions"] = 2
    runner = await collect(tmp_path, spec)
    # o sorteio sai do id do experimento: usar o mesmo id em E e EP prova que a regra é a mesma
    exposed = runner.prepare(derive_spec(tmp_path, "b1", "x", "exposed"))
    stance = runner.prepare(derive_spec(tmp_path, "b1", "x", "stance"))
    order = lambda prepared: [(m["repetition_index"], m["participant_id"], m["peer_order"], m["peer_order_method"]) for m in (json.loads(r)["context"]["metadata"] for r in prepared.requests_json)]
    assert order(stance) == order(exposed)
    assert all(method == PEER_ORDER_METHOD and sorted(o) == ["analista-1", "analista-2", "analista-3"] for _, _, o, method in order(stance))
    assert len({tuple(o) for _, _, o, _ in order(stance)}) > 1
    # a gravação no registro bruto também
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "ep", "stance"))
    await runner.run(prepared, monitor_capacity=False)
    sent = {(json.loads(r)["context"]["metadata"]["repetition_index"], json.loads(r)["agent_id"]): json.loads(r)["context"]["metadata"]["peer_order"] for r in prepared.requests_json}
    records = read_verified_records(tmp_path, "ep")
    assert len(records) == 6
    for record in records:
        meta = record.payload["request"]["studio_metadata"]
        assert meta["peer_order"] == sent[(meta["repetition_index"], meta["participant_id"])]
        assert meta["peer_order_method"] == PEER_ORDER_METHOD and meta["lab_exposure_mode"] == "stance"


@pytest.mark.asyncio
async def test_stance_requires_a_valid_blind_source_and_two_participants(tmp_path):
    runner = await collect(tmp_path, demo_spec("b1"))
    await runner.run(runner.prepare(derive_spec(tmp_path, "b1", "ep", "stance")), monitor_capacity=False)
    with pytest.raises(ValueError, match="cega"):
        runner.prepare(derive_spec(tmp_path, "ep", "ep2", "stance"))  # origem não pode ser outra condição derivada
    different = derive_spec(tmp_path, "b1", "ep3", "stance")
    different["task"]["objective"] += " (outra)"
    with pytest.raises(ValueError, match="diferem"):
        runner.prepare(different)
    solo = demo_spec("solo")
    solo["participants"] = solo["participants"][:1]
    solo["condition"] = {"id": "EP", "exposure": "stance", "prior_experiment": "b1", "tools": "off"}
    with pytest.raises(ValueError, match="pelo menos dois"):
        validate_spec(solo)
    with pytest.raises(ValueError, match="exposure"):
        validate_spec(demo_spec("x") | {"condition": {"id": "Z", "exposure": "desconhecida", "prior_experiment": "b1"}})


@pytest.mark.asyncio
async def test_stance_demo_runs_end_to_end_in_english_without_portuguese(tmp_path):
    spec = english_spec("b1")
    runner = await collect(tmp_path, spec)
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "ep", "stance"))
    result = await runner.run(prepared, monitor_capacity=False)
    assert result["status"] == "complete" and result["executed"] == 3
    for request in prepared.requests_json:
        for word in ("Você", "Reconsidere", "Escolha", "Analista", "média", "ção"):
            assert word not in request


@pytest.mark.asyncio
async def test_herd_batch_in_english_runs_five_conditions_for_two_questions(tmp_path):
    panel = PANEL | {"language": "en", "instructions": "Choose exactly one option."}
    bank = {"questions": [q for q in BANK_EN["questions"] if q["id"] in {"q01", "h01"}]}
    report = await HerdBatch(ExperimentRunner(tmp_path), bank, panel, run_id="en").run(["q01", "h01"], allow_live=False)
    assert not report.blocked and len(report.ran) == 10 and all(status == "complete" for _, status in report.ran)
    assert {expid.rsplit("-", 1)[1] for expid, _ in report.ran} == {"b1", "b2", "b3", "ep", "e"}
    ep = json.loads((tmp_path / "experiments" / "en-q01-ep" / "spec.json").read_text())
    assert ep["condition"] == {"id": "EP", "exposure": "stance", "tools": "off", "prior_experiment": "en-q01-b1"}


@pytest.mark.asyncio
async def test_herd_batch_blocks_stance_when_b1_is_missing_and_pilot_stays_blind_only(tmp_path):
    panel = PANEL | {"language": "en", "instructions": "Choose exactly one option."}
    bank = {"questions": [q for q in BANK_EN["questions"] if q["id"] == "q01"]}
    batch = HerdBatch(ExperimentRunner(tmp_path), bank, panel, run_id="b")
    (tmp_path / "experiments" / "b-q01-b1").mkdir(parents=True)
    report = await batch.run(["q01"], allow_live=False)
    assert {expid for expid, _ in report.blocked} == {"b-q01-b3", "b-q01-ep", "b-q01-e"}
    assert [(s.question_id, s.condition_id) for s in protocol_order(["a", "b", "c"], blind_first_only=True)] == [("a", "B1"), ("b", "B1"), ("c", "B1")]


def test_derived_phase_rotates_so_every_condition_opens_and_each_position_is_balanced():
    questions = [f"q{n:02d}" for n in range(1, 10)]
    steps = protocol_order(questions)
    assert [s.condition_id for s in steps[:18]] == ["B1", "B2", "B2", "B1"] * 4 + ["B1", "B2"]  # fase cega inalterada
    derived = [s for s in steps if s.derived]
    assert len(derived) == 27 and {s.condition_id for s in derived} == set(DERIVED_CONDITIONS)
    by_question = {q: [s.condition_id for s in derived if s.question_id == q] for q in questions}
    assert all(sorted(order) == sorted(DERIVED_CONDITIONS) for order in by_question.values())
    assert {order[0] for order in by_question.values()} == set(DERIVED_CONDITIONS)
    for position in range(3):  # cada condição ocupa cada posição o mesmo número de vezes
        assert {c: [o[position] for o in by_question.values()].count(c) for c in DERIVED_CONDITIONS} == {"B3": 3, "EP": 3, "E": 3}
    three = [s.condition_id for s in protocol_order(["a", "b", "c"]) if s.derived]
    assert {three[0], three[3], three[6]} == set(DERIVED_CONDITIONS)
