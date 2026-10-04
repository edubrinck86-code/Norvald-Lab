"""Recusa por parte no parser do bloco CONTRIBUTION.

Divergência intencional do Studio (docs/MIGRACAO.md, 2026-10-04): uma
parte ilegível é recusada com motivo e as demais seguem. Nada é reparado.
"""
import csv
import json

import pytest

from norvald_lab.application.arof.exposed_context import seed_peer_contributions
from norvald_lab.application.arof.prior_contribution import PriorContribution
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.contribution_check import check_contribution
from norvald_lab.domain.deliberation.context_item import ContextItem
from norvald_lab.domain.deliberation.contribution import Contribution
from norvald_lab.domain.deliberation.working_context import WorkingContext
from norvald_lab.runner import ExperimentRunner
from norvald_lab.runtime import DemoProvider
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry

DECISION = {"local_id": "d1", "type": "decision", "content": "Escolho A", "confidence": "alta"}
ARGUMENT = {"local_id": "a1", "type": "argument", "content": "Porque x"}
SELECTS = {"relation_type": "selects", "source": "d1", "target": "option-a"}
SUPPORTS = {"relation_type": "supports", "source": "a1", "target": "d1"}


def block(knowledge, relations):
    return "Prosa.\n<<CONTRIBUTION>>\n" + json.dumps({"knowledge": knowledge, "relations": relations}) + "\n<<END_CONTRIBUTION>>"


def context():
    wc = WorkingContext(question="q")
    wc.add(ContextItem(id="option-a", type="option", content="A"))
    wc.add(ContextItem(id="option-b", type="option", content="B"))
    return wc


def test_relation_without_target_is_refused_and_the_rest_is_kept():
    content = block([DECISION, ARGUMENT], [SELECTS, {"relation_type": "supports", "source": "a1"}])
    check = check_contribution(content, "p1", context())
    assert check["usable"] and check["code"] == "partial"
    assert check["declared_items"] == check["accepted_items"] == 2
    assert check["declared_relations"] == 2 and check["accepted_relations"] == 1
    assert check["rejected"] == [{"kind": "relation", "identifier": "relations[1]", "reason": "campo obrigatório ausente: target"}]


def test_unit_without_local_id_is_refused_and_the_rest_is_kept():
    content = block([DECISION, {"type": "claim", "content": "sem id"}, ARGUMENT], [SELECTS, SUPPORTS])
    check = check_contribution(content, "p1", context())
    assert check["usable"] and check["code"] == "partial"
    assert check["declared_items"] == 3 and check["accepted_items"] == 2
    assert check["accepted_relations"] == 2
    assert check["rejected"] == [{"kind": "knowledge", "identifier": "knowledge[1]", "reason": "local_id obrigatório"}]


@pytest.mark.parametrize("part,reason", [
    ("texto solto", "parte não é um objeto JSON"),
    ({"local_id": "k9", "content": "sem tipo"}, "type obrigatório"),
    ({"local_id": "k9", "type": "claim", "content": "x", "metadata": 7}, "metadata não é um objeto JSON"),
])
def test_each_unreadable_unit_carries_its_own_reason(part, reason):
    contribution = Contribution.parse(block([DECISION, part], [SELECTS]), author_id="p1", round_number=1)
    assert [k.local_id for k in contribution.knowledge] == ["d1"]
    assert [(m.kind, m.index, m.reason) for m in contribution.malformed] == [("knowledge", 1, reason)]


def test_unreadable_part_is_never_repaired_or_counted_as_knowledge():
    contribution = Contribution.parse(
        block([DECISION, {"type": "claim", "content": "sem id"}], [SELECTS, {"source": "d1", "target": "option-a"}]),
        author_id="p1", round_number=1,
    )
    assert len(contribution.knowledge) == 1 and len(contribution.relations) == 1
    assert [(m.kind, m.index) for m in contribution.malformed] == [("knowledge", 1), ("relation", 1)]
    assert "malformed" not in contribution.to_dict()


def test_relation_pointing_to_a_refused_unit_is_refused_by_the_validator():
    content = block([DECISION, {"type": "argument", "content": "sem id"}], [SELECTS, SUPPORTS])
    check = check_contribution(content, "p1", context())
    assert check["accepted_items"] == 1 and check["accepted_relations"] == 1
    assert [p["reason"] for p in check["rejected"]] == ["local_id obrigatório", "source ou target inexistente"]


@pytest.mark.parametrize("content,code", [
    ("Prosa.\n<<CONTRIBUTION>>\n" + json.dumps({"knowledge": [DECISION], "relations": [SELECTS]})[:-20], "unclosed_block"),
    ("<<CONTRIBUTION>>{\"knowledge\": [" + json.dumps(DECISION) + ",]}<<END_CONTRIBUTION>>", "invalid_json"),
    (block("d1", []), "invalid_schema"),
])
def test_block_without_a_readable_structure_is_still_discarded_whole(content, code):
    check = check_contribution(content, "p1", context())
    assert not check["usable"] and check["code"] == code and check["accepted_items"] == 0


def test_only_unreadable_units_leave_nothing_usable():
    check = check_contribution(block([{"type": "claim", "content": "sem id"}], []), "p1", context())
    assert not check["usable"] and check["code"] == "invalid_schema"
    assert check["declared_items"] == 1 and check["accepted_items"] == 0


def test_author_with_one_unreadable_relation_is_seeded_in_the_exposed_context():
    seeded, authors, _audit = seed_peer_contributions(
        context(),
        [PriorContribution(author_id="p1", response=block([DECISION, ARGUMENT], [SELECTS, {"relation_type": "supports", "source": "a1"}]))],
    )
    assert authors == ("p1",)
    assert sorted(i.type for i in seeded.active_items() if i.author_id == "p1") == ["argument", "decision"]
    assert [(r.relation_type, r.target_id) for r in seeded.relations] == [("selects", "option-a")]


@pytest.mark.asyncio
async def test_origin_with_one_unreadable_relation_can_be_derived(tmp_path):
    class OneBadRelation(DemoProvider):
        async def execute(self, request, model):
            if request.agent_id != "analista-2":
                return await super().execute(request, model)
            return ExecutionResult(
                content=block([DECISION, ARGUMENT], [SELECTS, {"relation_type": "supports", "source": "a1"}]),
                tokens=0, duration_seconds=0, provider="demo", model=model,
            )

    spec = demo_spec("base-parcial")
    registry = AgentRegistry()
    registry.register_provider("simulador", OneBadRelation(), kind="demo")
    for participant in spec["participants"]:
        registry.register_agent(participant["id"], "simulador", participant["model"])
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(spec), registry=registry, monitor_capacity=False)

    prepared = runner.prepare(derive_spec(tmp_path, "base-parcial", "e-parcial", "exposed"))
    audits = json.loads(prepared.seed_audits_json)
    assert all(sorted(a["autores_semeados"]) == ["analista-1", "analista-2", "analista-3"] for a in audits)

    with (tmp_path / "experiments/base-parcial/outcomes.csv").open(encoding="utf-8") as handle:
        row = next(r for r in csv.DictReader(handle) if r["participant_id"] == "analista-2")
    assert row["status"] == "ok" and row["option_selected"] == "option-a"
    assert row["validation_code"] == "partial"
    assert row["rejected_reasons"] == "campo obrigatório ausente: target"
