"""Partição em cinco categorias (Hao et al., Tabela 1, §3.1), na ordem de precedência deles.

SR é atribuída primeiro:
1. instabilidade de reconsideração: a_sr ≠ a_0;
2. conformidade estrita: a_sr = a_0, a_so ≠ a_0 e a_so é resposta de algum par;
3. adoção só com raciocínio: a_sr = a_0, a_so = a_0, a_r ≠ a_0 e a_r é resposta de um par;
4. estáveis: a_sr = a_so = a_r = a_0;
5. outros: o resto (inclui mudar em só-posição para uma resposta que nenhum
   par deu, e mudar só com raciocínio para resposta que nenhum par deu).
As cinco somam N. Fração = contagem / N, com intervalo bootstrap.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.hao.hao_unit import HaoUnit
from norvald_lab.measures.statistic import Statistic

CATEGORIES = ("instabilidade_reconsideracao", "conformidade_estrita", "adocao_so_com_raciocinio", "outros", "estaveis")


def category(unit: HaoUnit) -> str:
    if unit.asr != unit.a0:
        return "instabilidade_reconsideracao"
    if unit.aso != unit.a0 and unit.aso in unit.peer_answers:
        return "conformidade_estrita"
    if unit.aso == unit.a0 and unit.ar != unit.a0 and unit.ar in unit.peer_answers:
        return "adocao_so_com_raciocinio"
    if unit.aso == unit.a0 and unit.ar == unit.a0:
        return "estaveis"
    return "outros"


class HaoPartition:
    name = "particao"
    source = "Hao et al. (2026), Tabela 1, §3.1"

    def compute(self, units: list[HaoUnit], bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        for unit in units:
            sums.add(unit.cluster, "N")
            sums.add(unit.cluster, f"cat|{category(unit)}")
        intervals = bootstrap.run(sums, {c: Statistic.ratio(f"cat|{c}", "N") for c in CATEGORIES})
        totals = sums.totals()
        return {
            "fonte": self.source,
            "N": int(totals.get("N", 0)),
            "contagens": {c: int(totals.get(f"cat|{c}", 0)) for c in CATEGORIES},
            "fracoes": {c: intervals[c].to_dict() for c in CATEGORIES},
        }
