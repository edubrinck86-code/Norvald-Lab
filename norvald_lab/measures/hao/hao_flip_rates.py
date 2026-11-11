"""Taxas de mudança (Hao et al., §3, item 1; Tabela 2).

Mudança espontânea (flip de SR) = nº de pares com a_sr ≠ a_0 / N. A mesma
conta com a_so e a_r dá as taxas só-posição e raciocínio. Denominador: todos
os pares do subconjunto. Também por modelo-alvo, porque aqui cada alvo é um
modelo diferente (protocolo §6: "a análise precisa ser por alvo").
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.hao.hao_unit import HaoUnit
from norvald_lab.measures.statistic import Statistic

FLIPS = {"sr": "asr", "so": "aso", "r": "ar"}


class HaoFlipRates:
    name = "taxas_de_mudanca"
    source = "Hao et al. (2026), §3 item 1, Tabela 2"

    def compute(self, units: list[HaoUnit], bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        models = sorted({u.model for u in units})
        for unit in units:
            for scope in ("todos", unit.model):
                sums.add(unit.cluster, f"{scope}|N")
                for flip, field in FLIPS.items():
                    sums.add(unit.cluster, f"{scope}|{flip}", float(getattr(unit, field) != unit.a0))
        stats = {f"{scope}|{flip}": Statistic.ratio(f"{scope}|{flip}", f"{scope}|N") for scope in ["todos", *models] for flip in FLIPS}
        intervals = bootstrap.run(sums, stats)
        return {
            "fonte": self.source,
            "todos": {flip: intervals[f"todos|{flip}"].to_dict() for flip in FLIPS},
            "por_modelo_alvo": {m: {flip: intervals[f"{m}|{flip}"].to_dict() for flip in FLIPS} for m in models},
        }
