"""Conservative, non-executing recovery plans and adjustment revalidation.

These are decisions about observations, *not* changes to their scientific
status. A valid follow-up cannot rewrite an invalid original observation.
"""
from __future__ import annotations

from pathlib import Path

from norvald_lab.storage import digest

SCHEMA_VERSION = "norvald.lab.criterion_recovery.v1"

FORMAT_ERRORS = frozenset({
    "missing_block", "unclosed_block", "invalid_json", "invalid_schema",
    "empty_knowledge", "rejected_knowledge", "partial", "empty_response",
})


def _attempts(root: Path, adjustments, incident):
    """Summaries only; never copy model answers or unsafe unsealed checks."""
    observation_id = incident.get("observation_id")
    if not observation_id:
        return []
    experiment_id = incident["experiment_id"]
    records = adjustments.list(experiment_id)
    original_seal = root / "experiments" / experiment_id / "integrity.json"
    original_hash = digest(original_seal) if original_seal.is_file() else None
    selected = []
    for row in records:
        if row.get("observation_id") != observation_id:
            continue
        path = adjustments.directory(experiment_id) / row["id"]
        sealed = (path / "integrity.json").exists() and row.get("status") != "altered"
        linked = original_hash is not None and row.get("source_integrity_sha256") == original_hash
        check = row.get("check") if sealed and linked and row.get("status") == "complete" else None
        criterion = incident["criterion_id"]
        flag = "fully_valid" if criterion.endswith(".fully_valid") else "usable"
        valid = (check.get(flag) is True) if isinstance(check, dict) else False
        selected.append({
            "adjustment_id": row["id"],
            "parent_id": row.get("parent_id"),
            "status": row.get("status"),
            "source_link_verified": linked,
            "integrity_verified": sealed,
            "criterion_status": "met_in_adjustment" if valid else
                                "not_met_in_adjustment" if check and check.get(flag) is False else
                                "not_evaluable",
            "validator_code": check.get("code") if check else None,
            "independent_sample": False,
        })
    return selected


def recovery_plan(incident, evaluation, adjustments, root):
    """Explain safe next steps. Never calls providers or starts adjustments."""
    checks = evaluation.get("evaluations") or []
    integrity = next((c for c in checks if c["criterion_id"] == "lab.dataset.integrity"), {})
    ready = integrity.get("status") == "met"
    check = next((c for c in checks
                  if c["criterion_id"] == incident["criterion_id"]
                  and c["criterion_version"] == incident["criterion_version"]
                  and (c.get("evidence") or {}).get("observation_id", "") ==
                      incident.get("observation_id", "")
                  and (c.get("evidence") or {}).get("participant_id", "") ==
                      incident.get("participant_id", "")
                  and (c.get("evidence") or {}).get("run_id", "") ==
                      incident.get("run_id", "")), None)
    current = check.get("status") if check else "not_evaluable"
    plan = {
        "schema_version": SCHEMA_VERSION,
        "incident_id": incident["id"],
        "original_criterion_status": incident["status"],
        "current_evaluation_status": current,
        "action": "review_manually",
        "automatic": False,
        "requires_approval": True,
        "allowed": False,
        "reason": "O Lab preserva a falha original; não existe correção automática de evidência.",
        "proposed_payload": None,
        "revalidations": [],
        "original_still_unmet": current == "not_met",
    }
    if not ready:
        plan.update(action="investigate_integrity", reason=(
            "Integridade da coleta não confirmada; nenhum ajuste pode ser sugerido como válido."))
        return plan
    if incident["criterion_id"] == "lab.dataset.integrity":
        plan.update(action="investigate_integrity", reason=(
            "Uma falha de integridade exige investigação. Não reparar ou recalcular o RAW."))
        return plan

    try:
        attempts = _attempts(Path(root), adjustments, incident)
    except (OSError, ValueError, KeyError, TypeError):
        attempts = []
        plan["revalidation_error"] = "Histórico de ajustes indisponível ou inconsistente."
    plan["revalidations"] = attempts

    if incident["criterion_id"] in {"arof.contribution.usable",
                                    "arof.contribution.fully_valid"}:
        spec = next((c for c in checks if c["criterion_id"] == "lab.experiment.complete"), {})
        # Get mode from the persisted, verified snapshot's Spec at the caller.
        if (incident.get("validator_code") in FORMAT_ERRORS
                and spec.get("status") == "met" and incident.get("observation_id")):
            plan.update(action="preview_adjustment",
                        allowed=True,
                        reason=("Um ajuste assistido pode ser conferido antes de enviar. "
                                "É outra chamada paga e não substitui a observação original."),
                        proposed_payload={
                            "observation_id": incident["observation_id"],
                            "instruction": ("Corrija somente o formato e as partes recusadas pelo "
                                            "diagnóstico da tentativa original. Preserve o conteúdo "
                                            "fundamentado; não invente unidades ou relações para "
                                            "satisfazer o validador."),
                            "max_tokens": None,
                            "parent_id": None,
                        })
        elif incident["validator_code"] == "execution_failed":
            plan.update(action="new_collection_review", reason=(
                "A execução original falhou. Avaliar nova coleta independente com autorização."))
    elif incident["criterion_id"] in {"arof.contribution.coverage", "lab.experiment.complete"}:
        plan.update(action="new_collection_review", reason=(
            "Analisar o registro e planejar nova coleta se necessário; "
            "não inserir resultados faltantes no experimento fechado."))
    return plan
