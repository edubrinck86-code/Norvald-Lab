"""Critério E — o tamanho efetivo depende do alvo e do método (2609.21277).

Dois objetos distintos (TESE-005 §5), lado a lado, em B1:
- dependência de POSIÇÕES nas contestáveis: ρ̄_pos = média dos kappas de
  Cohen entre pares de participantes, sobre as opções escolhidas;
- dependência de ERROS nas perguntas de gabarito: ρ̄_erro (phi, o mesmo de
  F) e, para comparar objeto com objeto pelo mesmo estimador, o kappa dos
  rótulos certo/errado.
Cada um vira N_eff = n/(1 + (n − 1)ρ̄).

O bootstrap reamostra dentro de cada tipo (contestável, gabarito), para
que a proporção entre os dois braços fique a do banco.

O critério diz "diferem de forma relevante (limiar a definir)": aqui saem os
números e as diferenças com intervalo; o veredito fica "a definir".
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.gabarito_errors import b1_errors
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.pairwise_dependence import add_binary_pairs, add_label_pairs, agreement, effective_n, kappa, mean_over_pairs, phi
from norvald_lab.measures.statistic import Statistic
from norvald_lab.measures.verdict import A_DEFINIR

POS, ERR, ERR_K = "E|pos", "E|erro", "E|erro_kappa"


def _difference(a, b):
    return lambda t: None if (x := a(t)) is None or (y := b(t)) is None else x - y


class CriterionE:
    letter = "E"
    source = "critério E (bloco 1.2); afirmação de 2609.21277"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        agents: set[str] = set()
        labels: set[str] = set()
        for unit, by_condition in table.by_question_unit.items():
            cluster = unit[1]
            if table.answer(cluster) is not None:
                errors = b1_errors(table, unit)
                agents |= set(errors)
                add_binary_pairs(sums, cluster, ERR, errors, stratum="gabarito")
                add_label_pairs(sums, cluster, ERR_K, {a: "W" if e else "C" for a, e in errors.items()}, stratum="gabarito")
            elif table.info(cluster).kind == "contestavel":
                positions = {row.agent: row.option for row in by_condition.get("B1", {}).values() if row.option is not None}
                agents |= set(positions)
                labels |= set(positions.values())
                add_label_pairs(sums, cluster, POS, positions, stratum="contestavel")
        n = len(agents)
        ordered, option_labels = sorted(agents), sorted(labels)
        rho_pos = lambda t: mean_over_pairs(ordered, lambda i, j: kappa(t, POS, i, j, option_labels))
        rho_err = lambda t: mean_over_pairs(ordered, lambda i, j: phi(t, ERR, i, j))
        rho_err_k = lambda t: mean_over_pairs(ordered, lambda i, j: kappa(t, ERR_K, i, j, ("C", "W")))
        neff = lambda rho: (lambda t: effective_n(n, rho(t)))
        stats = {
            "rho_posicoes_kappa": Statistic(rho_pos),
            "concordancia_posicoes": Statistic(lambda t: mean_over_pairs(ordered, lambda i, j: agreement(t, POS, i, j))),
            "rho_erros_phi": Statistic(rho_err),
            "rho_erros_kappa": Statistic(rho_err_k),
            "n_eff_posicoes": Statistic(neff(rho_pos)),
            "n_eff_erros_phi": Statistic(neff(rho_err)),
            "n_eff_erros_kappa": Statistic(neff(rho_err_k)),
            "dif_rho_kappa_posicoes_menos_erros": Statistic(_difference(rho_pos, rho_err_k)),
            "dif_n_eff_posicoes_menos_erros_phi": Statistic(_difference(neff(rho_pos), neff(rho_err))),
        }
        intervals = bootstrap.run(sums, stats)
        strata = sums.strata()
        return {
            "fonte": self.source,
            "medida": "dependência de posições (kappa, contestáveis) × dependência de erros (phi e kappa, gabarito), em B1",
            "n_participantes": n,
            "perguntas": {"contestaveis": sum(s == "contestavel" for s in strata.values()), "gabarito": sum(s == "gabarito" for s in strata.values())},
            "resultado": {name: interval.to_dict() for name, interval in intervals.items()},
            "limiar": A_DEFINIR,
            "veredito": A_DEFINIR,
        }
