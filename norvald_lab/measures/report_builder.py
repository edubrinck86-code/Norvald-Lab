"""Monta o relatório JSON com todas as medidas, a partir de uma tabela.

Variantes da regra 3: "com_indiretas" (a seleção indireta resolvida um
passo conta como posição) e "sem_indiretas" (essas linhas ficam sem
posição). Quando a tabela não tem nenhuma seleção indireta as duas são a
mesma conta; a segunda sai como referência à primeira, sem recalcular.

Hao et al. em dois subconjuntos rotulados: "todas" e "discordancia".
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from norvald_lab.measures.attempts_summary import AttemptsSummary
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.conditions import CONDITIONS, CONTRASTS
from norvald_lab.measures.criteria import CRITERIA
from norvald_lab.measures.cross_check import CrossCheck
from norvald_lab.measures.hao import HAO_MEASURES
from norvald_lab.measures.hao.hao_unit import SUBSETS, hao_units, subset
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.reasons.same_answer_reasons import SameAnswerReasons

SCHEMA = "norvald.lab.herd.measures.v1"
SAME = {"igual_a": "com_indiretas", "motivo": "nenhuma seleção indireta na tabela"}


def table_summary(table: ObservationTable) -> dict:
    questions = {row.question_id for row in table.rows}
    return {
        "linhas": len(table.rows),
        "perguntas": len(questions),
        "perguntas_por_tipo": dict(sorted(Counter(table.info(q).kind for q in questions).items())),
        "perguntas_com_gabarito": sum(table.answer(q) is not None for q in questions),
        "linhas_por_condicao": {c: sum(r.condition == c for r in table.rows) for c in CONDITIONS},
        "sem_posicao_por_condicao": {c: sum(r.condition == c and r.option is None for r in table.rows) for c in CONDITIONS},
        "selecoes_indiretas": table.indirect_rows,
        "selecoes_indiretas_da_propria_decisao": sum(r.indirect and r.option is not None and r.indirect_source == r.participant_id for r in table.rows),
    }


class MeasuresReport:
    def __init__(self, bootstrap: ClusteredBootstrap, reasons: SameAnswerReasons | None = None):
        self.bootstrap = bootstrap
        self.reasons = reasons or SameAnswerReasons()

    def _variants(self, table: ObservationTable, compute) -> dict:
        out = {"com_indiretas": compute(table)}
        out["sem_indiretas"] = SAME if table.indirect_rows == 0 else compute(table.without_indirect())
        return out

    def _hao(self, table: ObservationTable) -> dict:
        units = hao_units(table)
        out = {"n_pares_agente_pergunta": {name: len(subset(units, name)) for name in SUBSETS}}
        for measure in HAO_MEASURES:
            out[measure.name] = {name: measure.compute(subset(units, name), self.bootstrap) for name in SUBSETS}
        return out

    def build(self, table: ObservationTable) -> dict:
        return {
            "schema": SCHEMA,
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "rodadas": list(table.runs),
            "bootstrap": self.bootstrap.describe(),
            "contrastes": {name: f"M({a}) − M({b})" for name, (a, b) in CONTRASTS.items()},
            "mapeamento_hao": {"a_0": "B1", "a_sr": "B3", "a_so": "EP", "a_r": "E"},
            "tabela": table_summary(table),
            "tentativas_e_custo": AttemptsSummary().compute(table),
            "criterios": {c.letter: self._variants(table, lambda t, c=c: c.compute(t, self.bootstrap)) for c in CRITERIA},
            "hao": self._variants(table, self._hao),
            "conferencia_algebrica": self._variants(table, lambda t: CrossCheck().compute(t, self.bootstrap)),
            "razoes": self._variants(table, lambda t: self.reasons.compute(t, self.bootstrap)),
        }
