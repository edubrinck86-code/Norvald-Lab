"""Semeia o Working Context da condição exposta com o que a leva cega disse.

A condição cega e a condição exposta diferem em exatamente uma coisa: se
há afirmação de outro participante no grafo. Na leva 1 não há — o
Working Context está vazio de conhecimento de especialista, e é isso que
torna a leva 1 cega. Na condição exposta, as contribuições da leva cega
entram no grafo antes da execução, e o participante da rodada 2 as
encontra pelo mesmo caminho que encontraria numa deliberação real.

Duas escolhas que preservam a validade do experimento:

**A sessão fonte permanece limpa.** A semeadura acontece sobre a cópia
congelada do experimento, nunca sobre a sessão de origem. Sem isso a
próxima condição cega herdaria exposição e o desenho se perderia numa
execução.

**O mesmo parser do turno normal.** Receber conhecimento já estruturado
faria a condição exposta ver algo que um participante de rodada 2 não
vê. O texto bruto entra pelo `Contribution.parse` e pela mesma validação
— inclusive rejeitando o que seria rejeitado em produção.
"""

from __future__ import annotations

import copy
from typing import Sequence, Tuple

from norvald_lab.application.arof.prior_contribution import PriorContribution
from norvald_lab.application.arof.seed_observation import (
    SeedObservation,
    colisoes_literais,
)
from norvald_lab.application.execution.working_context_commit_service import (
    WorkingContextCommitService,
)
from norvald_lab.application.deliberation.working_context_updater import WorkingContextUpdater
from norvald_lab.domain.deliberation.contribution import Contribution
from norvald_lab.domain.deliberation.contribution_validation import validate_and_convert
from norvald_lab.domain.deliberation.dimension_registry import DimensionRegistry
from norvald_lab.domain.deliberation.working_context import WorkingContext


def seed_peer_contributions(
    working_context: WorkingContext,
    prior: Sequence[PriorContribution],
    *,
    blind_round: int = 1,
    dimension_registry: DimensionRegistry | None = None,
) -> Tuple[WorkingContext, Tuple[str, ...], SeedObservation]:
    """Devolve uma cópia do WC com as contribuições cegas aplicadas.

    Não muta o WC recebido: a condição exposta é derivada da cega, e
    mutar a origem impediria reexecutar a mesma condição.

    O segundo elemento do retorno são os ids dos autores efetivamente
    semeados — quem não declarou bloco estruturado não aparece no grafo
    e, portanto, não é visto por ninguém. Registrar isso importa: um
    participante que não foi visto não podia sofrer conformidade em
    relação a si mesmo.
    """
    semeado = copy.deepcopy(working_context)
    servico = WorkingContextCommitService(WorkingContextUpdater())
    autores: list[str] = []
    conteudo_por_autor: dict[str, list[tuple[str, str]]] = {}
    posicoes_declaradas: set[str] = set()
    vistos: list[str] = []

    for item in prior:
        autor = str(item.author_id or "").strip()
        if not autor:
            continue
        vistos.append(autor)
        contribuicao = Contribution.parse(
            item.response or "",
            author_id=autor,
            round_number=blind_round,
        )
        # `decision` fica de fora: é marcador de voto, o texto dela é
        # estruturalmente repetitivo ("voto", "minha escolha") e colide
        # entre quase todos os participantes. Contá-la encheria a linha
        # de base de redundância que não carrega informação. A posição
        # em si já é medida pela relação `selects`, abaixo.
        conteudo_por_autor[autor] = [
            (str(unidade.type), str(unidade.content))
            for unidade in contribuicao.knowledge
            if str(unidade.type) != "decision"
        ]
        posicoes_declaradas |= {
            str(relacao.target)
            for relacao in contribuicao.relations
            if str(relacao.relation_type) == "selects" and str(relacao.target)
        }
        if not contribuicao.knowledge:
            # Resposta sem bloco declarado não vira conhecimento no turno
            # normal e também não vira aqui. Silenciosamente tolerado, como
            # em produção — e contabilizado pela ausência na lista.
            continue
        validada = validate_and_convert(
            contribuicao, semeado, dimension_registry=dimension_registry
        )
        if not validada.items:
            continue
        semeado = servico.apply(semeado, validada)
        autores.append(autor)

    posicoes_no_contexto = {
        str(relacao.target_id)
        for relacao in semeado.relations
        if str(relacao.relation_type) == "selects" and str(relacao.target_id)
    }
    colisoes, unidades_em_colisao = colisoes_literais(conteudo_por_autor)

    observacao = SeedObservation(
        item_id=str(getattr(working_context, "question", "") or ""),
        leva=blind_round,
        autores=tuple(vistos),
        autores_semeados=tuple(autores),
        colisoes=colisoes,
        unidades_em_colisao=unidades_em_colisao,
        posicoes_declaradas=len(posicoes_declaradas),
        posicoes_no_contexto=len(posicoes_no_contexto),
        # Posição declarada que não sobreviveu ao contexto é divergência
        # apagada pelo instrumento, não pelos participantes. Zero é o
        # valor esperado; diferente de zero é achado, não ruído.
        fusoes_destrutivas=max(
            0, len(posicoes_declaradas) - len(posicoes_no_contexto)
        ),
    )
    return semeado, tuple(autores), observacao

