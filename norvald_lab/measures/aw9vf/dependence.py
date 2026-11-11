"""Dependência e N_eff (344-66 itens 3–6; 344-71; 344-75; 344-83 itens 1–2).

- ρ̄_erro por condição: média dos phi par a par entre os vetores binários de
  erro, nas perguntas com gabarito. Par sem variância fica fora da média
  (como no critério F) e é contado.
- N_eff(c) = n / (1 + (n − 1) ρ̄_erro(c)), com n = tamanho do painel (os
  participantes distintos com posição em alguma das condições calculadas).
  O mesmo n em todas as condições, para a diferença só refletir o ρ̄.
- Δ_N_eff = N_eff(B1) − N_eff(E), IC bootstrap por pergunta. Sem teste de
  significância (344-77).
- ρ̄_comportamento: kappa de Fleiss de B1 nas contestáveis (FleissAgreement),
  descritivo; distância = ρ̄_comportamento − ρ̄_erro(B1), com IC.
- O bootstrap reamostra dentro de dois estratos, gabarito e contestável:
  a composição do estudo é fixa, e deixar a proporção entre eles variar
  misturaria a incerteza dos dois braços.
"""

from __future__ import annotations

from itertools import combinations

from norvald_lab.measures.aw9vf.fleiss_agreement import FleissAgreement
from norvald_lab.measures.aw9vf.neff_sweep import NeffSweep
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.gabarito_errors import condition_errors
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.pairwise_dependence import add_binary_pairs, effective_n, mean_over_pairs, phi
from norvald_lab.measures.statistic import Statistic

ERROR_CONDITIONS = ("B1", "B3", "EP", "E")


class Dependence:
    def __init__(self, bootstrap: ClusteredBootstrap):
        self.bootstrap = bootstrap

    def compute(self, table: ObservationTable, *, conditions: tuple[str, ...] = ERROR_CONDITIONS, behaviour: bool = True) -> dict:
        sums, agents = ClusterSums(), set()
        fleiss = FleissAgreement()
        for unit in table.by_question_unit:
            if table.answer(unit[1]) is not None:
                sums.touch(unit[1], stratum="gabarito")
                for condition in conditions:
                    errors = condition_errors(table, unit, condition)
                    agents |= set(errors)
                    add_binary_pairs(sums, unit[1], f"D|{condition}", errors, stratum="gabarito")
            elif behaviour and table.info(unit[1]).kind == "contestavel":
                sums.touch(unit[1], stratum="contestavel")
                fleiss.add(sums, unit[1], list(table.options(unit, "B1").values()), stratum="contestavel")
        ordered = sorted(agents)
        n = len(ordered)

        def rho(condition: str):
            return lambda t: mean_over_pairs(ordered, lambda i, j: phi(t, f"D|{condition}", i, j))

        stats = {}
        for condition in conditions:
            stats[f"rho|{condition}"] = Statistic(rho(condition))
            stats[f"neff|{condition}"] = Statistic(lambda t, c=condition: effective_n(n, rho(c)(t)) if n else None)
        if "B1" in conditions and "E" in conditions:
            stats["delta_neff"] = Statistic(lambda t: _difference(effective_n(n, rho("B1")(t)), effective_n(n, rho("E")(t))))
        if behaviour:
            stats["rho_comportamento"] = Statistic(fleiss.kappa)
            stats["concordancia_observada"] = Statistic(fleiss.observed)
            if "B1" in conditions:
                stats["distancia"] = Statistic(lambda t: _difference(fleiss.kappa(t), rho("B1")(t)))
        intervals = self.bootstrap.run(sums, stats)
        totals = sums.totals()
        out = {
            "n_painel": n,
            "perguntas_com_gabarito": sum(table.answer(u[1]) is not None for u in table.by_question_unit),
            "rho_erro": {c: intervals[f"rho|{c}"].to_dict() for c in conditions},
            "n_eff": {c: intervals[f"neff|{c}"].to_dict() for c in conditions},
            "pares_sem_correlacao_definida": {c: sum(phi(totals, f"D|{c}", i, j) is None for i, j in combinations(ordered, 2)) for c in conditions},
            "correlacao_por_par": {c: {f"{i} × {j}": phi(totals, f"D|{c}", i, j) for i, j in combinations(ordered, 2)} for c in conditions},
        }
        if "delta_neff" in intervals:
            out["delta_n_eff_B1_menos_E"] = intervals["delta_neff"].to_dict()
        anchors = {f"rho_erro_{c}": out["rho_erro"][c]["estimativa"] for c in conditions}
        if behaviour:
            out["rho_comportamento"] = {
                "medida": "kappa de Fleiss de B1 nas contestáveis (descritivo; fora da tabela de N_eff)",
                "contestaveis": int(totals.get("fleiss|itens", 0)),
                "kappa": intervals["rho_comportamento"].to_dict(),
                "concordancia_observada_P": intervals["concordancia_observada"].to_dict(),
                "leitura": "teto candidato, não piso (344-75, retratação declarada)",
            }
            if "distancia" in intervals:
                out["distancia_comportamento_menos_erro"] = {"definicao": "ρ̄_comportamento − ρ̄_erro(B1)", **intervals["distancia"].to_dict()}
        out["varredura_analitica"] = NeffSweep().table(n or 5, anchors)
        return out


def _difference(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a - b
