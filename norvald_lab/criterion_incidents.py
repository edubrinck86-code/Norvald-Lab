"""Durable criterion incidents outside the sealed experimental dataset.

Adapted from Huginn's incident aggregation and diary concepts. Reconciliation is
explicit, deterministic and idempotent: it records unmet criteria but never
repairs, dismisses, or reclassifies an original observation.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from norvald_lab.config import identifier

SCHEMA_VERSION = "norvald.lab.criterion_incident.v1"


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _identity(experiment_id, check):
    evidence = check.get("evidence") or {}
    coordinates = {
        "experiment_id": experiment_id,
        "criterion_id": check["criterion_id"],
        "criterion_version": check["criterion_version"],
        "observation_id": evidence.get("observation_id") or "",
        "participant_id": evidence.get("participant_id") or "",
        "run_id": evidence.get("run_id") or "",
    }
    digest = hashlib.sha256(_json(coordinates).encode("utf-8")).hexdigest()[:32]
    return "ci-" + digest, coordinates


def _decode(row):
    data = dict(row)
    data["evidence"] = json.loads(data["evidence"])
    return data


class CriterionIncidents:
    """SQLite ledger under observer/; never within experiments/<id>."""

    def __init__(self, root: Path):
        self.path = Path(root) / "observer" / "criterion_incidents.sqlite3"

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=15)
        if os.name == "posix":
            os.chmod(self.path, 0o600)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS criterion_incidents (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                criterion_id TEXT NOT NULL,
                criterion_version TEXT NOT NULL,
                observation_id TEXT NOT NULL,
                participant_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                status TEXT NOT NULL,
                validator_code TEXT NOT NULL,
                message TEXT NOT NULL,
                evidence TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS incident_experiment
                ON criterion_incidents(experiment_id, status, first_seen);
            CREATE TABLE IF NOT EXISTS criterion_incident_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                event TEXT NOT NULL,
                at TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS incident_event_history
                ON criterion_incident_events(incident_id, seq);
        """)
        return db

    def reconcile(self, experiment_id: str, evaluation: dict) -> dict:
        """Record only observed not_met conditions. Never auto-close incidents."""
        identifier(experiment_id, "experiment_id")
        if evaluation.get("subject") != {"type": "experiment", "experiment_id": experiment_id}:
            raise ValueError("Avaliação não corresponde ao experimento.")
        if evaluation.get("schema_version") != "norvald.lab.criteria.v1":
            raise ValueError("Versão de avaliação incompatível.")
        checks = evaluation.get("evaluations")
        if not isinstance(checks, list):
            raise ValueError("Avaliação não possui critérios.")
        integrity = next((row for row in checks if row["criterion_id"] == "lab.dataset.integrity"), None)
        if integrity is None or integrity["status"] == "pending":
            return {"experiment_id": experiment_id, "status": "pending",
                    "opened": [], "updated": [], "unchanged": 0}
        violations = [row for row in checks if row["status"] == "not_met"]
        opened, updated, unchanged = [], [], 0
        with closing(self._connect()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                for check in violations:
                    identity, coordinates = _identity(experiment_id, check)
                    current = db.execute("SELECT * FROM criterion_incidents WHERE id=?", (identity,)).fetchone()
                    evidence = _json(check.get("evidence") or {})
                    code, message = str(check["code"]), str(check["message"])
                    if current is None:
                        now = _utc()
                        db.execute("""
                            INSERT INTO criterion_incidents
                            (id, experiment_id, criterion_id, criterion_version, observation_id,
                             participant_id, run_id, status, validator_code, message, evidence,
                             first_seen, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)
                        """, (identity, experiment_id, coordinates["criterion_id"],
                              coordinates["criterion_version"], coordinates["observation_id"],
                              coordinates["participant_id"], coordinates["run_id"],
                              code, message, evidence, now, now))
                        self._event(db, identity, "detected", {"code": code})
                        opened.append(identity)
                    elif (current["validator_code"], current["message"], current["evidence"]) != (code, message, evidence):
                        db.execute("""
                            UPDATE criterion_incidents
                            SET validator_code=?, message=?, evidence=?, last_updated=?
                            WHERE id=?
                        """, (code, message, evidence, _utc(), identity))
                        self._event(db, identity, "evidence_changed", {"code": code})
                        updated.append(identity)
                    else:
                        unchanged += 1
        return {"experiment_id": experiment_id, "status": "reconciled",
                "opened": opened, "updated": updated, "unchanged": unchanged}

    @staticmethod
    def _event(db, identity, kind, payload):
        db.execute(
            "INSERT INTO criterion_incident_events(incident_id, event, at, payload) VALUES (?, ?, ?, ?)",
            (identity, kind, _utc(), _json(payload)))

    def list(self, *, experiment_id=None, status=None, limit=100):
        if experiment_id is not None:
            identifier(experiment_id, "experiment_id")
        if status is not None and status not in {"open", "acknowledged", "escalated"}:
            raise ValueError("Estado de incidente desconhecido.")
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("Limite de consulta inválido.")
        if not self.path.exists():
            return []
        query = "SELECT * FROM criterion_incidents WHERE 1=1"
        params = []
        if experiment_id is not None:
            query += " AND experiment_id=?"
            params.append(experiment_id)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY first_seen DESC, id LIMIT ?"
        with closing(self._connect()) as db:
            return [_decode(row) for row in db.execute(query, (*params, limit))]

    def all_matching(self, *, experiment_id=None, status=None):
        """Internal complete cursor scan; never capped by UI pagination."""
        if experiment_id is not None:
            identifier(experiment_id, "experiment_id")
        if status is not None and status not in {"open", "acknowledged", "escalated"}:
            raise ValueError("Estado de incidente desconhecido.")
        if not self.path.exists():
            return []
        query = "SELECT * FROM criterion_incidents WHERE 1=1"
        args = []
        if experiment_id is not None:
            query += " AND experiment_id=?"
            args.append(experiment_id)
        if status is not None:
            query += " AND status=?"
            args.append(status)
        query += " ORDER BY first_seen DESC,id"
        with closing(self._connect()) as db:
            return [_decode(row) for row in db.execute(query, args)]

    def get(self, incident_id: str):
        identifier(incident_id, "incident_id")
        if not self.path.exists():
            raise FileNotFoundError("Incidente não encontrado.")
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM criterion_incidents WHERE id=?", (incident_id,)).fetchone()
            if row is None:
                raise FileNotFoundError("Incidente não encontrado.")
            events = db.execute(
                "SELECT seq, event, at, payload FROM criterion_incident_events "
                "WHERE incident_id=? ORDER BY seq", (incident_id,)).fetchall()
            return _decode(row) | {"history": [
                {"seq": event["seq"], "event": event["event"], "at": event["at"],
                 "payload": json.loads(event["payload"])} for event in events]}

    def record_action(self, incident_id: str, *, event: str, payload: dict):
        """Append a confirmed owner action without changing criterion truth."""
        identifier(incident_id, "incident_id")
        if event not in {"assistant.adjustment_requested"}:
            raise ValueError("Evento de auditoria não permitido.")
        if not isinstance(payload, dict) or set(payload) != {"adjustment_id"}:
            raise ValueError("Registro deve conter somente o ID do ajuste.")
        identifier(payload["adjustment_id"], "adjustment_id")
        with closing(self._connect()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                found = db.execute("SELECT id FROM criterion_incidents WHERE id=?",
                                   (incident_id,)).fetchone()
                if found is None:
                    raise FileNotFoundError("Incidente não encontrado.")
                self._event(db, incident_id, event, payload | {"actor": "owner"})

    def mark(self, incident_id: str, *, status: str, note: str):
        identifier(incident_id, "incident_id")
        if status not in {"acknowledged", "escalated"}:
            raise ValueError("A ação não pode declarar a falha resolvida.")
        if not isinstance(note, str) or not note.strip() or len(note) > 2000:
            raise ValueError("Informe um motivo de 1 a 2.000 caracteres.")
        with closing(self._connect()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT status, note FROM criterion_incidents WHERE id=?",
                                 (incident_id,)).fetchone()
                if row is None:
                    raise FileNotFoundError("Incidente não encontrado.")
                if row["status"] == status and row["note"] == note.strip():
                    return self.get(incident_id)
                db.execute("UPDATE criterion_incidents SET status=?, note=?, last_updated=? WHERE id=?",
                           (status, note.strip(), _utc(), incident_id))
                self._event(db, incident_id, status, {"note": note.strip(), "actor": "owner"})
        return self.get(incident_id)
