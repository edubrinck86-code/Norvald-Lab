"""Deterministic criterion projections over existing Lab validators; never alter RAW."""
from __future__ import annotations

from collections.abc import Mapping

from norvald_lab.config import validate_spec

SCHEMA_VERSION = "norvald.lab.criteria.v1"


def _criterion(identifier, status, code, message, *, evidence=None):
    return {
        "criterion_id": identifier,
        "criterion_version": "1",
        "status": status,
        "code": code,
        "message": str(message),
        "evidence": evidence or {},
    }


def _overall(evaluations):
    states = {item["status"] for item in evaluations}
    if "not_met" in states:
        return "not_met"
    if "pending" in states:
        return "pending"
    if "not_evaluable" in states:
        return "not_evaluable"
    return "met"


def evaluate_spec(runner, payload):
    """Explain validation/preparation, including failures, without writing or calling LLMs.

    A successful result is a prepared *draft*, not permission to start collection.
    """
    checks = []
    try:
        validated = validate_spec(payload)
    except (ValueError, KeyError, TypeError) as exc:
        checks.append(_criterion("lab.spec.structure", "not_met", "invalid_spec", str(exc)))
        checks.append(_criterion("lab.spec.preparation", "not_evaluable", "invalid_spec",
                                 "A preparação depende de uma especificação estruturalmente válida."))
        return {"schema_version": SCHEMA_VERSION, "subject": {"type": "spec"},
                "overall": _overall(checks), "evaluations": checks, "fingerprint": None}
    checks.append(_criterion("lab.spec.structure", "met", "valid_spec",
                             "A especificação passou nas regras de validate_spec."))
    try:
        prepared = runner.prepare(validated)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        checks.append(_criterion("lab.spec.preparation", "not_met", "prepare_rejected", str(exc)))
        fingerprint = None
    else:
        checks.append(_criterion("lab.spec.preparation", "met", "prepared",
                                 "O Runner preparou e congelou as requisições sem executá-las.",
                                 evidence={"planned_requests": len(prepared.requests_json)}))
        fingerprint = prepared.condition_fingerprint
    return {"schema_version": SCHEMA_VERSION,
            "subject": {"type": "spec", "experiment_id": validated["experiment_id"]},
            "overall": _overall(checks), "evaluations": checks, "fingerprint": fingerprint}


def evaluate_snapshot(value):
    """Evaluate only authenticated-by-integrity closed snapshots for contribution criteria.

    Provisional/altered datasets cannot be represented as satisfying a criterion.
    This is a projection of the parser's existing decisions, not a new validator.
    """
    expid = value.get("experiment_id", "")
    checks = []
    integrity = value.get("integrity")
    sealed = isinstance(integrity, Mapping) and integrity.get("valid") is True and not value.get("provisional")
    if sealed:
        checks.append(_criterion("lab.dataset.integrity", "met", "integrity_verified",
                                 "O fechamento passou na verificação de integridade.",
                                 evidence={"experiment_id": expid}))
    elif isinstance(integrity, Mapping) and integrity.get("valid") is False:
        checks.append(_criterion("lab.dataset.integrity", "not_met", "integrity_failed",
                                 "O fechamento não passou na verificação de integridade.",
                                 evidence={"issues": integrity.get("issues", [])}))
    else:
        checks.append(_criterion("lab.dataset.integrity", "pending", "unsealed",
                                 "O fechamento íntegro ainda não está disponível."))
    state = value.get("status", "unknown")
    state_result = ("met" if state == "complete"
                    else "not_met" if state in {"failed", "incomplete", "aborted"}
                    else "pending")
    checks.append(_criterion("lab.experiment.complete", state_result, str(state),
                             "Estado de fechamento da execução, não uma avaliação científica."))

    spec = value.get("spec") or {}
    participants = spec.get("participants") or []
    repetitions = spec.get("repetitions", 0)
    if not sealed or not isinstance(repetitions, int) or repetitions < 1 or not participants:
        checks.append(_criterion("arof.contribution.coverage", "not_evaluable", "snapshot_unavailable",
                                 "É necessário um snapshot íntegro e um desenho experimental legível."))
    else:
        expected = {(p["id"], "r" + str(i).zfill(4))
                    for p in participants for i in range(1, repetitions + 1)}
        diagnostics = value.get("contribution_checks") or []
        actual = [(row.get("participant_id"), row.get("run_id")) for row in diagnostics]
        missing = sorted(expected - set(actual))
        duplicates = len(actual) != len(set(actual))
        unexpected = sorted(set(actual) - expected)
        accepted = not missing and not duplicates and not unexpected
        checks.append(_criterion("arof.contribution.coverage", "met" if accepted else "not_met",
                                 "complete_coverage" if accepted else "incomplete_coverage",
                                 "Diagnósticos por participante e repetição associados ao desenho.",
                                 evidence={"expected": len(expected), "observed": len(actual),
                                           "missing": [{"participant_id": p, "run_id": run} for p, run in missing],
                                           "unexpected": [{"participant_id": p, "run_id": run} for p, run in unexpected],
                                           "duplicate_pairs": duplicates}))
        for row in diagnostics:
            evidence = {"observation_id": row.get("observation_id"),
                        "participant_id": row.get("participant_id"),
                        "run_id": row.get("run_id"),
                        "validator_code": row.get("code"),
                        "declared_items": row.get("declared_items"),
                        "accepted_items": row.get("accepted_items"),
                        "declared_relations": row.get("declared_relations"),
                        "accepted_relations": row.get("accepted_relations"),
                        "rejected": row.get("rejected", [])}
            for identifier, flag in (("arof.contribution.usable", "usable"),
                                     ("arof.contribution.fully_valid", "fully_valid")):
                # Never infer acceptance when a field is absent.
                if row.get(flag) is None:
                    status = "not_evaluable"
                else:
                    status = "met" if row[flag] is True else "not_met"
                checks.append(_criterion(identifier, status, str(row.get("code") or "unavailable"),
                                         row.get("message") or "Sem diagnóstico estruturado.",
                                         evidence=evidence))
    return {"schema_version": SCHEMA_VERSION, "subject": {"type": "experiment", "experiment_id": expid},
            "overall": _overall(checks), "evaluations": checks}
