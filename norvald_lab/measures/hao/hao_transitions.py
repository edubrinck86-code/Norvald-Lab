"""Transições C→W / W→C / W→W por coorte (Hao et al., §3 item 3; Tabela 4).

Coortes, da partição: instabilidade (transição a_0 → a_sr), conformidade
estrita (a_0 → a_so) e adoção só com raciocínio (a_0 → a_r). Em cada coorte,
parcela = nº da transição / n da coorte ("within each event cohort"). Também
a parcela W→C entre C→W + W→C, como na tabela por modelo do protocolo.

Só perguntas com gabarito: sem gabarito não há C nem W.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.hao.hao_partition import category
from norvald_lab.measures.hao.hao_unit import HaoUnit
from norvald_lab.measures.hao.transition import transition
from norvald_lab.measures.statistic import Statistic

COHORTS = {"instabilidade_reconsideracao": "asr", "conformidade_estrita": "aso", "adocao_so_com_raciocinio": "ar"}
KINDS = ("C→W", "W→C", "W→W")


class HaoTransitions:
    name = "transicoes"
    source = "Hao et al. (2026), §3 item 3, Tabela 4"

    def compute(self, units: list[HaoUnit], bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        for unit in units:
            if unit.answer is None:
                continue
            sums.touch(unit.cluster)
            cohort = category(unit)
            if cohort not in COHORTS:
                continue
            kind = transition(unit.a0, getattr(unit, COHORTS[cohort]), unit.answer)
            sums.add(unit.cluster, f"{cohort}|n")
            sums.add(unit.cluster, f"{cohort}|{kind}")
        stats = {}
        for cohort in COHORTS:
            for kind in KINDS:
                stats[f"{cohort}|{kind}"] = Statistic.ratio(f"{cohort}|{kind}", f"{cohort}|n")
            stats[f"{cohort}|W→C_entre_C→W_e_W→C"] = Statistic(lambda t, c=cohort: None if not (t.get(f"{c}|C→W", 0) + t.get(f"{c}|W→C", 0)) else t.get(f"{c}|W→C", 0) / (t.get(f"{c}|C→W", 0) + t.get(f"{c}|W→C", 0)))
        intervals = bootstrap.run(sums, stats)
        totals = sums.totals()
        return {
            "fonte": self.source,
            "coortes": {
                cohort: {
                    "n": int(totals.get(f"{cohort}|n", 0)),
                    "contagens": {kind: int(totals.get(f"{cohort}|{kind}", 0)) for kind in KINDS},
                    "parcelas": {kind: intervals[f"{cohort}|{kind}"].to_dict() for kind in KINDS},
                    "parcela_W→C_entre_C→W_e_W→C": intervals[f"{cohort}|W→C_entre_C→W_e_W→C"].to_dict(),
                }
                for cohort in COHORTS
            },
        }
