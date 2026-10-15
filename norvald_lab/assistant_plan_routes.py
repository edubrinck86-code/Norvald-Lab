"""Staged non-destructive Lab Assistant operations, with plans shown first."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from norvald_lab.assistant_plans import AssistantPlans, EmergencyStop, _sha
from norvald_lab.storage import digest


def plan_router(root: Path, runner, adjustments, incidents, settings, incident_detail,
                start_experiment, live_enabled, logger, plans: AssistantPlans):
    router = APIRouter(prefix="/api/assistant")

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

    @router.get("/plans/{plan_id}")
    def read_plan(plan_id: str):
        try:
            return plans.get(plan_id)
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

    return router
