"""Taxa de conformidade estrita (Hao et al., Eq. 1).

N_strict / N_SR-stable: o denominador são os pares estáveis em
autorreflexão (a_sr = a_0), não todos. Também por modelo-alvo.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.hao.hao_partition import category
from norvald_lab.measures.hao.hao_unit import HaoUnit
from norvald_lab.measures.statistic import Statistic


class HaoStrictConformity:
    name = "conformidade_estrita"
    source = "Hao et al. (2026), Eq. 1"

    def compute(self, units: list[HaoUnit], bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        models = sorted({u.model for u in units})
        for unit in units:
            sums.touch(unit.cluster)
            if not unit.sr_stable:
                continue
            for scope in ("todos", unit.model):
                sums.add(unit.cluster, f"{scope}|estaveis_sr")
                sums.add(unit.cluster, f"{scope}|estrita", float(category(unit) == "conformidade_estrita"))
        stats = {scope: Statistic.ratio(f"{scope}|estrita", f"{scope}|estaveis_sr") for scope in ["todos", *models]}
        intervals = bootstrap.run(sums, stats)
        totals = sums.totals()
        return {
            "fonte": self.source,
            "N_estrita": int(totals.get("todos|estrita", 0)),
            "N_estaveis_sr": int(totals.get("todos|estaveis_sr", 0)),
            "taxa": intervals["todos"].to_dict(),
            "por_modelo_alvo": {m: intervals[m].to_dict() for m in models},
        }
