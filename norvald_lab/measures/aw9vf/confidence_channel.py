"""Canal da confiança (344-71; exploratório, 344-77): Wilcoxon pareado na mudança de confiança, E contra B3.

Mudança = posto da confiança declarada em E − posto em B3 (baixa 1, média 2,
alta 3), por participante e pergunta, só onde a confiança foi declarada nas
duas condições e há posição válida nas duas (344-81: pareado, ausência nunca
vira zero). Condicionado a se a maioria dos pares concorda com a posição do
participante:

- pares = os outros participantes elegíveis da pergunta (os que E mostrou);
- posição de cada um = a de B1 (é o que E expõe), e a do participante = a
  própria B1, antes da exposição;
- maioria = opção com MAIS da metade dos pares com posição válida;
  concorda se é a opção do participante, discorda se é outra; sem opção
  majoritária estrita, o par fica no grupo `sem_maioria`.

A previsão do registro é subida da confiança onde concorda e queda onde
discorda. Os pares participante-pergunta de uma mesma pergunta não são
independentes: o p-valor é exploratório e sem correção.
"""

from __future__ import annotations

from collections import Counter

from norvald_lab.measures.aw9vf.confidence_scale import ConfidenceScale
from norvald_lab.measures.aw9vf.exposure_eligibility import eligible_b1
from norvald_lab.measures.aw9vf.wilcoxon_signed_rank import WilcoxonSignedRank
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.statistic import Statistic

GROUPS = ("maioria_concorda", "maioria_discorda", "sem_maioria", "todos")


def peer_majority_relation(own: str, peers: list[str]) -> str:
    """Relação da maioria estrita dos pares com a opção do participante."""
    if not peers:
        return "sem_maioria"
    option, count = Counter(peers).most_common(1)[0]
    if count * 2 <= len(peers):
        return "sem_maioria"
    return "maioria_concorda" if option == own else "maioria_discorda"


class ConfidenceChannel:
    def __init__(self, bootstrap: ClusteredBootstrap):
        self.bootstrap = bootstrap

    def compute(self, table: ObservationTable) -> dict:
        scale = ConfidenceScale()
        changes: dict[str, list[tuple[str, float]]] = {group: [] for group in GROUPS}
        undeclared = 0
        for unit, by_condition in table.by_question_unit.items():
            eligible = eligible_b1(table, unit)
            for pid, own in eligible.items():
                b3, e = by_condition.get("B3", {}).get(pid), by_condition.get("E", {}).get(pid)
                if b3 is None or e is None or b3.option is None or e.option is None:
                    continue
                before, after = scale.rank(b3.confidence), scale.rank(e.confidence)
                if before is None or after is None:
                    undeclared += 1
                    continue
                group = peer_majority_relation(own.option, [row.option for other, row in eligible.items() if other != pid])
                for label in (group, "todos"):
                    changes[label].append((unit[1], float(after - before)))
        sums, stats = ClusterSums(), {}
        for unit in table.by_question_unit:
            sums.touch(unit[1])
        for group, values in changes.items():
            for cluster, delta in values:
                sums.add(cluster, f"conf|{group}|n")
                sums.add(cluster, f"conf|{group}|s", delta)
            stats[group] = Statistic.ratio(f"conf|{group}|s", f"conf|{group}|n")
        intervals = self.bootstrap.run(sums, stats)
        out = {}
        for group, values in changes.items():
            result = WilcoxonSignedRank().test([delta for _, delta in values])
            out[group] = {
                "pares": result.n, "nao_nulos": result.n_nonzero, "w_mais": result.w_plus, "w_menos": result.w_minus,
                "metodo_p": result.method, "p_bruto_sem_correcao": result.p,
                "efeito_bisserial_por_postos": result.rank_biserial, "mediana_da_mudanca": result.median_difference,
                "mudanca_media_E_menos_B3": intervals[group].to_dict(),
            }
        return {
            "exploratorio": True, "correcao_multipla": "nenhuma (344-77)",
            "previsao_do_registro": "confiança sobe onde a maioria dos pares concorda e cai onde discorda",
            "pares_sem_confianca_nas_duas_condicoes": undeclared,
            "grupos": out,
        }
