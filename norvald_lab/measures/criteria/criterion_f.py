"""Critério F — erros correlacionados: 9 juízes ≈ 2 votos (Kohli).

Braço de gabarito, só B1. Para cada par de participantes, a correlação
(phi) dos indicadores de erro nas perguntas com gabarito em que os dois
têm posição; ρ̄ = média dos pares definidos; N_eff = n/(1 + (n − 1)ρ̄), com
n = número de participantes.

Previsão: N_eff < n, limite superior do intervalo < n. Intervalo que inclui
n é não compatível.

As 6 declarações do TESE-005 §5 que devem acompanhar o N_eff são texto do
estudo, não saem daqui: o relatório deixa o lugar marcado.
"""

from __future__ import annotations

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.gabarito_errors import b1_errors
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.pairwise_dependence import add_binary_pairs, effective_n, mean_over_pairs, phi
from norvald_lab.measures.statistic import Statistic
from norvald_lab.measures.verdict import directional

PREFIX = "F|erro"


class CriterionF:
    letter = "F"
    source = "critério F (bloco 1.2); afirmação de Kohli et al."

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        sums = ClusterSums()
        agents: set[str] = set()
        for unit in (u for u in table.by_question_unit if table.answer(u[1]) is not None):
            errors = b1_errors(table, unit)
            agents |= set(errors)
            add_binary_pairs(sums, unit[1], PREFIX, errors)
            for agent, error in errors.items():
                sums.add(unit[1], f"F|taxa|{agent}|n")
                sums.add(unit[1], f"F|taxa|{agent}|s", error)
        n = len(agents)
        rho = lambda t: mean_over_pairs(sorted(agents), lambda i, j: phi(t, PREFIX, i, j))
        stats = {"rho_erro": Statistic(rho), "n_eff": Statistic(lambda t: effective_n(n, rho(t)))}
        for agent in sorted(agents):
            stats[f"taxa_erro|{agent}"] = Statistic.ratio(f"F|taxa|{agent}|s", f"F|taxa|{agent}|n")
        intervals = bootstrap.run(sums, stats)
        totals = sums.totals()
        pairs = {f"{i} × {j}": phi(totals, PREFIX, i, j) for i in sorted(agents) for j in sorted(agents) if i < j}
        return {
            "fonte": self.source,
            "medida": "ρ̄ dos indicadores de erro em B1 (gabarito) e N_eff = n/(1+(n−1)ρ̄)",
            "n_participantes": n,
            "rho_erro": intervals["rho_erro"].to_dict(),
            "n_eff": intervals["n_eff"].to_dict(),
            "correlacao_por_par": pairs,
            "pares_sem_correlacao_definida": sum(v is None for v in pairs.values()),
            "taxa_erro_por_participante": {a: intervals[f"taxa_erro|{a}"].to_dict() for a in sorted(agents)},
            "declaracoes_tese005_s5": "fora do código: anexar as 6 declarações do TESE-005 §5 ao relatar o N_eff",
            "veredito": directional(intervals["n_eff"], expected="abaixo", reference=float(n)) if n else "indeterminado (sem dados)",
        }
