"""O que o validador aceitou de uma execução, lido do próprio RAW.

Acréscimo do Lab (docs/MIGRACAO.md, 2026-10-04). Não existe no Studio.

`outcome_extract` lê o bloco declarado sem validar. O contexto exposto
de B3 e E é montado com o que o validador aceita. As duas leituras
divergem: uma relação recusada conta na tabela e não chega aos pares.
Este módulo produz a segunda leitura, para ficar ao lado da primeira na
mesma linha. Nenhuma das duas substitui a outra, e nenhuma regra de
validação é alterada aqui.

A validação precisa do Working Context que a execução recebeu. Ele está
no RAW, em `request.context.working_context`. Quando não está — replay
de dado legado, registro sem contexto — as colunas saem vazias. Vazio é
ausência de leitura, não zero.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Collection, Mapping

from norvald_lab.contribution_check import check_contribution
from norvald_lab.domain.deliberation.contribution import Contribution
from norvald_lab.domain.deliberation.contribution_validation import validate_and_convert
from norvald_lab.domain.deliberation.working_context import WorkingContext

CODIGO_EXECUCAO_FALHOU = "execution_failed"


@dataclass(frozen=True)
class OutcomeValidation:
    """Leitura do validador para uma execução. Todos os campos são texto.

    `validation_code` é o código do diagnóstico já usado na bancada
    (`usable`, `partial`, `missing_block`, `unclosed_block`,
    `invalid_json`, `invalid_schema`, `empty_knowledge`,
    `rejected_knowledge`, `empty_response`, `execution_failed`).

    As contagens são contagens: partes declaradas no bloco e partes
    aceitas. `option_accepted` é o alvo da primeira relação `selects`
    aceita. `grounding_targets_accepted` são os alvos das relações de
    fundamento aceitas. `rejected_reasons` lista o motivo de cada parte
    recusada, uma entrada por parte, separadas por " | ".

    Alvos e opções aparecem como foram declarados: `local_id` quando a
    unidade é da própria contribuição, id do Working Context quando já
    existia.
    """

    validation_code: str = ""
    items_declared: str = ""
    items_accepted: str = ""
    relations_declared: str = ""
    relations_accepted: str = ""
    option_accepted: str = ""
    grounding_targets_accepted: str = ""
    rejected_reasons: str = ""


def _contexto_da_execucao(payload: Mapping[str, Any]) -> WorkingContext | None:
    """O Working Context que a execução recebeu, ou None se o RAW não o traz."""
    pedido = payload.get("request")
    contexto = pedido.get("context") if isinstance(pedido, Mapping) else None
    texto = contexto.get("working_context") if isinstance(contexto, Mapping) else None
    if not isinstance(texto, str) or not texto.strip():
        return None
    try:
        dados = json.loads(texto)
        if not isinstance(dados, dict):
            return None
        return WorkingContext.from_dict(dados)
    except (ValueError, TypeError, KeyError):
        return None


def validation_from_payload(
    payload: Mapping[str, Any],
    *,
    response: str,
    grounding_relations: Collection[str],
) -> OutcomeValidation:
    """Valida a resposta contra o contexto gravado no mesmo registro RAW."""
    contexto = _contexto_da_execucao(payload)
    if contexto is None:
        return OutcomeValidation()

    autor = str(payload.get("participant_id") or "")
    diagnostico = check_contribution(response, autor, contexto)
    contribuicao = Contribution.parse(
        response,
        author_id=autor,
        round_number=int(payload.get("round_number") or 1),
    )
    validada = validate_and_convert(contribuicao, contexto)

    # O validador troca cada `local_id` por um UUID sorteado. Para a
    # tabela, o alvo volta a ser o `local_id` declarado.
    declarado_por_id = {item_id: local_id for local_id, item_id in validada.local_ids.items()}
    tipo_por_id = {item.id: item.type for item in validada.items}

    opcao = ""
    for relacao in validada.relations:
        if relacao["relation_type"] != "selects":
            continue
        if tipo_por_id.get(relacao["source_id"]) != "decision":
            continue
        opcao = declarado_por_id.get(relacao["target_id"], relacao["target_id"])
        break

    alvos = sorted(
        {
            declarado_por_id.get(relacao["target_id"], relacao["target_id"])
            for relacao in validada.relations
            if relacao["relation_type"] in grounding_relations
        }
    )

    return OutcomeValidation(
        validation_code=CODIGO_EXECUCAO_FALHOU if payload.get("error") else str(diagnostico["code"]),
        items_declared=str(diagnostico["declared_items"]),
        items_accepted=str(diagnostico["accepted_items"]),
        relations_declared=str(diagnostico["declared_relations"]),
        relations_accepted=str(diagnostico["accepted_relations"]),
        option_accepted=opcao,
        grounding_targets_accepted=";".join(alvos),
        rejected_reasons=" | ".join(parte.reason for parte in validada.rejected),
    )
