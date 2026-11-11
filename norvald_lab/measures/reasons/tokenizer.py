"""Tokenizador da linha de base lexical (documentado porque o número depende dele).

Passos, nesta ordem:
1. normalização Unicode NFKD e remoção dos acentos (marcas combinantes);
2. minúsculas;
3. tokens = sequências de [a-z0-9] (todo o resto separa);
4. descarta tokens com menos de 2 caracteres;
5. descarta palavras vazias (lista curta em inglês e português, abaixo);
6. descarta o vocabulário do enunciado e das opções da pergunta, quando
   dado: quem escolhe a mesma opção repete as palavras dela, e isso não é
   razão em comum, é eco da pergunta.
Sem radicalização (stemming): sem dependência externa e sem regra de idioma.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Collection

STOPWORDS = frozenset("""
a an and are as at be been but by can could do does for from had has have if in into is it its may might more most no not of on or our so such than that the their them then there these they this those to was we were which while will with would you your
also because both each how only other over same should very what when where who why
o os as um uma uns umas de da do das dos e em no na nos nas por para com sem que se ao aos mais mas ou como seu sua seus suas ser ter esta este isso isto essa esse ja nao sim ha pelo pela pelos pelas entre sobre tambem quando onde qual quais
""".split())

_TOKEN = re.compile(r"[a-z0-9]+")


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def tokenize(text: str, *, ignore: Collection[str] = ()) -> list[str]:
    return [t for t in _TOKEN.findall(_fold(text)) if len(t) >= 2 and t not in STOPWORDS and t not in ignore]


def vocabulary(text: str) -> frozenset[str]:
    """O conjunto de tokens de um texto (para descontar o enunciado)."""
    return frozenset(tokenize(text))
