"""Dano (H) e benefício (B) padronizados por estrato de apoio (Hao et al., §4.2, Ap. D).

Para X = só-posição (EP, a_so) e X = raciocínio (E, a_r), entre os pares
estáveis em autorreflexão (a_sr = a_0), perguntas com gabarito:
- H: população = a_0 certa; evento = a_X errada (C→W).
- B: população = a_0 errada E pelo menos um par certo em B1; evento = a_X certa (W→C).
Estrato s = quantos pares deram a mesma resposta do alvo em B1.

Padronização: H* = Σ_s w_s H_s e B* = Σ_s w_s B_s, com
w_s = (n_H,s + n_B,s) / (N_H + N_B). Os pesos saem das somas, então são
recalculados em cada réplica do bootstrap, como no paper.

Estrato em que H_s ou B_s não existe (n zero de um dos lados) fica fora e os
pesos são renormalizados sobre os estratos restantes. No paper isso não
aparece (os estratos 0–3 tinham os dois lados); aqui acontece no subconjunto
"todas" com o estrato de unanimidade (s = n − 1): com todos os pares na
resposta errada do alvo não existe par certo, então B não existe ali. Os
estratos usados e os excluídos ficam no relatório.

"Evento" é qualquer C→W (ou W→C) em X, não só a adoção da resposta de um
par: o protocolo diz "C→W entre alvos inicialmente certos e estáveis", sem
exigir que a resposta nova seja de um par.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.hao.hao_unit import HaoUnit
from norvald_lab.measures.statistic import Statistic, Totals

EXPOSURES = {"so": "aso", "r": "ar"}


def _strata(t: Totals, x: str, max_s: int) -> list[int]:
    return [s for s in range(max_s + 1) if t.get(f"{x}|H|n|{s}", 0) > 0 and t.get(f"{x}|B|n|{s}", 0) > 0]


def standardized(t: Totals, x: str, side: str, max_s: int) -> float | None:
    strata = _strata(t, x, max_s)
    if not strata:
        return None
    weights = {s: t[f"{x}|H|n|{s}"] + t[f"{x}|B|n|{s}"] for s in strata}
    total = sum(weights.values())
    return sum(weights[s] / total * t.get(f"{x}|{side}|e|{s}", 0.0) / t[f"{x}|{side}|n|{s}"] for s in strata)


def _difference(x: str, max_s: int):
    def compute(t: Totals) -> float | None:
        h, b = standardized(t, x, "H", max_s), standardized(t, x, "B", max_s)
        return None if h is None or b is None else h - b
    return compute


class HaoHarmBenefit:
    name = "dano_beneficio"
    source = "Hao et al. (2026), §4.2 e Ap. D, Tabela 3"

    def compute(self, units: list[HaoUnit], bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        max_s = max((len(u.peer_answers) for u in units), default=0)
        for unit in units:
            if unit.answer is None:
                continue
            sums.touch(unit.cluster)
            if not unit.sr_stable:
                continue
            s = unit.support
            if unit.is_correct(unit.a0):
                side = "H"
            elif any(unit.is_correct(peer) for peer in unit.peer_answers):
                side = "B"
            else:
                continue
            for x, field in EXPOSURES.items():
                after = getattr(unit, field)
                event = not unit.is_correct(after) if side == "H" else unit.is_correct(after)
                sums.add(unit.cluster, f"{x}|{side}|n|{s}")
                sums.add(unit.cluster, f"{x}|{side}|e|{s}", float(event))
                sums.add(unit.cluster, f"{x}|{side}|N")
                sums.add(unit.cluster, f"{x}|{side}|E", float(event))
        stats = {}
        for x in EXPOSURES:
            stats[f"{x}|H"] = Statistic(lambda t, x=x: standardized(t, x, "H", max_s), f"{x}|H|N")
            stats[f"{x}|B"] = Statistic(lambda t, x=x: standardized(t, x, "B", max_s), f"{x}|B|N")
            stats[f"{x}|H-B"] = Statistic(_difference(x, max_s))
            stats[f"{x}|H_bruto"] = Statistic.ratio(f"{x}|H|E", f"{x}|H|N")
            stats[f"{x}|B_bruto"] = Statistic.ratio(f"{x}|B|E", f"{x}|B|N")
        intervals = bootstrap.run(sums, stats)
        totals = sums.totals()
        out = {"fonte": self.source}
        for x, label in (("so", "so_posicao_EP"), ("r", "raciocinio_E")):
            used = _strata(totals, x, max_s)
            weight_total = sum(totals[f"{x}|H|n|{s}"] + totals[f"{x}|B|n|{s}"] for s in used)
            out[label] = {
                "H_padronizado": intervals[f"{x}|H"].to_dict(),
                "B_padronizado": intervals[f"{x}|B"].to_dict(),
                "H_menos_B": intervals[f"{x}|H-B"].to_dict(),
                "H_bruto": intervals[f"{x}|H_bruto"].to_dict(),
                "B_bruto": intervals[f"{x}|B_bruto"].to_dict(),
                "estratos_usados": used,
                "pesos": {str(s): (totals[f"{x}|H|n|{s}"] + totals[f"{x}|B|n|{s}"]) / weight_total for s in used},
                "estratos_excluidos": {str(s): {"n_H": int(totals.get(f"{x}|H|n|{s}", 0)), "n_B": int(totals.get(f"{x}|B|n|{s}", 0))}
                                       for s in range(max_s + 1) if s not in used and (totals.get(f"{x}|H|n|{s}", 0) or totals.get(f"{x}|B|n|{s}", 0))},
            }
        return out
