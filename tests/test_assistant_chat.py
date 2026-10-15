"""Unified chat threads, screen references, plan cards and isolated owner actions."""
import asyncio

from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec
from norvald_lab.storage import verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry


class Operator(LLMProvider):
    def __init__(self, spec):
        self.spec = spec
        self.requests = []

    async def execute(self, request, model):
        self.requests.append(request)
        if request.user_message == "planeje" and not request.tool_exchanges:
            return ExecutionResult(
                content="", tokens=3, duration_seconds=0, provider="openrouter", model=model,
                tool_calls=[ToolCall(call_id="plan-1", name="call_operation",
                                     arguments={"name": "lab.experiment.plan",
                                                "input": {"spec": self.spec}})])
        if request.tool_exchanges:
            assert request.tool_exchanges[-1].results[0].is_error is False
        return ExecutionResult(content="Operação preparada. Consulte o plano abaixo.",
                               tokens=7, duration_seconds=0,
                               provider="openrouter", model=model)

    async def list_models(self):
        return []


def registry(spec, provider):
    agents = AgentRegistry()
    agents.register_provider("operator", provider, kind="openrouter")
    agents.register_agent("lab-assistant", "operator", spec["participants"][0]["model"])
    return agents


def test_independent_conversations_context_and_plan_events(tmp_path, monkeypatch):
    spec = demo_spec("threaded-experiment")
    operator = Operator(spec)
    monkeypatch.setattr("norvald_lab.lab_assistant.build_registry",
                        lambda payload, **kw: registry(payload, operator))
    with TestClient(create_app(tmp_path, allow_live=True, enable_demo=True)) as client:
        client.put("/api/assistant/settings", json={"kind": "openrouter",
                                                   "model": "operator-local"})
        t1 = client.post("/api/assistant/threads", json={})
        t2 = client.post("/api/assistant/threads", json={"title": "Outra análise"})
        assert t1.status_code == 201 and t2.status_code == 201
        first, second = t1.json()["id"], t2.json()["id"]
        assert first != second
        assert len(client.get("/api/assistant/threads").json()) == 2

        malformed = client.post("/api/assistant/threads/" + first + "/send",
                                json={"text": "planeje", "context": {"file_path": "../secrets"}})
        assert malformed.status_code == 422
        assert client.post("/api/assistant/threads/" + first + "/send",
                           json={"text": "planeje", "context": {"view": "observe"}},
                           headers={"Origin": "https://untrusted.invalid"}).status_code == 403

        planned = client.post("/api/assistant/threads/" + first + "/send", json={
            "text": "planeje", "context": {"view": "observe", "experiment_id": "threaded-experiment"}})
        assert planned.status_code == 200, planned.text
        data = planned.json()
        assert data["thread"]["title"] == "planeje"
        assert len(data["messages"]) == 2
        assert len(data["events"]) == 1
        event = data["events"][0]
        assert event["message_seq"] == data["messages"][-1]["seq"]
        assert event["operation"] == "lab.experiment.plan"
        assert event["status"] == "ok"
        plan_id = event["payload"]["plan_id"]
        assert plan_id.startswith("plan-")
        assert not client.app.state.assistant_plans.was_presented(plan_id)
        assert not (tmp_path / "experiments").exists()

        second_chat = client.post("/api/assistant/threads/" + second + "/send", json={
            "text": "explique os critérios", "context": {"view": "assistant"}})
        assert second_chat.status_code == 200
        assert len(second_chat.json()["messages"]) == 2
        assert second_chat.json()["events"] == []
        assert "threaded-experiment" in operator.requests[0].context.working_context
        assert "lab.general" in operator.requests[-1].context.working_context

        after_restart = client.get("/api/assistant/threads/" + first).json()
        assert len(after_restart["messages"]) == 2
        assert len(after_restart["events"]) == 1
        assert client.get("/api/assistant/threads/" + "chat-invalid").status_code == 404

        assert client.get("/api/assistant/plans/" + plan_id).status_code == 200
        assert client.app.state.assistant_plans.was_presented(plan_id) is False
        assert client.post("/api/assistant/plans/" + plan_id + "/present", json={}).status_code == 200
        executed = client.post("/api/assistant/threads/" + first + "/plans/" + plan_id
                               + "/execute", json={})
        assert executed.status_code == 202, executed.text
        assert executed.json()["new_execution"] is True
        repeat = client.post("/api/assistant/threads/" + first + "/plans/" + plan_id
                             + "/execute", json={})
        assert repeat.status_code == 202 and repeat.json()["new_execution"] is False
        async def settle():
            await asyncio.gather(*list(client.app.state.jobs.values()))
        client.portal.call(settle)
        assert verify_experiment(tmp_path, "threaded-experiment")["valid"]
        actions = client.get("/api/assistant/threads/" + first).json()["events"]
        assert len([item for item in actions if item["operation"] == "lab.plan.execute"]) == 2
        assert actions[-1]["payload"]["new_execution"] is False

    with TestClient(create_app(tmp_path, allow_live=True, enable_demo=True)) as reopened:
        restored = reopened.get("/api/assistant/threads/" + first).json()
        assert len(restored["messages"]) == 2
        assert restored["events"][0]["payload"]["plan_id"] == plan_id
        assert len(reopened.get("/api/assistant/threads").json()) == 2


def test_thread_specific_destructive_confirmation(tmp_path):
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        spec = demo_spec("thread-exclusion")
        assert client.post("/api/experiments", json=spec).status_code == 202
        async def settle():
            await asyncio.gather(*list(client.app.state.jobs.values()))
        client.portal.call(settle)
        originals = {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*") if p.is_file()}
        thread_id = client.post("/api/assistant/threads", json={}).json()["id"]
        staged = client.post("/api/assistant/destructive/exclusion/plan",
                             json={"experiment_id": "thread-exclusion"}).json()
        request_id = staged["request"]["id"]
        route = "/api/assistant/threads/" + thread_id + "/destructive/" + request_id + "/confirm"
        assert client.post(route, json={"experiment_id": "thread-exclusion",
                                       "confirmed": False}).status_code == 409
        assert client.post(route, json={"experiment_id": "thread-exclusion",
                                       "confirmed": True}).status_code == 200
        assert client.post(route, json={"experiment_id": "thread-exclusion",
                                       "confirmed": True}).status_code == 409
        events = client.get("/api/assistant/threads/" + thread_id).json()["events"]
        assert events[-1]["operation"] == "lab.destructive.exclusion.confirm"
        assert originals == {str(p): p.read_bytes() for p in (tmp_path / "experiments").rglob("*") if p.is_file()}
