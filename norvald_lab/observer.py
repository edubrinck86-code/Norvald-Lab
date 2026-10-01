"""Projeção de leitura e caderno pessoal fora do dataset experimental."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from norvald_lab.config import identifier
from norvald_lab.storage import verify_experiment


def read_jsonl(path: Path, *, provisional: bool = False) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    result = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            # Durante append, só a última linha pode estar em construção.
            if provisional and index == len(lines) - 1 and not line.endswith("\n"):
                break
            raise
    return result


def snapshot(root: Path, experiment_id: str, status: str) -> dict:
    identifier(experiment_id)
    directory = root / "experiments" / experiment_id
    if not (directory / "manifest.json").exists():
        raise FileNotFoundError(experiment_id)
    check = verify_experiment(root, experiment_id) if (directory / "integrity.json").exists() else None
    # Um registro alterado não vira resposta válida na tela de observação.
    if check and not check["valid"]:
        return {"experiment_id": experiment_id, "status": status, "integrity": check,
                "provisional": False, "spec": {}, "requests": [], "events": [], "records": []}
    return {"experiment_id": experiment_id, "status": status, "integrity": check,
            "provisional": check is None,
            "spec": json.loads((directory / "spec.json").read_text()),
            "requests": json.loads((directory / "requests.json").read_text()),
            "events": read_jsonl(directory / "events.jsonl", provisional=check is None),
            "records": [item for path in sorted((directory / "raw").rglob("*.jsonl"))
                        for item in read_jsonl(path, provisional=check is None)]}


class NotebookStore:
    def __init__(self, root: Path):
        self.root = root
        self.directory = root / "observer" / "notes"

    def path(self, note_id: str) -> Path:
        return self.directory / (identifier(note_id, "note_id") + ".json")

    def list(self) -> list[dict]:
        return sorted([json.loads(path.read_text()) for path in self.directory.glob("*.json")],
                      key=lambda note: note["updated_at"], reverse=True)

    def save(self, data: dict, note_id: str | None = None) -> dict:
        if not isinstance(data, dict) or set(data) - {"title", "content", "anchor"}:
            raise ValueError("Nota aceita title, content e anchor.")
        title, content = data.get("title", "Sem título"), data.get("content", "")
        if not isinstance(title, str) or len(title) > 300 or not isinstance(content, str) or len(content) > 1_000_000:
            raise ValueError("Título ou conteúdo da nota inválido.")
        previous = None
        if note_id:
            previous = json.loads(self.path(note_id).read_text())
        anchor = data.get("anchor", previous.get("anchor") if previous else None)
        if previous and anchor != previous.get("anchor"):
            raise ValueError("A referência original da nota não pode ser alterada.")
        if anchor and not previous:
            if not isinstance(anchor, dict) or set(anchor) - {"experiment_id", "observation_id", "excerpt", "event_index"}:
                raise ValueError("Referência da nota inválida.")
            if ("observation_id" in anchor) == ("event_index" in anchor) or ("excerpt" in anchor and "observation_id" not in anchor):
                raise ValueError("Uma nota aponta para um trecho ou um momento, sem misturar referências.")
            expid = identifier(anchor.get("experiment_id"), "experiment_id")
            directory = self.root / "experiments" / expid
            if not directory.is_dir():
                raise ValueError("Experimento da nota não encontrado.")
            if (directory / "integrity.json").exists() and not verify_experiment(self.root, expid)["valid"]:
                raise ValueError("Não é possível fixar um registro alterado.")
            if "observation_id" in anchor:
                records = [r for p in (directory / "raw").rglob("*.jsonl") for r in read_jsonl(p, provisional=True)]
                record = next((r for r in records if r["observation_id"] == anchor["observation_id"]), None)
                excerpt = anchor.get("excerpt", "")
                if record is None or not isinstance(excerpt, str) or not excerpt or excerpt not in ((record.get("result") or {}).get("content") or ""):
                    raise ValueError("Trecho deve existir literalmente na resposta original.")
            elif "event_index" in anchor:
                index = anchor["event_index"]
                if type(index) is not int or not 0 <= index < len(read_jsonl(directory / "events.jsonl", provisional=True)):
                    raise ValueError("Momento não encontrado no registro original.")
            else:
                raise ValueError("Informe o trecho ou momento de origem.")
        now = datetime.now(timezone.utc).isoformat()
        note = {"id": note_id or uuid4().hex, "title": title, "content": content,
                "anchor": anchor, "created_at": previous["created_at"] if previous else now, "updated_at": now}
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.path(note["id"])
        temp = path.with_suffix("." + uuid4().hex + ".tmp")
        try:
            temp.write_text(json.dumps(note, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return note

    def delete(self, note_id: str):
        self.path(note_id).unlink()
