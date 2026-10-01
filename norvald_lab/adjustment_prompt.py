"""Explain observed formatting failures without changing the original response."""
from __future__ import annotations

import json

from norvald_lab.contribution_check import check_contribution
from norvald_lab.domain.deliberation.contribution import (
    DECLARABLE_KNOWLEDGE_TYPES, _CONTRIBUTION_RE, _strip_code_fence,
)
from norvald_lab.domain.deliberation.working_context import WorkingContext


def adjustment_diagnostic(record, request):
    content = (record.get("result") or {}).get("content") or ""
    context = WorkingContext.from_dict(json.loads(request["context"]["working_context"]))
    check = check_contribution(content, record["participant_id"], context)
    details = []
    match = _CONTRIBUTION_RE.search(content)
    if match:
        try:
            payload = json.loads(_strip_code_fence(match.group("body")))
        except json.JSONDecodeError as exc:
            details.append(f"JSON do bloco: {exc.msg}; linha {exc.lineno}, coluna {exc.colno}.")
        else:
            if isinstance(payload, dict) and check["code"] == "invalid_schema":
                for name, required in (("knowledge", ("local_id", "type")), ("relations", ("relation_type", "source", "target"))):
                    parts = payload.get(name, [])
                    if not isinstance(parts, list):
                        details.append(f"{name} deve ser uma lista JSON.")
                        continue
                    for index, part in enumerate(parts):
                        if not isinstance(part, dict):
                            details.append(f"{name}[{index}] deve ser um objeto JSON.")
                            continue
                        for field in required:
                            if field not in part:
                                details.append(f"{name}[{index}].{field}: campo obrigatório ausente.")
                        if name == "knowledge":
                            try:
                                dict(part.get("metadata", {}))
                            except (ValueError, TypeError):
                                details.append(f"knowledge[{index}].metadata não pode ser convertido em objeto JSON.")
    error = record.get("error")
    if error:
        check.update(usable=False, code="execution_failed", message="A execução anterior falhou; não há uma resposta completa disponível para corrigir.")
    return check | {"details": details, "execution_error": error}


def diagnostic_instructions(diagnostic, *, previous_limit, new_limit):
    lines = ["DIAGNÓSTICO DA RESPOSTA QUE SERÁ AJUSTADA:",
             f"Código: {diagnostic['code']}. {diagnostic['message']}"]
    lines.extend(diagnostic["details"])
    for rejected in diagnostic["rejected"]:
        lines.append(f"Parte recusada: {rejected['kind']} / {rejected['identifier'] or 'sem identificador'}: {rejected['reason']}.")
    if diagnostic["execution_error"]:
        lines.append("Erro operacional registrado (não é uma falha de argumento): " + json.dumps(diagnostic["execution_error"], ensure_ascii=False))
        lines.append("Produza uma resposta completa a partir do objetivo e material originais. Uma falha de conexão, credencial ou limite do provedor pode exigir ajuste da configuração pelo usuário.")
    if diagnostic["code"] == "unclosed_block":
        lines.append("O delimitador <<END_CONTRIBUTION>> não foi encontrado. Regere o bloco inteiro com JSON válido e feche com esse delimitador; não devolva somente um fragmento. O diagnóstico não comprova que o limite de tokens causou o corte.")
    elif diagnostic["code"] == "missing_block":
        lines.append("Declare explicitamente suas unidades no bloco <<CONTRIBUTION>> ... <<END_CONTRIBUTION>>; prosa sozinha não é extraída como conhecimento.")
    elif diagnostic["code"] == "invalid_json":
        lines.append("Corrija a sintaxe JSON no local indicado e reenvie o bloco completo.")
    elif diagnostic["code"] in {"empty_knowledge", "rejected_knowledge", "invalid_schema"}:
        lines.append("Corrija os campos ou partes indicados. knowledge deve conter ao menos uma unidade declarada por você e sustentada no material; não invente conteúdo apenas para passar pela validação.")
    lines.append("Tipos declaráveis em knowledge.type: " + ", ".join(DECLARABLE_KNOWLEDGE_TYPES) + ".")
    lines.append("Cada unidade usa local_id único, type permitido e content não vazio. relations é uma lista, podendo ser vazia; suas relações devem usar referências existentes. Este diagnóstico não avalia a qualidade ou a verdade da resposta.")
    lines.append(f"Limite de saída da tentativa anterior: {previous_limit if previous_limit is not None else 'padrão do provedor'}. Limite solicitado agora: {new_limit if new_limit is not None else 'padrão do provedor'}.")
    if previous_limit == new_limit:
        lines.append("O limite de saída não foi aumentado neste pedido.")
    return "\n".join(lines)
