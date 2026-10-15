"""Natural language drafts, sealed comparisons, restart-safe monitoring and schedules."""
import asyncio
import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.assistant_automation import LabAutomation, iso, utc
from norvald_lab.assistant_comparison import compare_experiments
from norvald_lab.assistant_design import parse_spec_reply
from norvald_lab.cli import demo_spec
from norvald_lab.criterion_incidents import CriterionIncidents
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry


class DraftProvider(LLMProvider):
    def __init__(self, spec):
        self.spec, self.requests = spec, []

    async def execute(self, request, model):
        self.requests.append(request)
        return ExecutionResult(content=json.dumps(self.spec), tokens=7, duration_seconds=0,
                               provider="openrouter", model=model)

    async def list_models(self):
        return []


def registry(spec, provider):
    agents = AgentRegistry()
    agents.register_provider("operator", provider, kind="openrouter")
    agents.register_agent("lab-assistant", "operator", spec["participants"][0]["model"])
    return agents


def test_parser_only_accepts_json_object():
    assert parse_spec_reply(' ```json\n{"a": 1}\n``` ') == {"a": 1}
    with pytest.raises(ValueError, match="objeto"):
        parse_spec_reply("[]")
    with pytest.raises(ValueError, match="JSON"):
        parse_spec_reply("O experimento já foi iniciado.")


def test_language_draft_is_never_execution(tmp_path, monkeypatch):
    spec = demo_spec("draft-from-language")
    provider = DraftProvider(spec)
    monkeypatch.setattr("norvald_lab.assistant_design.build_registry",
                        lambda draft, **kwargs: registry(draft, provider))
    with TestClient(create_app(tmp_path, allow_live=True, enable_demo=True)) as client:
        client.put("/api/assistant/settings", json={
            "kind": "openrouter", "model": "planner-operator"})
        result = client.post("/api/assistant/spec/draft", json={
            "goal": "Monte um experimento B1 com três participantes."})
        assert result.status_code == 200, result.text
        assert result.json()["ready"] is True
        assert result.json()["draft"]["experiment_id"] == "draft-from-language"
        assert len(provider.requests) == 1
        assert not provider.requests[0].allow_tools
        assert not (tmp_path / "experiments").exists()
        assert client.post("/api/assistant/spec/draft", json={
            "goal": "não execute", "command": "run"}).status_code == 422


@pytest.mark.asyncio
async def test_verified_comparison_and_unpaired_blocks(tmp_path):
    runner = ExperimentRunner(tmp_path)
    for name in ("comparison-first", "comparison-second"):
        await runner.run(runner.prepare(demo_spec(name)), monitor_capacity=False)
    result = compare_experiments(tmp_path, "comparison-first", "comparison-second")
    assert result["schema_version"] == "norvald.lab.comparison.v1"
    assert result["comparability"]["structurally_aligned"]
    assert len(result["pairs"]) == 3
    assert result["differences"]["responses"] == 0
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        response = client.get("/api/assistant/compare", params={
            "left": "comparison-first", "right": "comparison-second"})
        assert response.status_code == 200
        assert len(response.json()["pairs"]) == 3
        assert client.get("/api/assistant/compare", params={
            "left": "comparison-first", "right": "comparison-first"}).status_code == 409

    raw = next((tmp_path / "experiments" / "comparison-second" / "raw").rglob("*.jsonl"))
    raw.write_text(raw.read_text().replace("option", "edited"))
    with pytest.raises(ValueError, match="íntegro"):
        compare_experiments(tmp_path, "comparison-first", "comparison-second")


@pytest.mark.asyncio
async def test_monitor_restores_tracking_for_cli_experiments(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec("from-cli")), monitor_capacity=False)
    monitor = LabAutomation(tmp_path)
    incidents = CriterionIncidents(tmp_path)
    first = monitor.monitor(incidents)
    assert len(first["observed"]) == 1
    assert first["errors"] == []
    second = LabAutomation(tmp_path).monitor(incidents)
    assert not second["observed"]
    assert second["skipped"] == 1
    assert verify_experiment(tmp_path, "from-cli")["valid"]


def test_persistent_routine_plan_and_state(tmp_path):
    automation = LabAutomation(tmp_path)
    runner = ExperimentRunner(tmp_path)
    with pytest.raises(ValueError, match="futura"):
        automation.schedule(runner, demo_spec("loop-plan"), 20,
                            iso(utc() - timedelta(hours=1)))
    first = iso(utc() + timedelta(minutes=1))
    routine = automation.schedule(runner, demo_spec("loop-plan"), 30, first)
    assert routine["active"] == 1
    assert LabAutomation(tmp_path).get(routine["id"])["next_due"] == first
    assert automation.claim_due(now=utc()) is None
    occurrence = automation.claim_due(now=utc() + timedelta(minutes=2))
    assert occurrence["routine_id"] == routine["id"]
    assert occurrence["experiment_id"] != "loop-plan"
    assert occurrence["spec"]["experiment_id"] == occurrence["experiment_id"]
    assert len(automation.history(routine["id"])) == 1
    assert automation.set_active(routine["id"], False)["active"] == 0
    assert automation.claim_due(now=utc() + timedelta(days=1)) is None


def test_scheduled_routine_uses_presented_plan_and_emergency(tmp_path):
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        spec = demo_spec("schedule-first")
        planned = client.post("/api/assistant/plans/experiment",
                              json={"spec": spec}).json()
        assert planned["plan"]["status"] == "planned"
        first_at = iso(utc() + timedelta(seconds=1))
        saved = client.post("/api/assistant/routines", json={
            "plan_id": planned["plan"]["id"],
            "interval_seconds": 3600, "first_at": first_at})
        assert saved.status_code == 200, saved.text
        routine_id = saved.json()["routine"]["id"]
        assert saved.json()["planned_before_execution"]
        assert client.get("/api/assistant/routines").json()[0]["id"] == routine_id
        assert client.post("/api/assistant/emergency/stop", json={}).status_code == 200
        client.portal.call(asyncio.sleep, 1.1)
        blocked = client.post("/api/assistant/automation/tick", json={}).json()
        assert blocked["emergency_stopped"]
        assert client.get("/api/assistant/routines/" + routine_id + "/history").json() == []
        client.post("/api/assistant/emergency/resume", json={})
        fired = client.post("/api/assistant/automation/tick", json={})
        assert fired.status_code == 200, fired.text
        assert fired.json()["occurrence"]["status"] == "accepted"
        history = client.get("/api/assistant/routines/" + routine_id + "/history").json()
        assert len(history) == 1 and history[0]["plan_id"].startswith("plan-")
        expid = history[0]["experiment_id"]
        async def settle():
            await asyncio.gather(*list(client.app.state.jobs.values()))
        client.portal.call(settle)
        assert verify_experiment(tmp_path, expid)["valid"]
        assert client.post("/api/assistant/routines/" + routine_id + "/state",
                           json={"active": False}).json()["active"] == 0
