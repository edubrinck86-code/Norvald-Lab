"""Conferência algébrica entre os dois métodos (pedido de 11/11/2026).

Nos pares estáveis em autorreflexão (B3 = B1), o acerto em B3 é o de B1.
Então, por par, acerto(E) − acerto(B3) vale +1 numa transição W→C de B1
para E, −1 numa C→W e 0 no resto (sem mudança ou W→W). Somando:

    Δ_pares(acerto | estáveis em SR) = (#W→C − #C→W) / N_estáveis.

O lado esquerdo sai do nosso contraste genérico (IndicatorContrasts, sobre
`Observation.correct` da tabela); o direito, do classificador de transições
de Hao (`transition`, sobre a_0 e a_r das HaoUnit). São dois caminhos de
código sobre os mesmos pares; se divergirem, um deles está errado. Vale o
mesmo para Δ_posição (EP − B3) com a_so.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.hao.hao_unit import HaoUnit, hao_units, subset
from norvald_lab.measures.hao.transition import transition
from norvald_lab.measures.indicator_contrasts import IndicatorContrasts
from norvald_lab.measures.observation_table import ObservationTable

TOLERANCE = 1e-12
PAIRS = {"delta_pares": ("E", "ar"), "delta_posicao": ("EP", "aso")}


def _ours(table: ObservationTable, stable: list[HaoUnit]) -> dict[str, float | None]:
    sums = ClusterSums()
    rates = IndicatorContrasts(sums, "X", conditions=("B3", "EP", "E"), contrasts={"delta_pares": ("E", "B3"), "delta_posicao": ("EP", "B3")})
    for unit in stable:
        by_condition = table.by_question_unit[unit.question_unit]
        values = {c: float(by_condition[c][unit.participant_id].correct) for c in ("B3", "EP", "E")}
        rates.add(unit.cluster, values)
    totals = sums.totals()
    out = {}
    for name in PAIRS:
        num, den = rates.contrast_keys("todas", name)
        out[name] = totals[num] / totals[den] if totals.get(den) else None
    return out


def _hao(stable: list[HaoUnit]) -> dict[str, float | None]:
    out = {}
    for name, (_, field) in PAIRS.items():
        kinds = [transition(u.a0, getattr(u, field), u.answer) for u in stable]
        out[name] = (kinds.count("W→C") - kinds.count("C→W")) / len(stable) if stable else None
    return out


class CrossCheck:
    source = "Δ_pares(acerto) nos estáveis em SR = (W→C − C→W)/N_estáveis (álgebra)"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap | None = None) -> dict:
        out = {"fonte": self.source}
        for name in ("todas", "discordancia"):
            stable = [u for u in subset(hao_units(table), name) if u.answer is not None and u.sr_stable]
            ours, hao = _ours(table, stable), _hao(stable)
            out[name] = {
                "N_estaveis_sr": len(stable),
                "nosso_lado": ours,
                "lado_hao": hao,
                "iguais": all((ours[k] is None and hao[k] is None) or (ours[k] is not None and hao[k] is not None and abs(ours[k] - hao[k]) < TOLERANCE) for k in PAIRS),
            }
        return out
