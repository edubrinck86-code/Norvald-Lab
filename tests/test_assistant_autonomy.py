"""Operator tool plans, general chat, and opt-in autonomous recoveries."""
import asyncio

import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry


class Stub(LLMProvider):
    def __init__(self, text):
        self.text, self.requests = text, []

    async def execute(self, request, model):
        self.requests.append(request)
        return ExecutionResult(content=self.text, tokens=3, duration_seconds=0,
                               provider="openrouter", model=model)

    async def list_models(self):
        return []


def registry(spec, provider, name="operator"):
    instance = AgentRegistry()
    instance.register_provider(name, provider, kind="openrouter")
    for member in spec["participants"]:
        instance.register_agent(member["id"], name, member["model"])
    return instance


def test_general_chat_can_create_staged_plan_but_never_execute(tmp_path, monkeypatch):
    spec = demo_spec("planned-by-agent")

    class PlanningProvider(Stub):
        async def execute(self, request, model):
            self.requests.append(request)
            if not request.tool_exchanges:
                return ExecutionResult(content="", tokens=1, duration_seconds=0,
                                       provider="openrouter", model=model,
                                       tool_calls=[ToolCall(call_id="plan-tool",
                                           name="call_operation", arguments={
                                               "name": "lab.experiment.plan",
                                               "input": {"spec": spec}})])
            assert request.tool_exchanges[0].results[0].is_error is False
            assert '"status": "planned"' in request.tool_exchanges[0].results[0].content
            return ExecutionResult(content="Plano preparado e disponível no painel.",
                                   tokens=3, duration_seconds=0,
                                   provider="openrouter", model=model)

    provider = PlanningProvider("")
    monkeypatch.setattr("norvald_lab.lab_assistant.build_registry",
                        lambda operator_spec, **kw: registry(operator_spec, provider))
    with TestClient(create_app(tmp_path, allow_live=True, enable_demo=True)) as client:
        client.put("/api/assistant/settings", json={
            "kind": "openrouter", "model": "assistant-operator"})
        response = client.post("/api/assistant/chat", json={
            "text": "Planeje este experimento, mas mostre antes de executar."})
        assert response.status_code == 200, response.text
        assert len(response.json()["messages"]) == 2
        assert len(provider.requests) == 2
        assert client.get("/api/assistant/conversation").json()["messages"] == response.json()["messages"]
        plans = client.get("/api/assistant/plans").json()
        assert len(plans) == 1
        assert plans[0]["status"] == "planned"
        assert plans[0]["payload"]["spec"]["experiment_id"] == "planned-by-agent"
        assert not (tmp_path / "experiments").exists()


@pytest.mark.asyncio
async def test_recovery_is_staged_by_default_then_opt_in_executed_once(tmp_path, monkeypatch):
    spec = demo_spec("recover-live")
    spec["mode"] = "live"
    spec["providers"] = {"router": {"kind": "openrouter"}}
    for participant in spec["participants"]:
        participant.update(provider="router", model="participant-test")

    raw_provider = Stub("Resposta sem um bloco CONTRIBUTION válido.")
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(spec),
                     registry=registry(spec, raw_provider, name="router"),
                     allow_live=True, monitor_capacity=False)
    assert verify_experiment(tmp_path, "recover-live")["valid"]
    originals = {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
                 if p.is_file()}

    followup = Stub("Sem contribuição corrigida, resultado de ajuste separado.")
    monkeypatch.setattr("norvald_lab.adjustments.build_registry",
                        lambda operation_spec, **kw: registry(operation_spec, followup, name="router"))
    with TestClient(create_app(tmp_path, allow_live=True)) as client:
        client.post("/api/experiments/recover-live/criteria/reconcile")
        report = client.post("/api/assistant/automation/tick", json={})
        assert report.status_code == 200, report.text
        first = report.json()
        assert len(first["recovery_planned"]) == 3
        assert first["recovery_executed"] == []
        queue = client.get("/api/assistant/automation/recovery").json()
        assert queue["settings"]["auto_recovery"] is False
        assert len(queue["queue"]) == 3
        assert all(row["state"] == "planned" for row in queue["queue"])
        assert followup.requests == []
        assert originals == {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
                             if p.is_file()}
        assert client.put("/api/assistant/automation/recovery/settings", json={
            "auto_recovery": True}).status_code == 200
        second = client.post("/api/assistant/automation/tick", json={})
        assert second.status_code == 200, second.text
        assert len(second.json()["recovery_executed"]) == 3
        async def settle():
            await asyncio.gather(*list(client.app.state.adjustment_jobs.values()))
        client.portal.call(settle)
        assert len(followup.requests) == 3
        third = client.post("/api/assistant/automation/tick", json={})
        assert third.status_code == 200
        assert third.json()["recovery_planned"] == []
        assert third.json()["recovery_executed"] == []
        assert len(followup.requests) == 3
        assert all(x["state"] == "accepted" for x in
                   client.get("/api/assistant/automation/recovery").json()["queue"])
    assert verify_experiment(tmp_path, "recover-live")["valid"]
    assert originals == {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*")
                         if p.is_file()}
