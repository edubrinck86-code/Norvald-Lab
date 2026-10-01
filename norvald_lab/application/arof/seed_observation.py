"""O que a semeadura da condição exposta fez com a leva cega.

Duas medidas por leva, as duas determinísticas e as duas sem juiz
semântico. Existem porque o estímulo da condição exposta é um documento
construído pelo Studio, e um documento construído pode alterar o que se
pretende medir antes de qualquer modelo deliberar.

**Colisão literal.** Dois participantes emitindo a mesma afirmação byte
a byte é a forma mais extrema de redundância observável, e a mais barata
de detectar: sem embedding, sem similaridade, sem modelo. É o piso de
redundância de conteúdo, e serve de linha de base que qualquer medida
estrutural de raciocínio precisa superar para valer a pena.

**Auditoria de normalização.** O Working Context funde unidades. Fundir
duas afirmações que declaram a MESMA posição é remover repetição, e é o
trabalho dele. Fundir duas que declaram posições DIFERENTES é apagar
divergência — e aí o painel da leva 2 vê menos desacordo do que existia,
por decisão do instrumento e não dos participantes.

O critério é mecânico porque o desenho da tarefa o tornou mecânico: a
posição é a relação `decision --selects--> option`, não o texto.

Nada aqui chega ao agente. O registro é do experimento; o produto não
muda de comportamento por existir esta medição.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Mapping, Sequence

SEED_OBSERVATION_SCHEMA_VERSION = "arof.seed.v1"


def _normalizar(conteudo: str) -> str:
    return " ".join(str(conteudo or "").split()).casefold()


@dataclass(frozen=True)
class ColisaoLiteral:
    """Um par de autores que declarou conteúdo idêntico na mesma leva.

    Guarda os autores e a contagem, nunca o texto: o conteúdo é do
    usuário, e a taxa é o que a análise precisa.
    """

    autor_a: str
    autor_b: str
    unidades: int

    def to_dict(self) -> dict[str, Any]:
        return {"autor_a": self.autor_a, "autor_b": self.autor_b, "unidades": self.unidades}


@dataclass(frozen=True)
class SeedObservation:
    schema_version: str = SEED_OBSERVATION_SCHEMA_VERSION
    item_id: str = ""
    leva: int = 1
    autores: tuple[str, ...] = ()
    autores_semeados: tuple[str, ...] = ()
    colisoes: tuple[ColisaoLiteral, ...] = ()
    unidades_em_colisao: int = 0
    posicoes_declaradas: int = 0
    posicoes_no_contexto: int = 0
    fusoes_destrutivas: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "item_id": self.item_id,
            "leva": self.leva,
            "autores": list(self.autores),
            "autores_semeados": list(self.autores_semeados),
            "colisoes": [c.to_dict() for c in self.colisoes],
            "unidades_em_colisao": self.unidades_em_colisao,
            "posicoes_declaradas": self.posicoes_declaradas,
            "posicoes_no_contexto": self.posicoes_no_contexto,
            "fusoes_destrutivas": self.fusoes_destrutivas,
        }


def colisoes_literais(
    conteudo_por_autor: Mapping[str, Sequence[tuple[str, str]]],
) -> tuple[tuple[ColisaoLiteral, ...], int]:
    """Pares de autores com unidades `(tipo, conteúdo)` idênticas.

    A comparação normaliza espaço e caixa, e nada além disso. Qualquer
    tolerância a mais deixaria de ser colisão literal e passaria a ser
    julgamento de semelhança, que é outra medida e exige outra defesa.
    """
    chaves = {
        autor: {(str(tipo), _normalizar(conteudo)) for tipo, conteudo in unidades}
        for autor, unidades in conteudo_por_autor.items()
    }
    encontradas: list[ColisaoLiteral] = []
    em_colisao: set[tuple[str, str]] = set()
    for a, b in combinations(sorted(chaves), 2):
        comuns = chaves[a] & chaves[b]
        if not comuns:
            continue
        encontradas.append(ColisaoLiteral(a, b, len(comuns)))
        em_colisao |= comuns
    return tuple(encontradas), len(em_colisao)

