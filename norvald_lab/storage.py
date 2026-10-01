from __future__ import annotations

import hashlib
import json
from pathlib import Path

from norvald_lab.config import identifier
from norvald_lab.infrastructure.arof.dataset_store import replay_jsonl


def write_once(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(directory: Path) -> None:
    files = {str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob("*")) if p.is_file() and p.name != "integrity.json"}
    write_once(directory / "integrity.json", {"schema_version": "norvald.lab.integrity.v1", "algorithm": "sha256", "files": files})


def verify_experiment(root: Path, experiment_id: str) -> dict:
    identifier(experiment_id, "experiment_id")
    directory = root / "experiments" / experiment_id
    integrity = json.loads((directory / "integrity.json").read_text())
    problems = []
    for name, expected in integrity["files"].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()):
            problems.append(f"Caminho fora do experimento: {name}")
        elif not path.is_file() or digest(path) != expected:
            problems.append(f"Arquivo ausente ou alterado: {name}")
    present = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file() and p.name != "integrity.json"}
    if present != set(integrity["files"]):
        problems.append("O conjunto de arquivos mudou depois do fechamento.")
    completion = json.loads((directory / "completion.json").read_text())
    paths = []
    for item in completion["files"]:
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(directory.resolve()):
            problems.append("RAW fora do diretório do experimento.")
        elif not path.exists() or digest(path) != item["sha256"]:
            problems.append(f"RAW alterado: {item['path']}")
        else:
            paths.append(path)
    replay = replay_jsonl(paths)
    problems.extend(issue.message for issue in replay.issues)
    return {"experiment_id": experiment_id, "valid": not problems, "status": completion["status"], "records": len(replay.records), "issues": problems}


def read_verified_records(root: Path, experiment_id: str):
    check = verify_experiment(root, experiment_id)
    if not check["valid"] or check["status"] != "complete":
        raise ValueError("Origem precisa estar completa e íntegra: " + str(check))
    directory = root / "experiments" / experiment_id
    completion = json.loads((directory / "completion.json").read_text())
    return replay_jsonl([root / item["path"] for item in completion["files"]]).records
