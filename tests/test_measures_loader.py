"""Carregador da tabela de observações: tentativa mais recente, falha da tentativa 1, regra 3."""

from measures_helpers import base_context, contribution, payload, write_experiment

from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
from norvald_lab.measures.question_info import QuestionInfo

CATALOG = QuestionCatalog({"q01": QuestionInfo("q01", "gabarito", "", "option-b", "Protocolo? REST/JSON gRPC")})

PEERS = base_context(
    [{"id": "dec-p2", "type": "decision", "content": "gRPC", "author_id": "p2", "round_number": 1},
     {"id": "opt-p3", "type": "option", "content": "uma opção inventada", "author_id": "p3", "round_number": 1}],
    [{"author_id": "p2", "relation_type": "selects", "round_number": 1, "source_id": "dec-p2", "target_id": "option-b"}],
)


def _load(root, runs=("rod",)):
    return ObservationLoader(root, CATALOG).load(runs)


def test_latest_attempt_wins_and_attempt1_failure_is_kept(tmp_path):
    # O runner ganha novas tentativas (attempt_index 2): a linha é a da última,
    # mas a falha da primeira continua visível, e o custo soma as duas.
    write_experiment(tmp_path, "rod", "q01", "B1", [
        payload("rod", "q01", "B1", "p1", content="", error="timeout", attempt=1, cost=0.0),
        payload("rod", "q01", "B1", "p1", content=contribution("option-b"), attempt=2, cost=0.02),
        payload("rod", "q01", "B1", "p2", content=contribution("option-a"), attempt=1, cost=0.01),
    ])
    rows = {r.participant_id: r for r in _load(tmp_path).rows}
    assert rows["p1"].option == "option-b" and rows["p1"].attempts == 2 and rows["p1"].attempt1_failed
    assert rows["p1"].correct is True and rows["p1"].cost == 0.02
    assert rows["p2"].option == "option-a" and rows["p2"].attempts == 1 and not rows["p2"].attempt1_failed
    assert rows["p2"].correct is False and rows["p2"].kind == "gabarito"
    assert "Prosa da justificativa." in rows["p2"].justification and "Escolha." in rows["p2"].justification


def test_attempt_order_does_not_depend_on_file_order(tmp_path):
    write_experiment(tmp_path, "rod", "q01", "B1", [
        payload("rod", "q01", "B1", "p1", content=contribution("option-a"), attempt=2),
        payload("rod", "q01", "B1", "p1", content=contribution("option-b"), attempt=1),
    ])
    row = _load(tmp_path).rows[0]
    assert row.option == "option-a" and not row.attempt1_failed


def test_failed_last_attempt_has_no_position(tmp_path):
    write_experiment(tmp_path, "rod", "q01", "B1", [payload("rod", "q01", "B1", "p1", content="sem bloco nenhum")])
    row = _load(tmp_path).rows[0]
    assert row.option is None and row.correct is None and row.attempt1_failed and row.status == "no_decision"


def test_indirect_selection_resolved_one_step(tmp_path):
    # fumaca-2 (Nemotron): a decisão em E apontou para a decisão de um par.
    write_experiment(tmp_path, "rod", "q01", "E", [
        payload("rod", "q01", "E", "p1", content=contribution("dec-p2"), context=PEERS, peer_order=("p2", "p1", "p3")),
        payload("rod", "q01", "E", "p4", content=contribution("opt-p3"), context=PEERS),
    ])
    table = _load(tmp_path)
    rows = {r.participant_id: r for r in table.rows}
    assert rows["p1"].option == "option-b" and rows["p1"].indirect and rows["p1"].indirect_source == "p2"
    assert not rows["p1"].attempt1_failed  # resolvida não é falha
    assert rows["p1"].peer_order == ("p2", "p1", "p3")
    assert rows["p4"].option is None  # option criada por participante não é opção da pergunta
    assert table.indirect_rows == 1
    without = {r.participant_id: r for r in table.without_indirect().rows}
    assert without["p1"].option is None and without["p1"].correct is None and without["p1"].cost == rows["p1"].cost


def test_directory_must_match_the_run(tmp_path):
    # A rodada "rod" não pode engolir "rod-3-q01-b1" só pelo prefixo do nome.
    write_experiment(tmp_path, "rod-3", "q01", "B1", [payload("rod-3", "q01", "B1", "p1", content=contribution("option-a"))])
    write_experiment(tmp_path, "rod", "q01", "B1", [payload("rod", "q01", "B1", "p1", content=contribution("option-b"))])
    assert [r.option for r in _load(tmp_path).rows] == ["option-b"]
    assert {r.run for r in _load(tmp_path, ("rod", "rod-3")).rows} == {"rod", "rod-3"}


def test_agent_is_the_model_when_unique_in_the_run(tmp_path):
    # Achado do piloto (11/11/2026): "analista-1" (pt) e "analyst-1" (en) são o mesmo modelo.
    write_experiment(tmp_path, "a", "q01", "B1", [payload("a", "q01", "B1", "analista-1", content=contribution("option-a"), model="gemma")])
    write_experiment(tmp_path, "b", "q01", "B1", [payload("b", "q01", "B1", "analyst-1", content=contribution("option-a"), model="gemma")])
    write_experiment(tmp_path, "c", "q01", "B1", [payload("c", "q01", "B1", f"p{i}", content=contribution("option-a"), model="demo-v1") for i in (1, 2)])
    agents = {(r.run, r.participant_id): r.agent for r in _load(tmp_path, ("a", "b", "c")).rows}
    assert agents[("a", "analista-1")] == agents[("b", "analyst-1")] == "gemma"
    assert agents[("c", "p1")] != agents[("c", "p2")]


def test_catalog_reads_frozen_plan_and_answers(tmp_path):
    plan = tmp_path / "studies" / "rod" / "plan.json"
    plan.parent.mkdir(parents=True)
    plan.write_text('{"bank": {"questions": [{"id": "m1", "kind": "gabarito", "category": "law", "question": "Q?", "options": [{"id": "option-a", "content": "A"}]}]}}')
    answers = tmp_path / "answers.json"
    answers.write_text('{"answers": {"m1": "option-a", "g9": "option-b"}}')
    catalog = QuestionCatalog.from_files(tmp_path, ["rod"], [], [answers])
    assert catalog.get("m1") == QuestionInfo("m1", "gabarito", "law", "option-a", "Q? A")
    assert catalog.get("g9").answer == "option-b" and catalog.get("zz").kind == "desconhecido"
