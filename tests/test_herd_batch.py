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
    # Contrato mudou de propósito em 11/11/2026 (5ª condição EP): a fase derivada tem três
    # condições e gira em quadrado latino pela posição da pergunta (ver schedule.py).
    steps = [(s.question_id, s.condition_id) for s in protocol_order(["q01", "q02"])]
    assert steps == [("q01", "B1"), ("q01", "B2"), ("q02", "B2"), ("q02", "B1"),
                     ("q01", "B3"), ("q01", "EP"), ("q01", "E"),
                     ("q02", "EP"), ("q02", "E"), ("q02", "B3")]


def test_pilot_order_is_blind_first_only():
    assert [(s.question_id, s.condition_id) for s in protocol_order(["q01", "g01"], blind_first_only=True)] == [("q01", "B1"), ("g01", "B1")]


def test_participants_have_neutral_labels():
    spec = blind_spec(BANK["questions"][0], PANEL, run_id="t", condition_id="B1")
    assert [p["id"] for p in spec["participants"]] == ["analista-1", "analista-2", "analista-3"]
    assert all(p["reasoning_effort"] == "default" and p["sampling_with_reasoning"] is False for p in spec["participants"])
    with pytest.raises(ValueError):
        blind_spec(BANK["questions"][0], PANEL, run_id="t", condition_id="E")


@pytest.mark.asyncio
async def test_batch_runs_five_conditions_and_resumes(tmp_path):
    runner = ExperimentRunner(tmp_path)
    batch = HerdBatch(runner, BANK, PANEL, run_id="piloto")
    report = await batch.run(["q01", "g01"], allow_live=False)
    assert len(report.ran) == 10 and all(status == "complete" for _, status in report.ran)
    assert not report.blocked
    e = json.loads((tmp_path / "experiments" / experiment_id("piloto", "q01", "E") / "spec.json").read_text())
    assert e["condition"] == {"id": "E", "exposure": "exposed", "tools": "off", "prior_experiment": "piloto-q01-b1"}
    again = await batch.run(["q01", "g01"], allow_live=False)
    assert not again.ran and len(again.existing) == 10


@pytest.mark.asyncio
async def test_derived_conditions_blocked_when_b1_missing(tmp_path):
    runner = ExperimentRunner(tmp_path)
    batch = HerdBatch(runner, BANK, PANEL, run_id="piloto")
    (tmp_path / "experiments" / "piloto-q01-b1").mkdir(parents=True)  # B1 que não fechou
    report = await batch.run(["q01"], allow_live=False)
    assert {expid for expid, _ in report.blocked} == {"piloto-q01-b3", "piloto-q01-ep", "piloto-q01-e"}
    assert ("piloto-q01-b1", "unfinished") in report.existing


def test_plan_is_frozen_per_run(tmp_path):
    freeze_plan(tmp_path, "rodada", BANK, PANEL)
    freeze_plan(tmp_path, "rodada", BANK, PANEL)  # mesma configuração: aceita
    changed = json.loads(json.dumps(PANEL)) | {"sampling": {"temperature": 0.2, "top_p": 1.0, "max_tokens": 800}}
    with pytest.raises(ValueError, match="congelada"):
        freeze_plan(tmp_path, "rodada", BANK, changed)


def test_english_panel_produces_an_english_spec():
    # 11/11/2026: coleta em inglês; nem o rótulo do participante pode ficar em português.
    panel = PANEL | {"language": "en", "instructions": "Choose exactly one option."}
    spec = blind_spec(BANK_EN["questions"][0], panel, run_id="t", condition_id="B1")
    assert spec["language"] == "en"
    assert [p["name"] for p in spec["participants"]] == ["Analyst 1", "Analyst 2", "Analyst 3"]
    assert "Analista" not in json.dumps(spec)
    assert "language" not in blind_spec(BANK["questions"][0], PANEL, run_id="t", condition_id="B1")


@pytest.mark.asyncio
async def test_english_batch_runs_end_to_end_in_demo(tmp_path):
    panel = PANEL | {"language": "en", "instructions": "Choose exactly one option."}
    bank = {"questions": [q for q in BANK_EN["questions"] if q["id"] in {"q01", "h01"}]}
    report = await HerdBatch(ExperimentRunner(tmp_path), bank, panel, run_id="en").run(["q01", "h01"], allow_live=False)
    assert len(report.ran) == 10 and not report.blocked
    for path in tmp_path.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "Reconsidere" not in text and "Você é" not in text


@pytest.mark.asyncio
async def test_derived_conditions_run_when_b1_incomplete(tmp_path, monkeypatch):
    # 12/11/2026, conf2: B1 "incomplete" bloqueava a pergunta inteira; o registro (344-79, item 2) manda seguir.
    runner = ExperimentRunner(tmp_path)
    batch = HerdBatch(runner, BANK, PANEL, run_id="piloto")
    real = batch._status
    monkeypatch.setattr(batch, "_status", lambda expid: "incomplete" if expid == "piloto-q01-b1" and real(expid) else real(expid))
    await batch.run(["q01"], allow_live=False, blind_first_only=True)
    report = await batch.run(["q01"], allow_live=False)
    assert not report.blocked
    assert {"piloto-q01-b3", "piloto-q01-ep", "piloto-q01-e"} <= {expid for expid, _ in report.ran}
