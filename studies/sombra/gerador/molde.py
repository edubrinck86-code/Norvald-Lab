"""Molde de um par clássico × sorteado (tese 4, sombra da memória).

Um molde guarda a estrutura de um problema clássico do MMLU-Pro: o enunciado com
lacunas, os parâmetros originais, as faixas do sorteio, a fórmula que calcula o
gabarito e as regras dos distratores (erros típicos). Nenhuma pergunta é escrita
à mão pelo Opus: o conteúdo concreto vem do sorteio e o gabarito, do cálculo
(decisão de 15/11/2026, para não levar a memória de treino do redator ao bloco novo).
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple


@dataclass(frozen=True)
class Molde:
    classico_id: str                     # id da pergunta de origem no conf2-mmlu
    area: str
    enunciado: str                       # str.format com os nomes dos parâmetros
    originais: Dict[str, float]          # valores do enunciado publicado
    faixas: Dict[str, Tuple[float, float, int]]  # (mínimo, máximo, casas decimais)
    resposta: Callable[[Dict[str, float]], float]
    erros: List[Callable[[Dict[str, float]], float]] = field(default_factory=list)
    formato: str = "{:.2f}"              # como a opção aparece
    nomes: Dict[str, List[str]] = field(default_factory=dict)  # parâmetros de texto (nomes próprios)
