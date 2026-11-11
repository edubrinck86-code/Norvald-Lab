"""Interface da similaridade entre justificativas.

Hoje só existe a linha de base lexical (TF-IDF). A interface é pequena de
propósito, para encaixar depois um modelo de embeddings sem tocar na medida:
recebe os textos e o enunciado da pergunta, devolve a matriz de
similaridade (simétrica, diagonal 1, None quando não há como comparar —
por exemplo um texto sem nenhum token).

`prompt` é o enunciado + opções. O método lexical o usa para descontar o
vocabulário dado; um modelo de embeddings pode ignorá-lo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class ReasonSimilarity(ABC):
    name: str = ""

    @abstractmethod
    def matrix(self, texts: Sequence[str], *, prompt: str = "") -> list[list[float | None]]:
        ...

    def describe(self) -> dict:
        return {"metodo": self.name}
