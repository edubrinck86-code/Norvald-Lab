"""Linha de base lexical: cosseno entre vetores TF-IDF (stdlib).

- tf = contagem bruta do token no texto;
- idf = ln((1 + N) / (1 + df)) + 1 (idf suavizado), com N e df contados
  num corpus de referência dado na construção — na medida, todas as
  justificativas da tabela. Ajustar o idf só nos 2 a 5 textos de uma
  pergunta daria pesos instáveis;
- cosseno entre os vetores tf·idf. Texto sem token: similaridade None.

Mede sobreposição de palavras, não de ideias: duas razões iguais ditas com
palavras diferentes saem distantes. Por isso a medida é exploratória.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Sequence

from norvald_lab.measures.reasons.reason_similarity import ReasonSimilarity
from norvald_lab.measures.reasons.tokenizer import tokenize, vocabulary


class TfidfCosineSimilarity(ReasonSimilarity):
    name = "tfidf-cosseno-v1"

    def __init__(self, corpus: Iterable[str]):
        documents = [set(tokenize(text)) for text in corpus]
        self.n_documents = len(documents)
        df = Counter(token for doc in documents for token in doc)
        self._df = df

    def idf(self, token: str) -> float:
        return math.log((1 + self.n_documents) / (1 + self._df.get(token, 0))) + 1

    def _vector(self, text: str, ignore: frozenset[str]) -> dict[str, float]:
        return {token: count * self.idf(token) for token, count in Counter(tokenize(text, ignore=ignore)).items()}

    def matrix(self, texts: Sequence[str], *, prompt: str = "") -> list[list[float | None]]:
        ignore = vocabulary(prompt)
        vectors = [self._vector(text, ignore) for text in texts]
        norms = [math.sqrt(sum(w * w for w in v.values())) for v in vectors]
        out: list[list[float | None]] = []
        for i, vi in enumerate(vectors):
            row: list[float | None] = []
            for j, vj in enumerate(vectors):
                if not norms[i] or not norms[j]:
                    row.append(None)
                else:
                    dot = sum(w * vj.get(token, 0.0) for token, w in vi.items())
                    row.append(dot / (norms[i] * norms[j]))
            out.append(row)
        return out

    def describe(self) -> dict:
        return {"metodo": self.name, "idf": "ln((1+N)/(1+df))+1 sobre todas as justificativas da tabela", "N_corpus": self.n_documents, "tokenizador": "norvald_lab.measures.reasons.tokenizer"}
