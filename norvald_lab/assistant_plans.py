"""Operation plans and emergency loop detection for the native Lab Assistant.

No token quota, call quota, daily budget, or mandatory approval for ordinary
operations. The only automatic stop is repeated cycles with unchanged inputs.
Plans are persisted before execution and remain separate from experimental RAW.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from norvald_lab.config import identifier


class EmergencyStop(RuntimeError):
    """The operator needs to inspect an apparent repeated-action loop."""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


class AssistantPlans:
    """Durable plans + cycle watch; distinct from experimental and adjustment data."""

    def __init__(self, root: Path):
        self.path = Path(root) / "observer" / "lab_assistant_plans.sqlite3"

    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=15000")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                evidence_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS emergency (
                id INTEGER PRIMARY KEY CHECK(id=1),
                stopped INTEGER NOT NULL,
                reason TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT OR IGNORE INTO emergency(id,stopped,reason,updated_at)
                VALUES (1,0,'','');
            CREATE TABLE IF NOT EXISTS automatic_actions (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                signature TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS presented_plans (
                plan_id TEXT PRIMARY KEY,
                shown_at TEXT NOT NULL
            );
        """)
        if os.name == "posix":
            os.chmod(self.path, 0o600)
        return connection

    def control(self):
        if not self.path.exists():
            return {"stopped": False, "reason": "", "updated_at": ""}
        with closing(self._db()) as db:
            row = db.execute("SELECT * FROM emergency WHERE id=1").fetchone()
            return {"stopped": bool(row["stopped"]), "reason": row["reason"],
                    "updated_at": row["updated_at"]}

    def stop(self, *, reason="Interrupção emergencial solicitada pelo operador."):
        with closing(self._db()) as db:
            with db:
                db.execute("UPDATE emergency SET stopped=1,reason=?,updated_at=? WHERE id=1",
                           (reason, _now()))
        return self.control()

    def resume(self):
        with closing(self._db()) as db:
            with db:
                db.execute("UPDATE emergency SET stopped=0,reason='',updated_at=? WHERE id=1",
                           (_now(),))
                db.execute("DELETE FROM automatic_actions")
        return self.control()

    def create(self, *, action, experiment_id, incident_id="", payload,
               evidence_sha256):
        if action not in {"lab.adjustment.request", "lab.experiment.start"}:
            raise ValueError("Ação de plano não permitida.")
        identifier(experiment_id, "experiment_id")
        if incident_id:
            identifier(incident_id, "incident_id")
        if not isinstance(payload, dict):
            raise ValueError("Payload do plano inválido.")
        if not isinstance(evidence_sha256, str) or len(evidence_sha256) != 64:
            raise ValueError("Hash de evidência inválido.")
        plan_id = "plan-" + secrets.token_hex(16)
        timestamp = _now()
        with closing(self._db()) as db:
            with db:
                db.execute("""
                    INSERT INTO plans
                    (id, action, experiment_id, incident_id, payload, evidence_sha256,
                     status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                """, (plan_id, action, experiment_id, incident_id,
                      _json(payload), evidence_sha256, timestamp, timestamp))
        return self.get(plan_id)

    @staticmethod
    def _read(row):
        value = dict(row)
        value["payload"] = json.loads(value["payload"])
        value["result"] = json.loads(value["result"]) if value["result"] else None
        return value

    def get(self, plan_id):
        identifier(plan_id, "plan_id")
        if not self.path.exists():
            raise FileNotFoundError("Plano não encontrado.")
        with closing(self._db()) as db:
            row = db.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
            if row is None:
                raise FileNotFoundError("Plano não encontrado.")
            return self._read(row)

    def list(self, *, status=None):
        if status is not None and status not in {"planned", "running", "accepted", "failed"}:
            raise ValueError("Estado de plano desconhecido.")
        if not self.path.exists():
            return []
        with closing(self._db()) as db:
            query = "SELECT * FROM plans"
            params = ()
            if status is not None:
                query += " WHERE status=?"
                params = (status,)
            query += " ORDER BY created_at DESC, id"
            return [self._read(row) for row in db.execute(query, params)]

    def mark_presented(self, ids):
        """A response showing the plan was requested by the local UI."""
        with closing(self._db()) as db:
            with db:
                for plan_id in ids:
                    identifier(plan_id, "plan_id")
                    db.execute("""
                        INSERT OR IGNORE INTO presented_plans(plan_id,shown_at)
                        SELECT id,? FROM plans WHERE id=?
                    """, (_now(), plan_id))

    def was_presented(self, plan_id):
        identifier(plan_id, "plan_id")
        if not self.path.exists():
            return False
        with closing(self._db()) as db:
            return db.execute(
                "SELECT 1 FROM presented_plans WHERE plan_id=?", (plan_id,)
            ).fetchone() is not None

    @staticmethod
    def _cycling(last):
        # Never stop simply because the operator executed many different tasks.
        # Detect only a short recurring cycle without any change to the inputs
        # or source evidence: AAAA, ABABABAB, ABCABCABCABC.
        for period in (1, 2, 3):
            if len(last) >= 4 * period:
                tail = last[-4 * period:]
                if all(tail[i:i + period] == tail[:period]
                       for i in range(0, 4 * period, period)):
                    return True
        return False

    def claim(self, plan_id, *, evidence_sha256, automatic=False):
        """Exactly once; an automatic repeated cycle triggers emergency stop."""
        identifier(plan_id, "plan_id")
        with closing(self._db()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                item = db.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
                if item is None:
                    raise FileNotFoundError("Plano não encontrado.")
                if item["status"] != "planned":
                    return self._read(item), False
                emergency = db.execute("SELECT stopped,reason FROM emergency WHERE id=1").fetchone()
                if emergency["stopped"]:
                    raise EmergencyStop("Automação interrompida: " + emergency["reason"])
                if item["evidence_sha256"] != evidence_sha256:
                    raise ValueError("A evidência mudou depois da apresentação do plano. Gere outro.")
                if automatic:
                    signature = _sha({"action": item["action"], "payload": json.loads(item["payload"]),
                                     "evidence_sha256": evidence_sha256})
                    rows = db.execute(
                        "SELECT signature FROM automatic_actions ORDER BY seq DESC LIMIT 11").fetchall()
                    history = [row["signature"] for row in reversed(rows)] + [signature]
                    if self._cycling(history):
                        db.execute("UPDATE emergency SET stopped=1,reason=?,updated_at=? WHERE id=1",
                                   ("Ciclo repetitivo sem mudança de evidência.", _now()))
                        # Commit of emergency flag happens below.
                        stopped = True
                    else:
                        db.execute("INSERT INTO automatic_actions(signature,plan_id,at) VALUES (?,?,?)",
                                   (signature, plan_id, _now()))
                        stopped = False
                else:
                    stopped = False
                if not stopped:
                    db.execute("UPDATE plans SET status='running',updated_at=? WHERE id=?",
                               (_now(), plan_id))
            if stopped:
                raise EmergencyStop("Loop repetitivo detectado. Novas ações interrompidas.")
        return self.get(plan_id), True

    def finish(self, plan_id, result):
        identifier(plan_id, "plan_id")
        if not isinstance(result, dict):
            raise ValueError("Resultado do plano inválido.")
        with closing(self._db()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT status FROM plans WHERE id=?", (plan_id,)).fetchone()
                if row is None:
                    raise FileNotFoundError("Plano não encontrado.")
                if row["status"] != "running":
                    raise ValueError("Plano não está em execução.")
                db.execute("UPDATE plans SET status='accepted',result=?,updated_at=? WHERE id=?",
                           (_json(result), _now(), plan_id))
        return self.get(plan_id)

    def fail(self, plan_id, error):
        identifier(plan_id, "plan_id")
        with closing(self._db()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("UPDATE plans SET status='failed',result=?,updated_at=? "
                           "WHERE id=? AND status='running'",
                           (_json({"error": str(error)}), _now(), plan_id))
        return self.get(plan_id)
