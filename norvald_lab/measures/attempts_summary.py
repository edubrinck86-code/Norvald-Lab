"""Falhas da tentativa 1 por modelo e custo total.

Falha da tentativa 1 = a primeira tentativa não deu posição utilizável
(erro do provider, resposta vazia, sem decisão, seleção recusada). Fica
visível mesmo quando a tentativa 2 salvou a linha, porque é sinal do
modelo, não do estudo. "sem_posicao_final" é o que sobrou sem posição
depois de todas as tentativas.

Custo: soma de `result.metadata.raw_usage.cost` de todas as tentativas
(US$, como o OpenRouter devolve). Tentativa sem esse campo conta zero, e o
número de linhas sem custo informado sai ao lado, para ninguém ler zero
como "de graça".
"""

from __future__ import annotations

from collections import defaultdict

from norvald_lab.measures.observation_table import ObservationTable


class AttemptsSummary:
    def compute(self, table: ObservationTable) -> dict:
        by_model: dict[str, dict] = defaultdict(lambda: {"observacoes": 0, "falhas_tentativa_1": 0, "com_nova_tentativa": 0, "sem_posicao_final": 0, "custo": 0.0})
        cost_by_condition: dict[str, float] = defaultdict(float)
        for row in table.rows:
            entry = by_model[row.model]
            entry["observacoes"] += 1
            entry["falhas_tentativa_1"] += int(row.attempt1_failed)
            entry["com_nova_tentativa"] += int(row.attempts > 1)
            entry["sem_posicao_final"] += int(row.option is None)
            entry["custo"] += row.cost
            cost_by_condition[row.condition] += row.cost
        for entry in by_model.values():
            entry["taxa_falha_tentativa_1"] = entry["falhas_tentativa_1"] / entry["observacoes"] if entry["observacoes"] else None
        return {
            "por_modelo": dict(sorted(by_model.items())),
            "custo_total_usd": sum(row.cost for row in table.rows),
            "custo_por_condicao_usd": dict(sorted(cost_by_condition.items())),
            "linhas_sem_custo_informado": sum(row.cost == 0 for row in table.rows),
        }
