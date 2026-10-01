"""O que este turno é, e o que ele permite.

A fase da rodada estava espalhada: `round_execution` recalculava
`current_round <= 1` para decidir ferramentas, `round_prompt` recalculava
para escolher o texto, `tool_loop` aplicava limites fixos sem saber de
fase nenhuma. Três lugares decidindo pedaços da mesma coisa, sem se
falarem.

O efeito prático apareceu nas correções: como a política só era editável
no prompt, toda correção virava reescrita de frase. "Não investigue"
produziu 32 chamadas na rodada 1 — pedir por escrito o que a estrutura
permite não funciona, e a estrutura permitia.

Aqui a fase vira uma decisão só, e as demais viram consequência dela:
quais ferramentas existem e o que o prompt diz. Uma fase nova se declara
num lugar; antes exigia lembrar de três.

A prioridade do recorte ficou de fora de propósito. O `ContextAssembler`
já põe o que está em disputa à frente, sempre, e na primeira rodada não
há disputa — um campo aqui seria um botão que não liga nada.

**Não é um motor.** Não executa, não chama provider, não muta o Working
Context. É a resposta a "o que é este turno", consultada por quem
executa — e é por isso que cabe no domínio, não numa camada nova.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


#: O protocolo nativo usa conclusão natural. Limites numéricos pertencem
#: a condições experimentais/configurações explícitas, não à fase.
NATIVE_MAX_TOOL_CALLS: Optional[int] = None

#: Orçamento do resultado das ferramentas no contexto.
#:
#: Cada iteração reenvia o acumulado, então o custo cresce com o produto
#: de chamadas por rodadas, não com a soma.
TOOL_CONTEXT_CHARS = 26_000


class Phase(Enum):
    """As fases de uma deliberação.

    A separação é temporal e não de conteúdo: o que muda entre elas é o
    que já existe para trabalhar em cima e o alcance das ferramentas.
    Em N+0 as Evidence vinculadas já foram projetadas como âncoras do WC
    e seu conteúdo selecionado é passado diretamente; Library/Repository/WC
    podem ser consultados. Em N+1+ existem também posições declaradas e o
    perfil se amplia para MCP/Web e demais capacidades configuradas.
    """

    POSICIONAMENTO = "posicionamento"
    DELIBERACAO = "deliberacao"


@dataclass(frozen=True)
class TurnPolicy:
    """O que o turno permite, derivado da fase.

    Cada campo aqui era uma decisão independente tomada em outro
    arquivo. Reuni-las não é centralizar por gosto: é que elas precisam
    concordar entre si, e concordavam por coincidência.
    """

    phase: Phase
    round_number: int

    #: Ferramentas chegam ao provider.
    #:
    #: O protocolo nativo possui ferramentas em todas as fases; o que muda
    #: é o perfil. N+0 recebe o conjunto ancorado em Library/Repository/WC.
    #: N+1+ recebe também as capacidades ampliadas.
    tools_enabled: bool

    #: Evidence anexada é passada diretamente no prompt apenas em N+0.
    #: Depois permanece como âncora estável do Working Context.
    include_attached_evidence: bool

    #: MCP/Web e demais capacidades ampliadas entram somente em N+1+.
    extended_tools_enabled: bool

    #: O prompt inclui as regras de uso de ferramenta.
    #:
    #: Descrever um recurso ausente gasta contexto e sugere um caminho
    #: que o turno não tem.
    include_tool_rules: bool

    #: O prompt pede resposta à rodada anterior.
    include_previous_round: bool

    #: Limite explícito de chamadas. None = conclusão natural.
    #:
    #: O Studio nativo não decide quantas consultas um especialista
    #: deveria precisar. Um número é intervenção experimental/configuração.
    max_tool_calls: Optional[int]

    #: Quanto do resultado das ferramentas volta ao modelo.
    #:
    #: O orçamento existe nas duas fases porque ambas possuem ferramentas;
    #: o perfil de N+0 é apenas mais restrito.
    tool_context_chars: int

    #: Uma parte rejeitada na validação interrompe o commit do resto.
    #:
    #: Não interrompe: uma relação com par inválido não deve descartar
    #: as unidades válidas da mesma contribuição. O que faltava era o
    #: rejeitado *chegar de volta* ao especialista — decidido em
    #: `report_rejected`, não aqui.
    reject_blocks_commit: bool = False

    #: O rejeitado volta ao especialista na rodada seguinte.
    #:
    #: Sempre. Descartar em silêncio faz o especialista redeclarar a
    #: mesma relação inválida indefinidamente: é uma correção que nunca
    #: acontece. O campo existe para que a decisão tenha dono explícito,
    #: e não para ser desligada.
    report_rejected: bool = True

    @property
    def is_first(self) -> bool:
        return self.phase is Phase.POSICIONAMENTO


def policy_for(round_number: int) -> TurnPolicy:
    """A política do turno.

    A regra é a rodada porque é o que separa as fases hoje. Se um dia a
    fase depender de outra coisa — o moderador declarar consolidação, o
    documento atingir cobertura —, muda aqui e as consequências
    acompanham, em vez de exigir três edições coordenadas.
    """
    primeira = round_number <= 1
    fase = Phase.POSICIONAMENTO if primeira else Phase.DELIBERACAO
    return TurnPolicy(
        phase=fase,
        round_number=round_number,
        tools_enabled=True,
        include_attached_evidence=primeira,
        extended_tools_enabled=not primeira,
        include_tool_rules=True,
        include_previous_round=not primeira,
        max_tool_calls=NATIVE_MAX_TOOL_CALLS,
        tool_context_chars=TOOL_CONTEXT_CHARS,
    )


#: O que o especialista lê sobre a própria fase.
#:
#: Fica ao lado da política e não no renderizador: o texto descreve o que
#: a política permite, e separá-los é como os dois divergiram antes —
#: o prompt pedia para não investigar enquanto a estrutura oferecia as
#: ferramentas.
_TEXTO_DA_FASE = {
    Phase.POSICIONAMENTO: (
        "Esta é a primeira rodada (N+0): ninguém se posicionou ainda. Sua "
        "base são a Evidence vinculada, o objetivo e o Working Context "
        "inicial, que já contém as âncoras estáveis das evidências. "
        "As ferramentas ancoradas de Library/Repository/WC estão disponíveis "
        "se forem necessárias; MCP e Web só entram a partir de N+1."
    ),
    Phase.DELIBERACAO: (
        "Esta é uma rodada N+1 ou posterior. Há posições declaradas nas "
        "rodadas anteriores. Primeiro use o Working Context e suas âncoras. "
        "Library/Repository continuam disponíveis e o perfil ampliado passa "
        "a incluir MCP/Web quando configurados. A Evidence anexada não é "
        "reenviada como bloco integral: sua proveniência permanece no WC."
    ),
}


def phase_text(policy: TurnPolicy) -> str:
    return _TEXTO_DA_FASE[policy.phase]

