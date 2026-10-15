"""Verified descriptive comparison, without causal inference or RAW mutation."""
from __future__ import annotations

from collections import Counter

from norvald_lab.config import identifier
from norvald_lab.observer import snapshot
from norvald_lab.storage import verify_experiment

SCHEMA_VERSION = "norvald.lab.comparison.v1"


def _verified(root, experiment_id):
    identifier(experiment_id, "experiment_id")
    checked = verify_experiment(root, experiment_id)
    if not checked.get("valid") or checked.get("status") != "complete":
        raise ValueError("A comparação exige experimento íntegro: " + experiment_id)
    state = snapshot(root, experiment_id, "complete")
    if state.get("provisional") or state.get("status") != "complete":
        raise ValueError("A comparação exige fechamento completo: " + experiment_id)
    return state


def _measure(state):
    checks = state.get("contribution_checks") or []
    by_pair = {}
    for row in checks:
        pair = (row.get("participant_id"), row.get("run_id"))
        if pair in by_pair:
            raise ValueError("Diagnóstico duplicado na comparação.")
        by_pair[pair] = row
    counts = Counter(row.get("code", "unknown") for row in checks)
    return by_pair, {"responses": len(checks),
                     "usable": sum(x.get("usable") is True for x in checks),
                     "fully_valid": sum(x.get("fully_valid") is True for x in checks),
                     "validator_codes": dict(sorted(counts.items()))}


def compare_experiments(root, left_id, right_id):
    if left_id == right_id:
        raise ValueError("Escolha dois experimentos distintos.")
    first, second = _verified(root, left_id), _verified(root, right_id)
    left, ls = _measure(first)
    right, rs = _measure(second)
    common = sorted(left.keys() & right.keys())
    only_first = sorted(left.keys() - right.keys())
    only_second = sorted(right.keys() - left.keys())

    def descriptor(row):
        return {"observation_id": row.get("observation_id"),
                "validator_code": row.get("code"),
                "usable": row.get("usable") is True,
                "fully_valid": row.get("fully_valid") is True,
                "declared_items": row.get("declared_items", 0),
                "accepted_items": row.get("accepted_items", 0),
                "declared_relations": row.get("declared_relations", 0),
                "accepted_relations": row.get("accepted_relations", 0)}
    aligned = [{
        "participant_id": participant, "run_id": run,
        "left": descriptor(left[(participant, run)]),
        "right": descriptor(right[(participant, run)]),
    } for participant, run in common]
    specs = [first["spec"], second["spec"]]
    same_models = {
        tuple(sorted((p["id"], p["provider"], p["model"]) for p in item["participants"]))
        for item in specs
    }
    comparability = {
        "participants_and_models_match": len(same_models) == 1,
        "same_task": specs[0]["task"] == specs[1]["task"],
        "same_documents": specs[0]["documents"] == specs[1]["documents"],
        "same_repetitions": specs[0]["repetitions"] == specs[1]["repetitions"],
        "condition": [item["condition"]["exposure"] for item in specs],
        "source_relation": (specs[1]["condition"].get("prior_experiment") == left_id
                            or specs[0]["condition"].get("prior_experiment") == right_id),
        "shared_observation_pairs": len(common),
    }
    comparable = (comparability["participants_and_models_match"] and
                  comparability["same_task"] and comparability["same_documents"] and
                  comparability["same_repetitions"] and not only_first and not only_second)
    return {"schema_version": SCHEMA_VERSION,
            "left_experiment_id": left_id, "right_experiment_id": right_id,
            "left": ls, "right": rs,
            "differences": {"responses": rs["responses"] - ls["responses"],
                            "usable": rs["usable"] - ls["usable"],
                            "fully_valid": rs["fully_valid"] - ls["fully_valid"]},
            "comparability": comparability | {"structurally_aligned": comparable},
            "pairs": aligned,
            "unmatched_left": [{"participant_id": x, "run_id": r} for x, r in only_first],
            "unmatched_right": [{"participant_id": x, "run_id": r} for x, r in only_second],
            "limitations": [
                "Comparação descritiva de critérios e metadados verificados, não teste de causalidade.",
                "Alinhamento estrutural não estabelece equivalência científica do protocolo.",
                "Uma validação de ajuste posterior não substitui a observação original.",
                "Diferenças de exposição, contexto ou modelos exigem interpretação independente.",
            ]}
