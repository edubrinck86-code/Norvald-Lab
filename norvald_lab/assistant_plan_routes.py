"""Staged non-destructive Lab Assistant operations, with plans shown first."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException

from norvald_lab.assistant_plans import AssistantPlans, EmergencyStop, _sha
from norvald_lab.assistant_automation import LabAutomation
from norvald_lab.assistant_destructive import DestructiveRequests
from norvald_lab.storage import digest


def plan_router(root: Path, runner, adjustments, incidents, settings, incident_detail,
                start_experiment, live_enabled, logger, plans: AssistantPlans,
                automation: LabAutomation, destructive: DestructiveRequests):
    router = APIRouter(prefix="/api/assistant")
    tick_lock = asyncio.Lock()

    @router.get("/destructive/requests")
    def list_destructive_requests():
        return destructive.list()

    @router.post("/destructive/exclusion/plan")
    def stage_exclusion(payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"experiment_id"}:
            raise HTTPException(422, "Informe somente experiment_id.")
        try:
            request = destructive.stage_exclusion(payload["experiment_id"])
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"request": request, "requires_owner_confirmation": True,
                "raw_deleted": False,
                "effect": "Somente ocultar o experimento da lista; restauração possível."}

    @router.post("/destructive/requests/{request_id}/confirm")
    def confirm_exclusion(request_id: str, payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"experiment_id", "confirmed"}:
            raise HTTPException(422, "Informe experiment_id e confirmed.")
        try:
            return destructive.confirm_exclusion(
                request_id, experiment_id=payload["experiment_id"],
                confirmed=payload["confirmed"])
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.get("/emergency")
    def emergency_state():
        return plans.control()

    @router.post("/emergency/stop")
    def emergency_stop():
        """Blocks further actions, without touching sealed RAW."""
        return plans.stop()

    @router.post("/emergency/resume")
    def emergency_resume():
        return plans.resume()

    @router.post("/incidents/{incident_id}/adjustment/plan")
    def plan_adjustment(incident_id: str, payload: dict):
        if not isinstance(payload, dict) or set(payload) - {"instruction", "max_tokens"}:
            raise HTTPException(422, "O plano aceita apenas instruction e max_tokens.")
        detail = incident_detail(incident_id)
        policy = detail["recovery"]
        if not policy["allowed"] or policy["action"] != "preview_adjustment":
            raise HTTPException(409, "O critério não permite este ajuste.")
        proposed = dict(policy["proposed_payload"])
        proposed.update(payload)
        try:
            saved, _ = adjustments.prepare(detail["experiment_id"], proposed, persist=False)
            plan = plans.create(
                action="lab.adjustment.request", experiment_id=detail["experiment_id"],
                incident_id=incident_id, payload=proposed,
                evidence_sha256=saved["source_integrity_sha256"])
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, settings.redact(str(exc))) from exc
        return {"plan": plan, "preview": saved, "requires_approval": False,
                "independent_sample": False}

    @router.post("/plans/experiment")
    def plan_experiment(payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"spec"} or not isinstance(payload["spec"], dict):
            raise HTTPException(422, "Informe a especificação do experimento em spec.")
        try:
            prepared = runner.prepare(payload["spec"])
            plan = plans.create(
                action="lab.experiment.start",
                experiment_id=prepared.spec["experiment_id"],
                payload={"spec": prepared.spec}, evidence_sha256=_sha(prepared.spec))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(422, settings.redact(str(exc))) from exc
        return {"plan": plan,
                "planning": {"objective": prepared.spec["task"]["objective"],
                             "mode": prepared.spec["mode"],
                             "condition": prepared.spec["condition"],
                             "participants": [
                                 {"id": p["id"], "provider": p["provider"], "model": p["model"]}
                                 for p in prepared.spec["participants"]],
                             "repetitions": prepared.spec["repetitions"],
                             "prepared_requests": len(prepared.requests_json),
                             "fingerprint": prepared.condition_fingerprint},
                "requires_approval": False}

    @router.get("/plans")
    def list_plans():
        rows = plans.list()
        plans.mark_presented([row["id"] for row in rows])
        return rows

    @router.get("/plans/{plan_id}")
    def read_plan(plan_id: str):
        try:
            detail = plans.get(plan_id)
            plans.mark_presented([detail["id"]])
            return detail
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @router.post("/plans/{plan_id}/execute", status_code=202)
    async def execute_plan(plan_id: str, payload: dict):
        if payload != {}:
            raise HTTPException(422, "Não altere o plano durante sua execução.")
        try:
            plan = plans.get(plan_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

        if plan["status"] != "planned":
            # Repeated requests are idempotent and can never launch twice.
            return {"plan_id": plan_id, "status": plan["status"],
                    "result": plan["result"], "new_execution": False}
        if plan["action"] == "lab.adjustment.request":
            if not live_enabled():
                raise HTTPException(403, "Chamadas reais estão desabilitadas no Lab.")
            detail = incident_detail(plan["incident_id"])
            policy = detail["recovery"]
            if (detail["experiment_id"] != plan["experiment_id"]
                    or policy["action"] != "preview_adjustment"
                    or not policy["allowed"]
                    or detail["observation_id"] != plan["payload"].get("observation_id")):
                raise HTTPException(409, "O estado experimental mudou desde o planejamento.")
            seal = root / "experiments" / plan["experiment_id"] / "integrity.json"
            if not seal.is_file():
                raise HTTPException(409, "Selo original não encontrado.")
            evidence = digest(seal)
        elif plan["action"] == "lab.experiment.start":
            if plan["payload"]["spec"].get("mode") == "live" and not live_enabled():
                raise HTTPException(403, "Chamadas reais estão desabilitadas no Lab.")
            try:
                prepared = runner.prepare(plan["payload"]["spec"])
                evidence = _sha(prepared.spec)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                raise HTTPException(422, settings.redact(str(exc))) from exc
        else:
            raise HTTPException(403, "O Assistant não executa operações destrutivas.")

        try:
            current, fresh = plans.claim(plan_id, evidence_sha256=evidence, automatic=True)
        except EmergencyStop as exc:
            raise HTTPException(423, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if not fresh:
            return {"plan_id": plan_id, "status": current["status"],
                    "result": current["result"], "new_execution": False}
        try:
            if current["action"] == "lab.adjustment.request":
                saved, spec = adjustments.prepare(current["experiment_id"], current["payload"])
                adjustments.start(saved, spec)
                result = {"experiment_id": current["experiment_id"],
                          "incident_id": current["incident_id"],
                          "adjustment_id": saved["id"], "status": "accepted",
                          "independent_sample": False}
                try:
                    incidents.record_action(current["incident_id"],
                                            event="assistant.adjustment_requested",
                                            payload={"adjustment_id": saved["id"]})
                except Exception:
                    logger.exception("Falha ao auditar ajuste %s", saved["id"])
            else:
                result = await start_experiment(current["payload"]["spec"])
            plans.finish(plan_id, result)
            return {"plan_id": plan_id, "status": "accepted",
                    "result": result, "new_execution": True}
        except Exception as exc:
            plans.fail(plan_id, settings.redact(str(exc)))
            raise

    @router.get("/routines")
    def list_routines():
        return automation.list()

    @router.post("/routines")
    def schedule_routine(payload: dict):
        if not isinstance(payload, dict) or set(payload) != {
                "plan_id", "interval_seconds", "first_at"}:
            raise HTTPException(422, "Informe plan_id, interval_seconds e first_at.")
        try:
            plan = plans.get(payload["plan_id"])
            if plan["action"] != "lab.experiment.start" or plan["status"] != "planned":
                raise ValueError("Somente planos de experimento preparados podem ser agendados.")
            routine = automation.schedule(runner, plan["payload"]["spec"],
                                          payload["interval_seconds"], payload["first_at"])
        except FileNotFoundError as exc:
            raise HTTPException(404, "Plano não encontrado.") from exc
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, settings.redact(str(exc))) from exc
        return {"routine": routine, "source_plan_id": plan["id"],
                "planned_before_execution": True}

    @router.get("/routines/{routine_id}/history")
    def routine_history(routine_id: str):
        try:
            return automation.history(routine_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, "Rotina não encontrada.") from exc

    @router.post("/routines/{routine_id}/state")
    def change_routine(routine_id: str, payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"active"}:
            raise HTTPException(422, "Informe active.")
        try:
            return automation.set_active(routine_id, payload["active"])
        except FileNotFoundError as exc:
            raise HTTPException(404, "Rotina não encontrada.") from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @router.get("/automation/recovery")
    def recovery_queue():
        return {"settings": automation.settings(), "queue": automation.queue()}

    @router.put("/automation/recovery/settings")
    def recovery_settings(payload: dict):
        if not isinstance(payload, dict) or set(payload) != {"auto_recovery"}:
            raise HTTPException(422, "Informe auto_recovery.")
        try:
            return automation.set_settings(auto_recovery=payload["auto_recovery"])
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @router.post("/automation/monitor")
    def monitor_now():
        return automation.monitor(incidents)

    async def _tick():
        """Reconcile datasets, stage recovery plans, then run prior scheduled work."""
        summary = {"monitor": automation.monitor(incidents),
                   "recovery_planned": [], "recovery_executed": [],
                   "occurrence": None, "errors": []}
        if plans.control()["stopped"]:
            summary["emergency_stopped"] = True
            return summary

        # Recoveries were prepared on an earlier tick. Never execute a newly
        # created recovery in the same tick as its plan was first persisted.
        previous = automation.queue()
        for item in previous:
            if item["state"] != "planned" or not automation.settings()["auto_recovery"]:
                continue
            try:
                result = await execute_plan(item["plan_id"], {})
                state = "accepted" if result["status"] == "accepted" else "blocked"
                automation.complete_recovery(item["experiment_id"], item["observation_id"],
                                             state=state)
                summary["recovery_executed"].append(
                    {"plan_id": item["plan_id"], "status": state})
            except Exception as exc:
                automation.complete_recovery(item["experiment_id"], item["observation_id"],
                                             state="failed", error=settings.redact(str(exc)))
                summary["errors"].append({"recovery_plan_id": item["plan_id"],
                                          "error": settings.redact(str(exc))})

        existing = {(row["experiment_id"], row["observation_id"])
                    for row in automation.queue()}
        for issue in incidents.all_matching(status="open"):
            if issue["criterion_id"] != "arof.contribution.fully_valid":
                continue
            identity = (issue["experiment_id"], issue["observation_id"])
            if not identity[1] or identity in existing:
                continue
            try:
                detail = incident_detail(issue["id"])
                policy = detail["recovery"]
                if (not policy["allowed"] or policy["action"] != "preview_adjustment"
                        or policy["revalidations"]):
                    continue
                proposed = dict(policy["proposed_payload"])
                saved, _ = adjustments.prepare(identity[0], proposed, persist=False)
                plan = plans.create(
                    action="lab.adjustment.request", experiment_id=identity[0],
                    incident_id=issue["id"], payload=proposed,
                    evidence_sha256=saved["source_integrity_sha256"])
                if automation.queue_recovery(
                        experiment_id=identity[0], observation_id=identity[1],
                        incident_id=issue["id"], plan_id=plan["id"]):
                    summary["recovery_planned"].append(plan["id"])
                    existing.add(identity)
            except Exception as exc:
                summary["errors"].append({"incident_id": issue["id"],
                                          "error": settings.redact(str(exc))})

        occurrence = automation.claim_due()
        if occurrence is None:
            return summary
        plan_id = ""
        try:
            prepared = runner.prepare(occurrence["spec"])
            plan = plans.create(
                action="lab.experiment.start", experiment_id=prepared.spec["experiment_id"],
                payload={"spec": prepared.spec}, evidence_sha256=_sha(prepared.spec))
            plan_id = plan["id"]
            automation.record(occurrence["id"], plan_id=plan_id, status="planned")
            result = await execute_plan(plan_id, {})
            state = "accepted" if result["status"] == "accepted" else "blocked"
            automation.record(occurrence["id"], plan_id=plan_id, status=state, result=result)
            summary["occurrence"] = {"id": occurrence["id"], "routine_id": occurrence["routine_id"],
                                     "plan_id": plan_id, "status": state}
        except Exception as exc:
            automation.record(occurrence["id"], plan_id=plan_id, status="failed",
                              result={"error": settings.redact(str(exc))})
            logger.exception("Falha na ocorrência agendada %s", occurrence["id"])
            summary["occurrence"] = {"id": occurrence["id"], "status": "failed"}
        return summary

    async def tick():
        # Background watcher and manual refresh share a single reconciliation pass.
        async with tick_lock:
            return await _tick()

    @router.post("/automation/tick")
    async def tick_now():
        return await tick()

    router.tick = tick
    router.plan_experiment = plan_experiment
    router.execute_plan = execute_plan
    router.plan_adjustment = plan_adjustment

    return router
