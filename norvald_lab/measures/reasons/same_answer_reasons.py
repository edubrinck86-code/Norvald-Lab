"""Mesma resposta, razões diferentes (pergunta do Eduardo, 11/11/2026; EXPLORATÓRIA).

Hao et al. nunca leem o conteúdo do raciocínio: medem só a letra. Aqui, para
cada pergunta e condição, entre os participantes que escolheram a MESMA
opção, a similaridade média, par a par, das justificativas
(`Observation.justification`).

Por pergunta e condição sai:
- n_concordantes: participantes num grupo de opção com dois ou mais;
- similaridade média entre concordantes (pares dentro do mesmo grupo);
- similaridade média entre discordantes e entre todos os pares, para referência;
- concordancia_com_razoes_diversas: há concordantes e a similaridade média
  entre eles fica abaixo do limiar. O limiar é PROVISÓRIO (0,2 por padrão,
  parâmetro): não há critério aprovado para ele.

E a pergunta de fundo — a exposição faz as razões convergirem? — como
contraste pareado por pergunta: E − B1 (e E − B3, que desconta a
reconsideração sozinha), na similaridade entre concordantes e entre todos
os pares, com intervalo bootstrap por pergunta.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.conditions import CONDITIONS
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.reasons.reason_similarity import ReasonSimilarity
from norvald_lab.measures.reasons.tfidf_similarity import TfidfCosineSimilarity
from norvald_lab.measures.statistic import Statistic

DEFAULT_THRESHOLD = 0.2
CONVERGENCE = {"E_menos_B1": ("E", "B1"), "E_menos_B3": ("E", "B3")}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


class SameAnswerReasons:
    source = "pergunta do Eduardo (11/11/2026); exploratória, fora de Hao et al."

    def __init__(self, similarity: ReasonSimilarity | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.similarity, self.threshold = similarity, threshold

    def _cell(self, rows, prompt: str, similarity: ReasonSimilarity) -> dict:
        rows = [row for row in rows if row.option is not None]
        matrix = similarity.matrix([row.justification for row in rows], prompt=prompt)
        agree, disagree = [], []
        for i, j in combinations(range(len(rows)), 2):
            value = matrix[i][j]
            if value is None:
                continue
            (agree if rows[i].option == rows[j].option else disagree).append(value)
        groups = defaultdict(int)
        for row in rows:
            groups[row.option] += 1
        n_agreeing = sum(size for size in groups.values() if size >= 2)
        mean_agree = _mean(agree)
        return {
            "n_participantes": len(rows),
            "n_concordantes": n_agreeing,
            "pares_concordantes": len(agree),
            "similaridade_concordantes": mean_agree,
            "similaridade_discordantes": _mean(disagree),
            "similaridade_todos": _mean(agree + disagree),
            "concordancia_com_razoes_diversas": None if mean_agree is None else mean_agree < self.threshold,
        }

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        similarity = self.similarity or TfidfCosineSimilarity(row.justification for row in table.rows if row.justification)
        sums = ClusterSums()
        agree = IndicatorContrasts(sums, "R.concordantes", contrasts=CONVERGENCE)
        everyone = IndicatorContrasts(sums, "R.todos", contrasts=CONVERGENCE)
        diverse = IndicatorContrasts(sums, "R.diversas", contrasts={})
        per_question = {}
        for unit, by_condition in table.by_question_unit.items():
            prompt = table.info(unit[1]).text
            cells = {c: self._cell(list(by_condition.get(c, {}).values()), prompt, similarity) for c in CONDITIONS if c in by_condition}
            per_question["/".join(unit)] = cells
            agree.add(unit[1], {c: cell["similaridade_concordantes"] for c, cell in cells.items()})
            everyone.add(unit[1], {c: cell["similaridade_todos"] for c, cell in cells.items()})
            diverse.add(unit[1], {c: None if cell["concordancia_com_razoes_diversas"] is None else float(cell["concordancia_com_razoes_diversas"]) for c, cell in cells.items()})
        stats: dict[str, Statistic] = agree.statistics() | everyone.statistics() | diverse.statistics()
        intervals = bootstrap.run(sums, stats)
        return {
            "fonte": self.source,
            "exploratoria": True,
            "similaridade": similarity.describe(),
            "limiar_provisorio": self.threshold,
            "resumo": {
                "similaridade_concordantes": agree.organize(intervals).get("todas", {}),
                "similaridade_todos_os_pares": everyone.organize(intervals).get("todas", {}),
                "fracao_com_razoes_diversas": diverse.organize(intervals).get("todas", {}).get("niveis", {}),
            },
            "por_pergunta": per_question,
        }
