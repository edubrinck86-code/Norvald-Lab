"""Contribuição sem fundamento declarado (achado do PR #16, 12/11/2026).

O portão de nova tentativa da coleta aceitava contribuição com opção e ZERO
fundamentos (derived_from, evidenced_by, documents). Agora, com
`budget.require_grounds`, ela conta como inválida e gasta a nova tentativa.
O validador compartilhado e as medidas NÃO mudam: as coletas conf2-* foram
validadas e analisadas com a regra antiga.
"""
import json

import pytest

from norvald_lab.cli import demo_spec
from norvald_lab.config import validate_spec
from norvald_lab.runner import ExperimentRunner, _has_valid_contribution
from test_agent_retry import VICTIM, FlakyProvider, raws, registry_for

BLOCK_NO_GROUNDS = {"knowledge": [{"local_id": "d", "type": "decision", "content": "x", "confidence": "medium"}],
                    "relations": [{"relation_type": "selects", "source": "d", "target": "option-a"}]}
# `evidenced_by` nem existe em RELATION_TYPES (o validador a recusa como "desconhecida");
# na prática o fundamento aceito é derived_from (ou documents) a partir de uma inferência.
BLOCK_GROUNDS = {"knowledge": BLOCK_NO_GROUNDS["knowledge"] + [{"local_id": "k1", "type": "inference", "content": "z"}],
                 "relations": BLOCK_NO_GROUNDS["relations"] + [{"relation_type": "derived_from", "source": "k1", "target": "evidence-d1"}]}


class Obs:
    def __init__(self, block):
        self.payload = {"participant_id": "p", "error": None, "round_number": 1,
                        "result": {"content": "<<CONTRIBUTION>>\n" + json.dumps(block) + "\n<<END_CONTRIBUTION>>"},
                        "request": {"context": {"working_context": json.dumps({"question": "q", "items": [{"id": "option-a", "type": "option", "content": "A"}, {"id": "evidence-d1", "type": "evidence", "content": "Documento", "source_type": "document", "source_id": "d1"}], "relations": []})}}}

    def to_dict(self):
        return self.payload


def test_zero_grounds_rejected_only_when_required():
    assert _has_valid_contribution(Obs(BLOCK_NO_GROUNDS))  # regra antiga preservada por padrão
    assert not _has_valid_contribution(Obs(BLOCK_NO_GROUNDS), True)
    assert _has_valid_contribution(Obs(BLOCK_GROUNDS), True)


def test_spec_unchanged_without_the_option_and_type_checked():
    assert "require_grounds" not in validate_spec(demo_spec("g0"))["budget"]
    bad = demo_spec("g1")
    bad["budget"] = {"require_grounds": "sim"}
    with pytest.raises(ValueError, match="require_grounds"):
        validate_spec(bad)


@pytest.mark.asyncio
async def test_collection_retries_when_no_grounds_are_declared(tmp_path):
    """O demo declara só `selects`: com a exigência, usa as 2 tentativas; sem ela, 1."""
    for expid, required, expected in (("sem", False, 1), ("com", True, 2)):
        spec = demo_spec(expid)
        spec["budget"] = {"max_agent_attempts": 2} | ({"require_grounds": True} if required else {})
        runner = ExperimentRunner(tmp_path)
        await runner.run(runner.prepare(spec), registry=registry_for(spec, FlakyProvider(bad=0)))
        assert {r["attempt_index"] for r in raws(tmp_path, expid) if r["participant_id"] == VICTIM} == set(range(1, expected + 1))
