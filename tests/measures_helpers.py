"""Construtores das tabelas pequenas dos testes de medidas (sem RAW, sem provider).

`table({"q1": {"B1": "aabbb", "E": "bbbbb"}}, answers={"q1": "a"})`: cada
letra é a opção de um participante (p1, p2, ...), "-" é posição ausente.
"""

from __future__ import annotations

import json
from pathlib import Path

from norvald_lab.measures.observation import Observation
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.question_info import QuestionInfo


def option(letter: str) -> str | None:
    return None if letter == "-" else f"option-{letter}"


def obs(question, condition, participant, letter, *, answer=None, model=None, run="r", peer_order=(), justification="", indirect=False, kind=None, cost=0.0, attempts=1, attempt1_failed=False):
    chosen = option(letter)
    return Observation(
        run=run, question_id=question, kind=kind or ("gabarito" if answer else "contestavel"), category="", condition=condition,
        repetition="r0001", participant_id=participant, model=model or f"m{participant[1:]}", option=chosen, indirect=indirect,
        indirect_source="", correct=None if answer is None or chosen is None else chosen == option(answer), confidence="alta",
        justification=justification, peer_order=tuple(peer_order), attempts=attempts, attempt1_failed=attempt1_failed,
        cost=cost, status="ok" if chosen else "no_decision", validation_code="usable",
    )


def table(spec, answers=None, *, texts=None, peer_orders=None, justifications=None) -> ObservationTable:
    answers, texts = answers or {}, texts or {}
    peer_orders, justifications = peer_orders or {}, justifications or {}
    rows = []
    for question, by_condition in spec.items():
        for condition, letters in by_condition.items():
            for index, letter in enumerate(letters, start=1):
                pid = f"p{index}"
                rows.append(obs(question, condition, pid, letter, answer=answers.get(question),
                                peer_order=peer_orders.get((question, condition, pid), ()),
                                justification=justifications.get((question, condition, pid), "")))
    questions = {q: QuestionInfo(q, "gabarito" if q in answers else "contestavel", "", option(answers[q]) if q in answers else None, texts.get(q, "")) for q in spec}
    return ObservationTable(tuple(rows), questions, ("r",))


# --- RAW fabricado, para o carregador -------------------------------------------------

def contribution(target: str, text: str = "Escolha.") -> str:
    block = {"knowledge": [{"local_id": "k1", "type": "decision", "content": text, "confidence": "alta"}], "relations": [{"relation_type": "selects", "source": "k1", "target": target}]}
    return f"Prosa da justificativa.\n<<CONTRIBUTION>>\n{json.dumps(block)}\n<<END_CONTRIBUTION>>"


def base_context(extra_items=(), extra_relations=()) -> str:
    items = [{"id": "option-a", "type": "option", "content": "REST/JSON"}, {"id": "option-b", "type": "option", "content": "gRPC"}]
    return json.dumps({"question": "Protocolo?", "items": items + list(extra_items), "relations": list(extra_relations)})


def payload(run, question, condition, participant, *, content, attempt=1, error=None, model="modelo-x", cost=0.01, context=None, peer_order=()):
    expid = f"{run}-{question}-{condition.lower()}"
    return {
        "schema_version": "arof.raw.v4", "observation_id": f"{expid}-{participant}-{attempt}", "logical_execution_id": f"{expid}:1:{participant}",
        "attempt_index": attempt, "captured_at": f"2026-11-11T10:00:0{attempt}+00:00", "participant_id": participant, "task_id": question,
        "task_label": question, "experiment_id": expid, "condition_id": condition, "run_id": "r0001", "round_number": 1 if condition in ("B1", "B2") else 2,
        "requested_model": model, "requested_provider_kind": "openrouter",
        "request": {"context": {"working_context": context or base_context()}, "studio_metadata": {"peer_order": list(peer_order)}},
        "result": None if error else {"content": content, "metadata": {"raw_usage": {"cost": cost}}},
        "error": error,
    }


def write_experiment(root: Path, run: str, question: str, condition: str, payloads) -> Path:
    directory = root / "experiments" / f"{run}-{question}-{condition.lower()}" / "raw" / "r0001"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "observations.jsonl").write_text("".join(json.dumps(p) + "\n" for p in payloads), encoding="utf-8")
    return directory.parent.parent
