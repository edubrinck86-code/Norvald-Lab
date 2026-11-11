"""Uma linha da tabela de observações: um participante, numa pergunta, numa condição."""

from __future__ import annotations

from dataclasses import dataclass

from norvald_lab.measures.ground import Ground


@dataclass(frozen=True)
class Observation:
    run: str  # rodada do herd (run_id do lote), não a repetição
    question_id: str
    kind: str  # contestavel, gabarito, reserva ou desconhecido
    category: str  # categoria do MMLU-Pro; vazio no banco próprio
    condition: str  # B1, B2, B3, EP ou E
    repetition: str  # r0001...; o herd usa uma repetição
    participant_id: str
    model: str
    # Opção aceita pelo validador e resolvida (regra 3). None quando a
    # execução não deu posição utilizável: ausência, nunca opção inventada.
    option: str | None
    indirect: bool  # regra 3: a decisão apontou para uma decisão, resolvida um passo
    indirect_source: str  # autor da decisão apontada (pode ser o próprio participante)
    correct: bool | None  # None quando não há gabarito ou não há posição
    confidence: str
    justification: str
    peer_order: tuple[str, ...]
    attempts: int
    attempt1_failed: bool
    cost: float  # soma de todas as tentativas: dinheiro gasto conta mesmo se falhou
    status: str  # leitura do extrator (ok, no_decision, failed) na última tentativa
    validation_code: str
    agent_key: str = ""  # preenchido pelo carregador; ver `agent`
    # Estrutura declarada, para o registro aw9vf (ver measures/aw9vf).
    # `structured`: a contribuição declarou ao menos uma unidade aceita pelo
    # validador; sem isso o participante não entra no Working Context e
    # ninguém o viu (344-79, item 2). `grounds`: os fundamentos declarados.
    # `claims`: (tipo, conteúdo) de cada unidade declarada, só para contar
    # colisões literais; o texto nunca vai para o relatório (344-83, item 5).
    structured: bool = True
    grounds: tuple[Ground, ...] = ()
    claims: tuple[tuple[str, str], ...] = ()

    @property
    def unit(self) -> tuple[str, str, str, str]:
        """O par agente-pergunta (Hao et al.): a unidade das medidas pareadas."""
        return (self.run, self.question_id, self.repetition, self.participant_id)

    @property
    def question_unit(self) -> tuple[str, str, str]:
        return (self.run, self.question_id, self.repetition)

    @property
    def agent(self) -> str:
        """Identidade do participante entre rodadas.

        O carregador usa o modelo quando ele é único na rodada: o id não
        serve sozinho, porque muda com o idioma ("analista-1" no piloto-3,
        "analyst-1" no piloto-mmlu-1) e com a ordem do painel; juntar as duas
        rodadas pelo id contava cada modelo duas vezes (achado de 11/11/2026).
        Quando o modelo se repete na rodada (no simulador todos são demo-v1),
        vale id + modelo.
        """
        return self.agent_key or f"{self.participant_id}·{self.model}"
