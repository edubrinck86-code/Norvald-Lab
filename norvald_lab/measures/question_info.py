"""O que a análise sabe de uma pergunta além das respostas: tipo, categoria, gabarito, texto."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionInfo:
    question_id: str
    kind: str = "desconhecido"
    category: str = ""
    answer: str | None = None  # id da opção certa; nunca entra em prompt, só aqui
    text: str = ""  # enunciado + opções, para a medida de razões descontar o vocabulário dado
