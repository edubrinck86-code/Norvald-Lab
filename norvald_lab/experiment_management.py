"""Observer metadata and editable copies; sealed datasets are never rewritten."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from norvald_lab.config import identifier
from norvald_lab.storage import write_once, verify_experiment


def experiment_template():
    return {"schema_version": "norvald.lab.spec.v1", "experiment_id": "experimento-" + uuid4().hex[:10],
            "mode": "live", "task": {"id": "pergunta", "objective": "", "instructions": ""},
            "participants": [{"id": "analista-1", "name": "Analista 1", "role": "Analista", "provider": "openrouter", "model": "", "reasoning_effort": "off", "sampling": {}}],
            "providers": {"openrouter": {"kind": "openrouter", "credential_env": "OPENROUTER_API_KEY"}},
            "documents": [], "working_context": {"items": [], "relations": []}, "repetitions": 1,
            "condition": {"id": "B1", "exposure": "blind", "tools": "off"},
            "budget": {"max_concurrency": 3, "max_concurrency_per_provider": 2, "timeout_seconds": 300, "max_logical_executions": 1}}


class ExperimentManagement:
    def __init__(self, root: Path):
        self.root = root
        self.deleted = root / "observer" / "excluded_experiments"

    def is_deleted(self, expid):
        return (self.deleted / (identifier(expid) + ".json")).exists()

    def exclude(self, expid):
        identifier(expid)
        if not (self.root / "experiments" / expid / "spec.json").exists():
            raise FileNotFoundError(expid)
        path = self.deleted / (expid + ".json")
        if not path.exists():
            write_once(path, {"experiment_id": expid})

    def restore(self, expid):
        (self.deleted / (identifier(expid) + ".json")).unlink(missing_ok=True)

    def editable_copy(self, expid):
        identifier(expid)
        directory = self.root / "experiments" / expid
        if (directory / "integrity.json").exists() and not verify_experiment(self.root, expid)["valid"]:
            raise ValueError("Registro alterado; cópia da configuração bloqueada.")
        spec = json.loads((directory / "spec.json").read_text())
        spec["experiment_id"] = "experimento-" + uuid4().hex[:10]
        # An edited task/model is a new independent base, not a paired derivative.
        spec["condition"] = {k: v for k, v in spec["condition"].items() if k != "prior_experiment"}
        spec["condition"].update(id="B1", exposure="blind")
        spec["source"] = {"notes": "Configuração copiada de " + expid + "; nova coleta independente."}
        if spec["mode"] == "demo":
            return experiment_template()
        return spec
