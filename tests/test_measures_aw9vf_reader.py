"""Registro aw9vf: fundamentos, estrutura e afirmações lidos do RAW pelo carregador."""

import json

from measures_helpers import base_context, payload, write_experiment

from norvald_lab.measures.ground import Ground
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
from norvald_lab.measures.question_info import QuestionInfo

CATALOG = QuestionCatalog({"q01": QuestionInfo("q01", "gabarito", "", "option-b", "Protocolo? REST/JSON gRPC")})

# Contexto da segunda onda: uma evidência da pergunta (sem autor), a contribuição de um par e a do próprio p1.
CONTEXT = base_context(
    [{"id": "ev-1", "type": "reference", "content": "RFC citada no enunciado"},
     {"id": "dec-p2", "type": "decision", "content": "gRPC", "author_id": "p2", "round_number": 1},
     {"id": "dec-p1", "type": "decision", "content": "REST", "author_id": "p1", "round_number": 1}],
    [{"author_id": "p2", "relation_type": "selects", "round_number": 1, "source_id": "dec-p2", "target_id": "option-b"}],
)


def block(units, relations):
    return "Prosa.\n<<CONTRIBUTION>>\n" + json.dumps({"knowledge": units, "relations": relations}) + "\n<<END_CONTRIBUTION>>"


def _load(root):
    return {(r.condition, r.participant_id): r for r in ObservationLoader(root, CATALOG).load(["rod"]).rows}


def test_grounds_are_classified_against_the_context_and_the_own_contribution(tmp_path):
    decision = {"local_id": "k1", "type": "decision", "content": "Escolho gRPC.", "confidence": "alta"}
    inference = {"local_id": "k2", "type": "inference", "content": "Logo, gRPC serve."}
    claim = {"local_id": "k3", "type": "claim", "content": "  Streaming   NATIVO  "}
    selects = {"relation_type": "selects", "source": "k1", "target": "option-b"}
    write_experiment(tmp_path, "rod", "q01", "B1", [
        payload("rod", "q01", "B1", "p1", content=block([decision, inference, claim], [selects, {"relation_type": "derived_from", "source": "k2", "target": "k3"}])),
        payload("rod", "q01", "B1", "p2", content="sem bloco nenhum"),
    ])
    write_experiment(tmp_path, "rod", "q01", "E", [
        payload("rod", "q01", "E", "p1", context=CONTEXT, content=block([decision], [
            selects,
            {"relation_type": "derived_from", "source": "k1", "target": "ev-1"},      # evidência da pergunta: base
            {"relation_type": "derived_from", "source": "k1", "target": "dec-p2"},    # contribuição de um par: peer
            {"relation_type": "documents", "source": "k1", "target": "dec-p1"},       # a própria contribuição: own
            {"relation_type": "supports", "source": "k1", "target": "dec-p2"},        # apoiar o par não é fundamento
        ])),
    ])
    rows = _load(tmp_path)
    b1 = rows[("B1", "p1")]
    # Em B1 o alvo "k3" é uma unidade da própria contribuição (não a decisão): fundamento local, pelo texto normalizado.
    assert b1.grounds == (Ground("local", "streaming nativo"),)
    assert b1.structured and [kind for kind, _ in b1.claims] == ["decision", "inference", "claim"]
    assert rows[("B1", "p2")].structured is False and rows[("B1", "p2")].grounds == () and rows[("B1", "p2")].claims == ()
    e = rows[("E", "p1")]
    assert set(e.grounds) == {Ground("base", "ev-1"), Ground("peer", "dec-p2"), Ground("own", "dec-p1")}
    assert all(g.scope != "local" for g in e.grounds)  # alvo que é a própria decisão não seria fundamento


def test_decision_target_is_not_a_ground(tmp_path):
    decision = {"local_id": "k1", "type": "decision", "content": "Escolho gRPC.", "confidence": "alta"}
    reason = {"local_id": "k2", "type": "claim", "content": "porque sim"}
    write_experiment(tmp_path, "rod", "q01", "B1", [
        payload("rod", "q01", "B1", "p1", content=block([decision, reason], [
            {"relation_type": "selects", "source": "k1", "target": "option-b"},
            {"relation_type": "derived_from", "source": "k2", "target": "k1"},  # o validador só aceita inferência → decisão
        ])),
    ])
    assert _load(tmp_path)[("B1", "p1")].grounds == ()


def test_declared_ground_counts_even_when_the_validator_rejects_it(tmp_path):
    # Dados reais de 11/11/2026: o validador recusa quase todo fundamento declarado
    # (decisão → opção, decisão → evidência). O registro mede o declarado.
    decision = {"local_id": "k1", "type": "decision", "content": "Escolho gRPC.", "confidence": "alta"}
    write_experiment(tmp_path, "rod", "q01", "B1", [
        payload("rod", "q01", "B1", "p1", content=block([decision], [
            {"relation_type": "selects", "source": "k1", "target": "option-b"},
            {"relation_type": "derived_from", "source": "k1", "target": "option-b"},
            {"relation_type": "derived_from", "source": "k1", "target": "evidence-<id>"},
        ])),
    ])
    row = _load(tmp_path)[("B1", "p1")]
    assert row.grounds == (Ground("base", "evidence-<id>"), Ground("base", "option-b"))
