"""Diagnóstico de leitura pelo parser e validador do protocolo existente."""
from __future__ import annotations

import json
from dataclasses import asdict

from norvald_lab.domain.deliberation.contribution import Contribution, _CONTRIBUTION_RE, _strip_code_fence
from norvald_lab.domain.deliberation.contribution_validation import validate_and_convert
from norvald_lab.domain.deliberation.working_context import WorkingContext


def check_contribution(content, author_id, context):
    contribution = Contribution.parse(content, author_id=author_id, round_number=1)
    validated = validate_and_convert(contribution, context)
    # Parte que o parser não leu também foi declarada: conta em "declared".
    malformed_items = sum(part.kind == "knowledge" for part in contribution.malformed)
    malformed_relations = sum(part.kind == "relation" for part in contribution.malformed)
    result = {"usable": bool(validated.items), "fully_valid": bool(validated.items) and not validated.rejected,
              "declared_items": len(contribution.knowledge) + malformed_items, "accepted_items": len(validated.items),
              "declared_relations": len(contribution.relations) + malformed_relations, "accepted_relations": len(validated.relations),
              "rejected": [asdict(p) for p in validated.rejected]}
    if not content.strip():
        return result | {"code": "empty_response", "message": "Nenhum conteúdo de resposta foi disponibilizado."}
    if validated.items:
        if validated.rejected:
            return result | {"code": "partial", "message":
                f"Contribuição aceita parcialmente: {len(validated.items)} unidades e {len(validated.relations)} relações aceitas; {len(validated.rejected)} partes recusadas. Confira as recusas antes de pedir um ajuste."}
        return result | {"code": "usable", "message": "Contribuição estruturada disponível para exposição."}
    match = _CONTRIBUTION_RE.search(content)
    if match is None:
        opened = "<<CONTRIBUTION>>" in content
        return result | {"code": "unclosed_block" if opened else "missing_block", "message":
            "O bloco CONTRIBUTION começou, mas não tem o delimitador de fechamento. Pode haver corte da resposta ou fechamento em outro formato." if opened else
            "A resposta não contém o bloco CONTRIBUTION com os delimitadores exigidos."}
    try:
        payload = json.loads(_strip_code_fence(match.group("body")))
    except (ValueError, TypeError):
        return result | {"code": "invalid_json", "message": "O bloco CONTRIBUTION contém JSON inválido."}
    if not isinstance(payload, dict) or not isinstance(payload.get("knowledge", []), list) or not isinstance(payload.get("relations", []), list):
        return result | {"code": "invalid_schema", "message": "O JSON não segue a estrutura de knowledge e relations exigida pelo protocolo."}
    if not payload.get("knowledge"):
        return result | {"code": "empty_knowledge", "message": "O bloco CONTRIBUTION não declarou nenhuma unidade de conhecimento."}
    if not contribution.knowledge:
        return result | {"code": "invalid_schema", "message": "Há campos ausentes ou inválidos nas unidades ou relações do bloco CONTRIBUTION."}
    reasons = "; ".join(dict.fromkeys(p.reason for p in validated.rejected if p.kind == "knowledge"))
    return result | {"code": "rejected_knowledge", "message": "Nenhuma unidade foi aceita pelo validador: " + reasons}


def check_records(records, requests):
    """Cada resposta é conferida contra seu contexto preparado, sem gravações."""
    result = []
    by_execution = {r["context"]["metadata"]["execution_id"]: r for r in requests}
    for record in records:
        request = by_execution.get(record["logical_execution_id"])
        if request is None:
            continue
        content = (record.get("result") or {}).get("content") or ""
        context = WorkingContext.from_dict(json.loads(request["context"]["working_context"]))
        check = check_contribution(content, record["participant_id"], context)
        if record.get("error"):
            check = check | {"usable": False, "fully_valid": False, "code": "execution_failed", "message": "A execução falhou; não há resposta válida para exposição."}
        result.append(check | {"observation_id": record["observation_id"], "participant_id": record["participant_id"],
                              "participant_name": record["participant_name"], "run_id": record["run_id"],
                              "model": record["requested_model"]})
    return result
