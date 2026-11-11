"""O par agente-pergunta de Hao et al. (§3.1), montado a partir da nossa tabela.

Correspondência (protocolo, §3): a_0 → B1, a_sr → B3 (autorreflexão),
a_so → EP (só posição), a_r → E (raciocínio completo). B2 não tem
equivalente no paper e não entra aqui.

Só entra o par com posição válida nas quatro condições: a partição da
Tabela 1 precisa das quatro. "Resposta de algum par" = a B1 de outro
participante da mesma pergunta (os pares de Hao são os outros 4 agentes,
com as respostas reais do Round 0).

Subconjuntos (§2 do protocolo): "todas" e "discordancia" (B1 não unânime
entre as posições válidas, o filtro "inter-agent disagreement" deles).
"""

from __future__ import annotations

from dataclasses import dataclass

from norvald_lab.measures.observation_table import ObservationTable

SUBSETS = ("todas", "discordancia")


@dataclass(frozen=True)
class HaoUnit:
    cluster: str  # question_id
    participant_id: str
    model: str
    a0: str
    asr: str
    aso: str
    ar: str
    peer_answers: tuple[str, ...]  # B1 dos outros participantes da pergunta
    answer: str | None  # gabarito; None em contestável
    disagreement: bool
    question_unit: tuple[str, str, str] = ("", "", "")  # (run, pergunta, repetição)

    @property
    def support(self) -> int:
        """s de Hao (Ap. D): quantos pares deram em B1 a mesma resposta do alvo."""
        return sum(peer == self.a0 for peer in self.peer_answers)

    @property
    def sr_stable(self) -> bool:
        return self.asr == self.a0

    def is_correct(self, option: str) -> bool:
        return option == self.answer


def hao_units(table: ObservationTable) -> list[HaoUnit]:
    units = []
    for unit in table.by_question_unit:
        b1 = table.options(unit, "B1")
        b3, ep, e = table.options(unit, "B3"), table.options(unit, "EP"), table.options(unit, "E")
        disagreement = len(set(b1.values())) > 1
        models = {pid: row.model for pid, row in table.by_question_unit[unit].get("B1", {}).items()}
        for pid, a0 in b1.items():
            if pid not in b3 or pid not in ep or pid not in e:
                continue
            peers = tuple(option for other, option in b1.items() if other != pid)
            units.append(HaoUnit(unit[1], pid, models.get(pid, ""), a0, b3[pid], ep[pid], e[pid], peers, table.answer(unit[1]), disagreement, unit))
    return units


def subset(units: list[HaoUnit], name: str) -> list[HaoUnit]:
    if name == "todas":
        return list(units)
    if name == "discordancia":
        return [u for u in units if u.disagreement]
    raise ValueError(f"Subconjunto desconhecido: {name}")
