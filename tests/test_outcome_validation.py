"""Colunas do validador ao lado da leitura do bloco declarado.

Acréscimo do Lab (docs/MIGRACAO.md, 2026-10-04). As colunas anteriores
de outcomes.csv não mudam de definição.
"""
import csv
import json

import pytest

from norvald_lab.application.arof.outcome_extract import OutcomeRow, row_from_payload, write_csv
from norvald_lab.cli import demo_spec
from norvald_lab.runner import ExperimentRunner

COLUNAS_ANTERIORES = [
    "question_id", "condition", "run_id", "participant_id", "provider", "model", "round_number",
    "peer_exposure_mode", "status", "option_selected", "confidence", "new_evidence_cited",
    "grounding_targets", "relations_out", "attempt_index", "captured_at",
]
COLUNAS_DO_VALIDADOR = [
    "validation_code", "items_declared", "items_accepted", "relations_declared", "relations_accepted",
    "option_accepted", "grounding_targets_accepted", "rejected_reasons",
]

DECISION = {"local_id": "d1", "type": "decision", "content": "Escolho A", "confidence": "alta"}
SELECTS = {"relation_type": "selects", "source": "d1", "target": "option-a"}


def working_context(with_evidence=False):
    items = [{"id": "option-a", "type": "option", "content": "A"}, {"id": "option-b", "type": "option", "content": "B"}]
    if with_evidence:
        items.append({"id": "evidence-d1", "type": "evidence", "content": "Documento", "source_type": "document", "source_id": "d1"})
    return json.dumps({"question": "q", "items": items, "relations": []})


def payload(knowledge, relations, *, context=working_context(), error=None):
    content = "Prosa.\n<<CONTRIBUTION>>\n" + json.dumps({"knowledge": knowledge, "relations": relations}) + "\n<<END_CONTRIBUTION>>"
    record = {
        "task_label": "q01", "condition_id": "B1", "run_id": "r0001", "participant_id": "p1",
        "round_number": 1, "attempt_index": 1, "result": {"content": content}, "error": error,
    }
    if context is not None:
        record["request"] = {"context": {"working_context": context}}
    return record


def test_previous_columns_keep_name_and_order_and_new_ones_come_after():
    assert list(OutcomeRow.__dataclass_fields__) == COLUNAS_ANTERIORES + COLUNAS_DO_VALIDADOR


def test_accepted_contribution_reads_the_same_on_both_sides():
    row = row_from_payload(payload([DECISION], [SELECTS]))
    assert row.option_selected == row.option_accepted == "option-a"
    assert row.validation_code == "usable"
    assert (row.items_declared, row.items_accepted, row.relations_declared, row.relations_accepted) == ("1", "1", "1", "1")
    assert row.rejected_reasons == ""


def test_label_instead_of_option_id_is_declared_but_not_accepted():
    row = row_from_payload(payload([DECISION], [{"relation_type": "selects", "source": "d1", "target": "A"}]))
    assert row.status == "ok" and row.option_selected == "A"
    assert row.option_accepted == ""
    assert row.validation_code == "partial"
    assert (row.relations_declared, row.relations_accepted) == ("1", "0")
    assert row.rejected_reasons == "source ou target inexistente"


@pytest.mark.parametrize("unit,relation,reason", [
    ({"local_id": "k1", "type": "inference", "content": "z"}, {"relation_type": "derived_from", "source": "k1", "target": "r1"},
     "relação incompatível: inference -derived_from-> reference"),
    ({"local_id": "k1", "type": "claim", "content": "y"}, {"relation_type": "evidenced_by", "source": "k1", "target": "r1"},
     "relação semântica desconhecida"),
])
def test_grounding_declared_but_refused_stays_only_on_the_declared_side(unit, relation, reason):
    reference = {"local_id": "r1", "type": "reference", "content": "RFC 9110"}
    row = row_from_payload(payload([DECISION, unit, reference], [SELECTS, relation]))
    assert row.new_evidence_cited is True and row.grounding_targets == "r1"
    assert row.grounding_targets_accepted == ""
    assert row.option_accepted == "option-a"
    assert row.rejected_reasons == reason


def test_accepted_grounding_appears_on_both_sides_with_the_declared_target():
    inference = {"local_id": "k1", "type": "inference", "content": "z"}
    row = row_from_payload(payload(
        [DECISION, inference],
        [SELECTS, {"relation_type": "derived_from", "source": "k1", "target": "evidence-d1"}],
        context=working_context(with_evidence=True),
    ))
    assert row.grounding_targets == row.grounding_targets_accepted == "evidence-d1"
    assert row.validation_code == "usable"


def test_accepted_target_inside_the_contribution_is_reported_by_local_id():
    claim = {"local_id": "c1", "type": "claim", "content": "y"}
    inference = {"local_id": "k1", "type": "inference", "content": "z"}
    row = row_from_payload(payload([DECISION, claim, inference], [SELECTS, {"relation_type": "derived_from", "source": "k1", "target": "c1"}]))
    assert row.grounding_targets == row.grounding_targets_accepted == "c1"


def test_every_refused_part_is_listed_once_in_declaration_order():
    argument = {"local_id": "a1", "type": "argument", "content": "x"}
    row = row_from_payload(payload(
        [DECISION, argument, {"local_id": "e1", "type": "evidence", "content": "não declarável"}],
        [SELECTS, {"relation_type": "supports", "source": "a1", "target": "option-a"}, {"relation_type": "supports", "source": "a1", "target": "option-b"}],
    ))
    assert row.rejected_reasons == " | ".join([
        "tipo semântico não declarável",
        "relação incompatível: argument -supports-> option",
        "relação incompatível: argument -supports-> option",
    ])
    assert (row.items_declared, row.items_accepted, row.relations_declared, row.relations_accepted) == ("3", "2", "3", "1")


def test_record_without_context_leaves_the_validator_columns_empty_not_zero():
    row = row_from_payload(payload([DECISION], [SELECTS], context=None))
    assert row.option_selected == "option-a"
    assert [getattr(row, name) for name in COLUNAS_DO_VALIDADOR] == [""] * len(COLUNAS_DO_VALIDADOR)


@pytest.mark.parametrize("context", ["", "não é json", "[]"])
def test_unreadable_context_is_absence_not_a_validation_result(context):
    row = row_from_payload(payload([DECISION], [SELECTS], context=context))
    assert [getattr(row, name) for name in COLUNAS_DO_VALIDADOR] == [""] * len(COLUNAS_DO_VALIDADOR)


def test_failed_execution_is_marked_on_the_validator_side_too():
    record = payload([DECISION], [SELECTS], error={"message": "timeout"})
    record["result"] = None
    row = row_from_payload(record)
    assert row.status == "failed" and row.validation_code == "execution_failed"
    assert row.option_accepted == "" and row.items_accepted == "0"


def test_csv_header_carries_both_readings(tmp_path):
    path = write_csv([row_from_payload(payload([DECISION], [SELECTS]))], tmp_path / "outcomes.csv")
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == COLUNAS_ANTERIORES + COLUNAS_DO_VALIDADOR
        assert next(reader)["option_accepted"] == "option-a"


@pytest.mark.asyncio
async def test_collected_experiment_writes_the_validator_columns_from_its_own_raw(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec("b1")), monitor_capacity=False)
    with (tmp_path / "experiments/b1/outcomes.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert all(r["validation_code"] == "usable" and r["option_accepted"] == r["option_selected"] != "" for r in rows)
