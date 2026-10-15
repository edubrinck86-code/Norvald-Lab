"""Local durable supervision and recurring experiment schedules.

No external integration, no token/cost quota, no modifications to sealed RAW.
A routine is scheduled only after its explicit experimental plan is presented.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from norvald_lab.assistant_plans import _sha
from norvald_lab.config import identifier
from norvald_lab.criteria import evaluate_snapshot
from norvald_lab.observer import snapshot
from norvald_lab.storage import digest, verify_experiment


def utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def _read(row):
    data = dict(row)
    if "spec" in data:
        data["spec"] = json.loads(data["spec"])
    if "result" in data and data["result"]:
        data["result"] = json.loads(data["result"])
    return data


class LabAutomation:
    """Separate observer SQLite storage with routine occurrences and scan cursor."""

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / "observer" / "assistant_automation.sqlite3"

    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS monitor_cursor (
              experiment_id TEXT PRIMARY KEY,
              seal_sha256 TEXT NOT NULL,
              checked_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS routines (
              id TEXT PRIMARY KEY,
              spec TEXT NOT NULL,
              interval_seconds INTEGER NOT NULL,
              next_due TEXT NOT NULL,
              active INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS routine_occurrences (
              id TEXT PRIMARY KEY,
              routine_id TEXT NOT NULL,
              experiment_id TEXT NOT NULL UNIQUE,
              plan_id TEXT NOT NULL,
              scheduled_for TEXT NOT NULL,
              status TEXT NOT NULL,
              result TEXT,
              created_at TEXT NOT NULL,
              UNIQUE(routine_id,scheduled_for)
            );
            CREATE INDEX IF NOT EXISTS routine_occ_idx
              ON routine_occurrences(routine_id,scheduled_for);
        """)
        if os.name == "posix":
            os.chmod(self.path, 0o600)
        return db

    def monitor(self, incidents):
        """Reconcile each newly sealed dataset; never change sealed data."""
        observed, skipped, failures = [], 0, []
        experiments = self.root / "experiments"
        for manifest in sorted(experiments.glob("*/manifest.json")):
            expid = manifest.parent.name
            if not (manifest.parent / "integrity.json").is_file():
                skipped += 1
                continue
            try:
                seal_sha = digest(manifest.parent / "integrity.json")
                with closing(self._db()) as db:
                    previous = db.execute(
                        "SELECT seal_sha256 FROM monitor_cursor WHERE experiment_id=?",
                        (expid,)).fetchone()
                if previous and previous["seal_sha256"] == seal_sha:
                    skipped += 1
                    continue
                verified = verify_experiment(self.root, expid)
                state = snapshot(self.root, expid, verified["status"])
                results = incidents.reconcile(expid, evaluate_snapshot(state))
                with closing(self._db()) as db:
                    with db:
                        db.execute("""
                          INSERT INTO monitor_cursor(experiment_id,seal_sha256,checked_at)
                          VALUES (?,?,?)
                          ON CONFLICT(experiment_id) DO UPDATE SET
                          seal_sha256=excluded.seal_sha256,checked_at=excluded.checked_at
                        """, (expid, seal_sha, iso(utc())))
                observed.append({"experiment_id": expid, "status": results["status"],
                                 "opened": results["opened"]})
            except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
                failures.append({"experiment_id": expid, "error": str(exc)})
        return {"observed": observed, "skipped": skipped, "errors": failures}

    def schedule(self, runner, spec, interval_seconds, first_at):
        if type(interval_seconds) is not int or interval_seconds <= 0:
            raise ValueError("A recorrência deve ser um intervalo positivo em segundos.")
        try:
            first = datetime.fromisoformat(first_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("Informe data e hora ISO 8601 com fuso.") from exc
        if first.tzinfo is None:
            raise ValueError("É obrigatório especificar fuso na data.")
        if first.astimezone(timezone.utc) <= utc():
            raise ValueError("A primeira execução deve ser futura.")
        prepared = runner.prepare(spec)
        rid = "routine-" + uuid4().hex
        with closing(self._db()) as db:
            with db:
                db.execute("""
                    INSERT INTO routines(id,spec,interval_seconds,next_due,active,created_at)
                    VALUES(?,?,?,?,1,?)
                """, (rid, json.dumps(prepared.spec, ensure_ascii=False, sort_keys=True),
                      interval_seconds, iso(first), iso(utc())))
        return self.get(rid)

    def get(self, routine_id):
        identifier(routine_id, "routine_id")
        if not self.path.exists():
            raise FileNotFoundError(routine_id)
        with closing(self._db()) as db:
            row = db.execute("SELECT * FROM routines WHERE id=?", (routine_id,)).fetchone()
        if row is None:
            raise FileNotFoundError(routine_id)
        return _read(row)

    def list(self):
        if not self.path.exists():
            return []
        with closing(self._db()) as db:
            return [_read(x) for x in db.execute("SELECT * FROM routines ORDER BY created_at DESC")]

    def history(self, routine_id):
        self.get(routine_id)
        with closing(self._db()) as db:
            return [_read(x) for x in db.execute(
                "SELECT * FROM routine_occurrences WHERE routine_id=? ORDER BY scheduled_for DESC",
                (routine_id,))]

    def set_active(self, routine_id, active):
        identifier(routine_id, "routine_id")
        if type(active) is not bool:
            raise ValueError("active deve ser booleano.")
        with closing(self._db()) as db:
            with db:
                cursor = db.execute("UPDATE routines SET active=? WHERE id=?",
                                    (int(active), routine_id))
                if cursor.rowcount != 1:
                    raise FileNotFoundError(routine_id)
        return self.get(routine_id)

    def claim_due(self, now=None):
        """Atomically reserve one occurrence; no replay after process crash."""
        now = (now or utc()).astimezone(timezone.utc)
        with closing(self._db()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT * FROM routines WHERE active=1 AND next_due<=? "
                    "ORDER BY next_due,id LIMIT 1", (iso(now),)).fetchone()
                if row is None:
                    return None
                planned_for = row["next_due"]
                next_due = datetime.fromisoformat(planned_for)
                interval = timedelta(seconds=row["interval_seconds"])
                # Skip missed windows rather than replay an unbounded backlog.
                while next_due <= now:
                    next_due += interval
                occurrence_id = "occ-" + uuid4().hex
                experiment_id = row["id"] + "-" + occurrence_id[4:16]
                spec = json.loads(row["spec"])
                spec["experiment_id"] = experiment_id
                db.execute("UPDATE routines SET next_due=? WHERE id=?",
                           (iso(next_due), row["id"]))
                db.execute("""
                    INSERT INTO routine_occurrences
                    (id,routine_id,experiment_id,plan_id,scheduled_for,status,created_at)
                    VALUES(?,?,?,'',?,'reserved',?)
                """, (occurrence_id, row["id"], experiment_id, planned_for, iso(utc())))
        return {"id": occurrence_id, "routine_id": row["id"], "experiment_id": experiment_id,
                "scheduled_for": planned_for, "spec": spec}

    def record(self, occurrence_id, *, plan_id="", status, result=None):
        identifier(occurrence_id, "occurrence_id")
        if status not in {"planned", "accepted", "failed", "blocked"}:
            raise ValueError("Estado de rotina inválido.")
        with closing(self._db()) as db:
            with db:
                db.execute("UPDATE routine_occurrences SET plan_id=?,status=?,result=? WHERE id=?",
                           (plan_id, status,
                            json.dumps(result, ensure_ascii=False) if result else None,
                            occurrence_id))
