"""Explicit owner gate for destructive Assistant actions.

Only reversible exclusion of a listed experiment is available. No path can
remove RAW, erase seals, modify credentials or bypass owner confirmation.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from norvald_lab.config import identifier


def _now():
    return datetime.now(timezone.utc)


class DestructiveRequests:
    def __init__(self, root: Path, management):
        self.path = Path(root) / "observer" / "assistant_destructive.sqlite3"
        self.management = management

    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS requests (
              id TEXT PRIMARY KEY,
              action TEXT NOT NULL,
              experiment_id TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              completed_at TEXT
            );
        """)
        if os.name == "posix":
            os.chmod(self.path, 0o600)
        return db

    def stage_exclusion(self, experiment_id):
        identifier(experiment_id, "experiment_id")
        if not (self.management.root / "experiments" / experiment_id / "spec.json").is_file():
            raise FileNotFoundError("Experimento não encontrado.")
        if self.management.is_deleted(experiment_id):
            raise ValueError("O experimento já foi excluído da lista.")
        request_id = "destructive-" + uuid4().hex
        created = _now()
        with closing(self._db()) as db:
            with db:
                db.execute("""
                    INSERT INTO requests(id,action,experiment_id,status,created_at,expires_at)
                    VALUES (?,'lab.experiment.exclude','?','requested',?,?)
                """.replace("'?'", "?"), (request_id, experiment_id,
                                             created.isoformat(),
                                             (created + timedelta(minutes=10)).isoformat()))
        return self.get(request_id)

    def get(self, request_id):
        identifier(request_id, "request_id")
        if not self.path.exists():
            raise FileNotFoundError("Solicitação inexistente.")
        with closing(self._db()) as db:
            row = db.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
            if row is None:
                raise FileNotFoundError("Solicitação inexistente.")
            return dict(row)

    def list(self):
        if not self.path.exists():
            return []
        with closing(self._db()) as db:
            return [dict(x) for x in db.execute(
                "SELECT * FROM requests ORDER BY created_at DESC,id")]

    def confirm_exclusion(self, request_id, *, experiment_id, confirmed):
        identifier(request_id, "request_id")
        identifier(experiment_id, "experiment_id")
        if confirmed is not True:
            raise ValueError("Confirmação explícita necessária para a ação destrutiva.")
        with closing(self._db()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
                if row is None:
                    raise FileNotFoundError("Solicitação inexistente.")
                if (row["status"] != "requested"
                        or row["experiment_id"] != experiment_id
                        or row["action"] != "lab.experiment.exclude"
                        or row["expires_at"] <= _now().isoformat()):
                    raise ValueError("Solicitação vencida, utilizada ou identificador divergente.")
                db.execute("UPDATE requests SET status='claimed' WHERE id=?", (request_id,))
        try:
            self.management.exclude(experiment_id)
        except Exception:
            # The claim is consumed even when the filesystem write fails.
            with closing(self._db()) as db:
                with db:
                    db.execute("UPDATE requests SET status='failed',completed_at=? WHERE id=?",
                               (_now().isoformat(), request_id))
            raise
        with closing(self._db()) as db:
            with db:
                db.execute("UPDATE requests SET status='executed',completed_at=? WHERE id=?",
                           (_now().isoformat(), request_id))
        return self.get(request_id)
