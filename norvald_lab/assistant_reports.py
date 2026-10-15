"""Versioned internal evidence packages, not external transmission."""
from __future__ import annotations

from collections import Counter

from norvald_lab.config import identifier
from norvald_lab.criteria import evaluate_snapshot
from norvald_lab.observer import snapshot
from norvald_lab.storage import digest, verify_experiment


def experiment_report(root, experiment_id, *, incidents):
    identifier(experiment_id, "experiment_id")
    integrity = verify_experiment(root, experiment_id)
    if not integrity["valid"]:
        raise ValueError("O relatório exige dados íntegros e selados.")
    state = snapshot(root, experiment_id, integrity["status"])
    checks = evaluate_snapshot(state)
    spec = state["spec"]
    contributions = state.get("contribution_checks") or []
    codes = Counter(row.get("code", "unknown") for row in contributions)
    selected = incidents.list(experiment_id=experiment_id, limit=500)
    observations = [{
        "observation_id": row.get("observation_id"),
        "participant_id": row.get("participant_id"),
        "run_id": row.get("run_id"),
        "usable": row.get("usable"),
        "fully_valid": row.get("fully_valid"),
        "validator_code": row.get("code"),
        "declared_items": row.get("declared_items"),
        "accepted_items": row.get("accepted_items"),
        "declared_relations": row.get("declared_relations"),
        "accepted_relations": row.get("accepted_relations"),
        "rejections": row.get("rejected", []),
    } for row in contributions]
    return {
        "schema_version": "norvald.lab.report.v1",
        "experiment_id": experiment_id,
        "status": integrity["status"],
        "synthetic": spec["mode"] == "demo",
        "design": {
            "task": spec["task"], "condition": spec["condition"],
            "participants": [{
                "id": item["id"], "provider": item["provider"], "model": item["model"],
                "reasoning_effort": item.get("reasoning_effort"),
            } for item in spec["participants"]],
            "repetitions": spec["repetitions"],
            "document_ids": [item["id"] for item in spec["documents"]],
        },
        "provenance": {
            "integrity_valid": integrity["valid"],
            "integrity_sha256": digest(root / "experiments" / experiment_id / "integrity.json"),
            "sealed_records": integrity["records"],
            "raw_not_modified": True,
        },
        "criteria": {"overall": checks["overall"], "evaluations": checks["evaluations"]},
        "observations": observations,
        "summary": {
            "responses": len(observations),
            "usable": sum(row["usable"] is True for row in observations),
            "fully_valid": sum(row["fully_valid"] is True for row in observations),
            "codes": dict(sorted(codes.items())),
            "incidents_recorded": len(selected),
        },
        "incident_refs": [{
            "id": item["id"], "criterion_id": item["criterion_id"],
            "observation_id": item["observation_id"], "status": item["status"],
        } for item in selected],
        "limitations": [
            "O relatório é uma projeção derivada de evidências originais seladas.",
            "Critério atendido não implica validade científica global.",
            "Ajustes posteriores são artefatos separados e não substituem o RAW.",
            "Nenhuma conclusão causal é calculada automaticamente.",
        ],
    }
