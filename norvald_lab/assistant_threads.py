"""Local conversational threads and typed operation events; no remote transport.

The original assistant_messages remains the immutable message store. Each new
thread uses its own identifier as that table's existing conversation key, so
the legacy incident and general transcripts are not lost or migrated.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from norvald_lab.config import identifier


def now():
    return datetime.now(timezone.utc).isoformat()


class AssistantThreads:
    def __init__(self, root: Path):
        self.path = Path(root) / "observer" / "assistant_threads.sqlite3"

    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                context TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS operation_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL REFERENCES threads(id),
                tool TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS thread_events_idx
                ON operation_events(thread_id,seq);
        """)
        if os.name == "posix":
            os.chmod(self.path, 0o600)
        return db

    @staticmethod
    def _thread(row):
        item = dict(row)
        item["context"] = json.loads(item["context"])
        return item

    def create(self, title="Nova conversa"):
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Informe um título de conversa.")
        thread_id = "chat-" + uuid4().hex
        moment = now()
        with closing(self._db()) as db:
            with db:
                db.execute("""
                    INSERT INTO threads(id,title,context,created_at,updated_at)
                    VALUES(?,?,?,?,?)
                """, (thread_id, title.strip(), "{}", moment, moment))
        return self.get(thread_id)

    def list(self):
        if not self.path.exists():
            return []
        with closing(self._db()) as db:
            return [self._thread(row) for row in db.execute(
                "SELECT * FROM threads ORDER BY updated_at DESC,id")]

    def get(self, thread_id):
        identifier(thread_id, "thread_id")
        if not thread_id.startswith("chat-"):
            raise FileNotFoundError("Conversa não encontrada.")
        if not self.path.exists():
            raise FileNotFoundError("Conversa não encontrada.")
        with closing(self._db()) as db:
            row = db.execute("SELECT * FROM threads WHERE id=?", (thread_id,)).fetchone()
        if row is None:
            raise FileNotFoundError("Conversa não encontrada.")
        return self._thread(row)

    def touch(self, thread_id, *, text=None, context=None):
        if context is not None and not isinstance(context, dict):
            raise ValueError("Contexto inválido.")
        item = self.get(thread_id)
        title = item["title"]
        if text and title == "Nova conversa":
            title = " ".join(text.split())[:92]
        with closing(self._db()) as db:
            with db:
                db.execute("""
                    UPDATE threads SET title=?,context=?,updated_at=? WHERE id=?
                """, (title, json.dumps(context if context is not None else item["context"],
                                        ensure_ascii=False), now(), thread_id))
        return self.get(thread_id)

    def add_event(self, thread_id, *, tool, operation, status, payload):
        self.get(thread_id)
        if status not in {"ok", "error", "blocked"} or not isinstance(payload, dict):
            raise ValueError("Evento de ferramenta inválido.")
        with closing(self._db()) as db:
            with db:
                db.execute("""
                    INSERT INTO operation_events(thread_id,tool,operation,status,payload,at)
                    VALUES(?,?,?,?,?,?)
                """, (thread_id, tool, operation, status,
                      json.dumps(payload, ensure_ascii=False, default=str), now()))

    def events(self, thread_id):
        self.get(thread_id)
        with closing(self._db()) as db:
            rows = db.execute("""
                SELECT seq,tool,operation,status,payload,at
                FROM operation_events WHERE thread_id=? ORDER BY seq
            """, (thread_id,)).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]
