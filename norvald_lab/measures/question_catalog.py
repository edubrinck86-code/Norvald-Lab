"""Junta bancos e gabaritos num catálogo por id de pergunta.

O banco vem primeiro do plano congelado da rodada (studies/<run>/plan.json,
gravado pelo `norvald-lab herd`): é o banco que a coleta usou de fato. Os
bancos passados à mão só completam perguntas que o plano não traz (rodadas
antigas, sem plano). O gabarito vem sempre de arquivo à parte, porque nunca
fez parte do plano nem do prompt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from norvald_lab.measures.question_info import QuestionInfo


def _read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _text(question: Mapping) -> str:
    options = " ".join(str(o.get("content", "")) for o in question.get("options", []))
    return f"{question.get('question', '')} {options}".strip()


class QuestionCatalog:
    def __init__(self, questions: Mapping[str, QuestionInfo]):
        self.questions = dict(questions)

    def get(self, question_id: str) -> QuestionInfo:
        return self.questions.get(question_id) or QuestionInfo(question_id)

    @classmethod
    def from_files(cls, root: Path, runs: Iterable[str], bank_paths: Iterable[Path] = (), answer_paths: Iterable[Path] = ()) -> "QuestionCatalog":
        banks = []
        for run in runs:
            plan = Path(root) / "studies" / run / "plan.json"
            if plan.exists():
                banks.append(_read(plan)["bank"])
        banks += [_read(path) for path in bank_paths if Path(path).exists()]
        answers: dict[str, str] = {}
        for path in answer_paths:
            if Path(path).exists():
                answers.update(_read(path)["answers"])
        questions: dict[str, QuestionInfo] = {}
        for bank in banks:
            for question in bank.get("questions", []):
                questions.setdefault(question["id"], QuestionInfo(
                    question_id=question["id"], kind=question.get("kind", "desconhecido"),
                    category=question.get("category", ""), answer=answers.get(question["id"]), text=_text(question)))
        for question_id, answer in answers.items():  # gabarito sem banco: ainda dá para medir acerto
            questions.setdefault(question_id, QuestionInfo(question_id, kind="gabarito", answer=answer))
        return cls(questions)
