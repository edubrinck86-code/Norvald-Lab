"""Cadernos de trabalho pessoais. Nunca alteram registros experimentais."""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from norvald_lab.config import identifier
from norvald_lab.observer import NotebookStore


class RevisionConflict(ValueError):
    pass


class WorkbookStore:
    def __init__(self, root: Path):
        self.directory = root / "observer" / "workbooks"
        self.notes = NotebookStore(root)
        self.lock = threading.RLock()

    def path(self, book_id: str) -> Path:
        return self.directory / (identifier(book_id, "workbook_id") + ".json")

    def get(self, book_id: str) -> dict:
        return json.loads(self.path(book_id).read_text(encoding="utf-8"))

    def list(self) -> list[dict]:
        with self.lock:
            return sorted([json.loads(p.read_text(encoding="utf-8")) for p in self.directory.glob("*.json")],
                          key=lambda b: b["updated_at"], reverse=True)

    def write(self, book: dict) -> dict:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.path(book["id"])
        temp = path.with_suffix("." + uuid4().hex + ".tmp")
        try:
            temp.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return book

    def check_revision(self, book: dict, revision):
        if type(revision) is not int or revision != book["revision"]:
            raise RevisionConflict("Este caderno mudou em outra aba. Sua edição permanece na tela; confira a versão salva antes de substituir.")

    def save(self, data: dict, book_id: str | None = None) -> dict:
        with self.lock:
            if set(data) - {"title", "blocks", "revision"}:
                raise ValueError("Caderno aceita title, blocks e revision.")
            previous = self.get(book_id) if book_id else None
            if previous:
                self.check_revision(previous, data.get("revision"))
            title, blocks = data.get("title", "Meu caderno"), data.get("blocks", [])
            if not isinstance(title, str) or len(title) > 300 or not isinstance(blocks, list) or len(blocks) > 500:
                raise ValueError("Título ou lista de blocos inválidos.")
            ids, sources = set(), [b.get("source_note") for b in previous["blocks"] if b.get("source_note")] if previous else []
            old = {b["id"]: b for b in previous["blocks"]} if previous else {}
            normalized = []
            for block in blocks:
                if not isinstance(block, dict) or set(block) - {"id", "title", "content", "type", "source_note"}:
                    raise ValueError("Bloco inválido.")
                bid = identifier(block.get("id"), "block_id")
                if bid in ids:
                    raise ValueError("IDs de bloco repetidos.")
                ids.add(bid)
                for field, limit in (("title", 300), ("content", 1_000_000), ("type", 100)):
                    if not isinstance(block.get(field, ""), str) or len(block.get(field, "")) > limit:
                        raise ValueError("Título, conteúdo ou tipo do bloco inválido.")
                source = block.get("source_note")
                if bid in old and source != old[bid].get("source_note"):
                    raise ValueError("A origem capturada de um bloco não pode ser alterada.")
                if source is not None and source not in sources:
                    raise ValueError("Use a captura de nota para vincular uma origem existente.")
                normalized.append({"id": bid, "title": block.get("title", ""), "content": block.get("content", ""),
                                   "type": block.get("type", "Contexto"), "source_note": source})
            if sum(len(b["content"]) for b in normalized) > 5_000_000:
                raise ValueError("Caderno excede o limite de conteúdo.")
            now = datetime.now(timezone.utc).isoformat()
            return self.write({"id": book_id or uuid4().hex, "title": title, "blocks": normalized,
                               "revision": previous["revision"] + 1 if previous else 1,
                               "created_at": previous["created_at"] if previous else now, "updated_at": now})

    def capture_note(self, book_id: str, note_id: str, revision: int) -> dict:
        with self.lock:
            book = self.get(book_id)
            self.check_revision(book, revision)
            note = json.loads(self.notes.path(note_id).read_text(encoding="utf-8"))
            if len(book["blocks"]) >= 500 or sum(len(b["content"]) for b in book["blocks"]) + len(note["content"]) > 5_000_000:
                raise ValueError("Caderno excede o limite de blocos ou conteúdo.")
            now = datetime.now(timezone.utc).isoformat()
            book["blocks"].append({"id": uuid4().hex, "title": note["title"], "content": note["content"], "type": "Observação",
                                   "source_note": {**note, "captured_at": now}})
            book.update(revision=book["revision"] + 1, updated_at=now)
            return self.write(book)

    def corpus(self, book_id: str, revision: int, block_ids: list[str] | None = None) -> dict:
        with self.lock:
            book = self.get(book_id)
            self.check_revision(book, revision)
            blocks = book["blocks"]
            if block_ids is not None:
                if not isinstance(block_ids, list) or not block_ids or not all(isinstance(i, str) for i in block_ids) or len(set(block_ids)) != len(block_ids):
                    raise ValueError("Selecione uma lista de IDs de blocos distintos.")
                if set(block_ids) - {b["id"] for b in blocks}:
                    raise ValueError("Bloco selecionado não encontrado.")
                blocks = [b for b in blocks if b["id"] in block_ids]
            if not blocks or not any(b["content"].strip() for b in blocks):
                raise ValueError("Escreva conteúdo antes de incluir o caderno no corpus.")
            text = "# " + book["title"] + "\n\n" + "\n\n".join("## " + (b["title"] or "Sem título") + "\n\n" + b["content"] for b in blocks) + "\n"
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return {"workbook_id": book_id, "revision": revision, "block_ids": [b["id"] for b in blocks], "sha256": digest,
                    "document": {"id": f"caderno-{book_id[:12]}-r{revision}-{digest[:12]}", "title": book["title"], "text": text,
                                 "source": f"notebook:{book_id}:r{revision}:sha256:{digest}"}}
