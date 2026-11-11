"""J — quem convenceu quem (exploratória, regra 4; sem veredito).

Para quem mudou em E (posição em E ≠ própria B1, as duas válidas):
1. para a posição de qual par foi: os "portadores" são os pares cuja B1 é a
   opção adotada. Crédito 1/k para cada um dos k portadores, somado por
   modelo de origem → modelo de destino. Mudança para uma opção que nenhum
   par tinha em B1 é contada à parte.
2. a posição do par na lista pesa? A ordem dos pares em E é sorteada por
   execução e gravada (peer_order, Lab PR #4 e #7). Sem efeito de ordem, a
   chance de o par na posição r ser portador é k/m (m pares). Comparamos o
   observado com esse esperado em cada posição; o resumo é
   (observado − esperado)/nº de mudanças, na primeira e na última posição
   (primazia e recência), com intervalo bootstrap.

EP usa a mesma ordem sorteada (só posições), então sai também, ao lado.
"""

from __future__ import annotations

from collections import defaultdict

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.statistic import Statistic, Totals

CONDITIONS_WITH_PEERS = ("E", "EP")


def _excess(prefix: str, which: str):
    def compute(t: Totals) -> float | None:
        n = t.get(f"{prefix}|ordenadas", 0.0)
        return None if n == 0 else (t.get(f"{prefix}|{which}|obs", 0.0) - t.get(f"{prefix}|{which}|esp", 0.0)) / n
    return compute


class CriterionJ:
    letter = "J"
    source = "J (bloco 1.2, regra 4), exploratória"

    def compute(self, table: ObservationTable, bootstrap: ClusteredBootstrap) -> dict:
        out = {"fonte": self.source, "exploratoria": True, "veredito": None, "por_condicao": {}}
        for condition in CONDITIONS_WITH_PEERS:
            out["por_condicao"][condition] = self._condition(table, bootstrap, condition)
        return out

    def _condition(self, table: ObservationTable, bootstrap: ClusteredBootstrap, condition: str) -> dict:
        sums = ClusterSums()
        prefix = f"J|{condition}"
        credit: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        by_rank_obs: dict[int, float] = defaultdict(float)
        by_rank_exp: dict[int, float] = defaultdict(float)
        for unit, by_condition in table.by_question_unit.items():
            b1_rows = {pid: row for pid, row in by_condition.get("B1", {}).items() if row.option is not None}
            cluster = unit[1]
            for pid, row in by_condition.get(condition, {}).items():
                if row.option is None or pid not in b1_rows or row.option == b1_rows[pid].option:
                    continue
                sums.add(cluster, f"{prefix}|mudancas")
                holders = [peer for peer in b1_rows if peer != pid and b1_rows[peer].option == row.option]
                if not holders:
                    sums.add(cluster, f"{prefix}|para_nenhum_par")
                    continue
                for peer in holders:
                    credit[row.model][b1_rows[peer].model] += 1 / len(holders)
                order = [peer for peer in row.peer_order if peer != pid]
                if not order or not set(holders) <= set(order):
                    sums.add(cluster, f"{prefix}|sem_ordem")
                    continue
                expected = len(holders) / len(order)
                sums.add(cluster, f"{prefix}|ordenadas")
                for which, peer in (("primeiro", order[0]), ("ultimo", order[-1])):
                    sums.add(cluster, f"{prefix}|{which}|obs", float(peer in holders))
                    sums.add(cluster, f"{prefix}|{which}|esp", expected)
                for rank, peer in enumerate(order, start=1):
                    by_rank_obs[rank] += float(peer in holders)
                    by_rank_exp[rank] += expected
        stats = {
            "excesso_primeiro": Statistic(_excess(prefix, "primeiro"), f"{prefix}|ordenadas"),
            "excesso_ultimo": Statistic(_excess(prefix, "ultimo"), f"{prefix}|ordenadas"),
            "fracao_para_posicao_de_par": Statistic(lambda t: None if not t.get(f"{prefix}|mudancas") else 1 - t.get(f"{prefix}|para_nenhum_par", 0.0) / t[f"{prefix}|mudancas"], f"{prefix}|mudancas"),
        }
        intervals = bootstrap.run(sums, stats)
        totals = sums.totals()
        return {
            "mudancas": int(totals.get(f"{prefix}|mudancas", 0)),
            "para_opcao_de_nenhum_par": int(totals.get(f"{prefix}|para_nenhum_par", 0)),
            "sem_ordem_gravada": int(totals.get(f"{prefix}|sem_ordem", 0)),
            "credito_destino_origem": {target: dict(sorted(sources.items())) for target, sources in sorted(credit.items())},
            "portador_por_posicao_na_lista": {str(rank): {"observado": by_rank_obs[rank], "esperado_sem_efeito": by_rank_exp[rank]} for rank in sorted(by_rank_obs)},
            "resultado": {name: interval.to_dict() for name, interval in intervals.items()},
        }
