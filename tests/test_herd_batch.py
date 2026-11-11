"""Coleta do Δ_herd em lote (criado em 11/11/2026).

O Lab aceitava uma pergunta por experimento; 44 perguntas × 4 condições à mão
eram 176 experimentos. O lote segue a ordem do TESE-002 §4.1 e é retomável.
"""

import json
from pathlib import Path

import pytest

from norvald_lab.herd.batch import HerdBatch
from norvald_lab.herd.run_command import freeze_plan
from norvald_lab.herd.schedule import protocol_order
from norvald_lab.herd.specs import blind_spec, experiment_id
from norvald_lab.runner import ExperimentRunner

BANK = json.loads(Path(__file__).resolve().parents[1].joinpath("studies/herd/bank.json").read_text(encoding="utf-8"))
BANK_EN = json.loads(Path(__file__).resolve().parents[1].joinpath("studies/herd/bank.en.json").read_text(encoding="utf-8"))
ANSWERS = json.loads(Path(__file__).resolve().parents[1].joinpath("studies/herd/answers.json").read_text(encoding="utf-8"))
PANEL = {
    "mode": "demo",
    "providers": {"simulador": {"kind": "demo"}},
    "participants": [{"provider": "simulador", "model": "demo-v1"} for _ in range(3)],
    "reasoning_effort": "default",
    "sampling": {"temperature": 0.7, "top_p": 1.0, "max_tokens": 800},
    "instructions": "Escolha exatamente uma das opções do Working Context.",
}


def test_bank_matches_the_protocol():
    kinds = [q["kind"] for q in BANK["questions"]]
    assert (kinds.count("contestavel"), kinds.count("gabarito"), kinds.count("reserva")) == (32, 12, 6)
    assert all(2 <= len(q["options"]) <= 3 for q in BANK["questions"])
    assert {q["id"] for q in BANK["questions"]} < {q["id"] for q in BANK_EN["questions"]}
    assert "Sim" not in json.dumps(ANSWERS["answers"])  # gabarito é id de opção, não texto


def test_english_bank_is_the_collection_bank():
    # 11/11/2026: a coleta passou a ser em inglês (decisão do Eduardo) e ganhou h01–h40,
    # porque o gabarito g01–g12 foi fácil demais no piloto-2 (só g02 e g12 tiveram erro).
    kinds = [q["kind"] for q in BANK_EN["questions"]]
    assert (kinds.count("contestavel"), kinds.count("gabarito"), kinds.count("reserva")) == (32, 52, 6)
    assert BANK_EN["language"] == "en"
    assert set(ANSWERS["answers"]) == {q["id"] for q in BANK_EN["questions"] if q["kind"] != "contestavel"}
    by_id = {q["id"]: q for q in BANK["questions"]}
    for q in BANK_EN["questions"]:  # mesma pergunta, mesmos ids de opção, nos dois idiomas
        if q["id"] in by_id:
            assert [o["id"] for o in q["options"]] == [o["id"] for o in by_id[q["id"]]["options"]]
    h = [ANSWERS["answers"][f"h{n:02d}"] for n in range(1, 41)]
    assert h.count("option-a") == h.count("option-b") == 20


def test_answers_never_reach_the_spec():
    spec = blind_spec(BANK["questions"][40], PANEL, run_id="t", condition_id="B1")
    assert "answer" not in json.dumps(spec) and "gabarito" not in json.dumps(spec)


def test_protocol_order_interleaves_and_alternates():
    steps = [(s.question_id, s.condition_id) for s in protocol_order(["q01", "q02"])]
    assert steps == [("q01", "B1"), ("q01", "B2"), ("q02", "B2"), ("q02", "B1"),
                     ("q01", "B3"), ("q01", "E"), ("q02", "E"), ("q02", "B3")]


def test_pilot_order_is_blind_first_only():
    assert [(s.question_id, s.condition_id) for s in protocol_order(["q01", "g01"], blind_first_only=True)] == [("q01", "B1"), ("g01", "B1")]


def test_participants_have_neutral_labels():
    spec = blind_spec(BANK["questions"][0], PANEL, run_id="t", condition_id="B1")
    assert [p["id"] for p in spec["participants"]] == ["analista-1", "analista-2", "analista-3"]
    assert all(p["reasoning_effort"] == "default" and p["sampling_with_reasoning"] is False for p in spec["participants"])
    with pytest.raises(ValueError):
        blind_spec(BANK["questions"][0], PANEL, run_id="t", condition_id="E")


@pytest.mark.asyncio
async def test_batch_runs_four_conditions_and_resumes(tmp_path):
    runner = ExperimentRunner(tmp_path)
    batch = HerdBatch(runner, BANK, PANEL, run_id="piloto")
    report = await batch.run(["q01", "g01"], allow_live=False)
    assert len(report.ran) == 8 and all(status == "complete" for _, status in report.ran)
    assert not report.blocked
    e = json.loads((tmp_path / "experiments" / experiment_id("piloto", "q01", "E") / "spec.json").read_text())
    assert e["condition"] == {"id": "E", "exposure": "exposed", "tools": "off", "prior_experiment": "piloto-q01-b1"}
    again = await batch.run(["q01", "g01"], allow_live=False)
    assert not again.ran and len(again.existing) == 8


@pytest.mark.asyncio
async def test_derived_conditions_blocked_when_b1_missing(tmp_path):
    runner = ExperimentRunner(tmp_path)
    batch = HerdBatch(runner, BANK, PANEL, run_id="piloto")
    (tmp_path / "experiments" / "piloto-q01-b1").mkdir(parents=True)  # B1 que não fechou
    report = await batch.run(["q01"], allow_live=False)
    assert {expid for expid, _ in report.blocked} == {"piloto-q01-b3", "piloto-q01-e"}
    assert ("piloto-q01-b1", "unfinished") in report.existing


def test_plan_is_frozen_per_run(tmp_path):
    freeze_plan(tmp_path, "rodada", BANK, PANEL)
    freeze_plan(tmp_path, "rodada", BANK, PANEL)  # mesma configuração: aceita
    changed = json.loads(json.dumps(PANEL)) | {"sampling": {"temperature": 0.2, "top_p": 1.0, "max_tokens": 800}}
    with pytest.raises(ValueError, match="congelada"):
        freeze_plan(tmp_path, "rodada", BANK, changed)
