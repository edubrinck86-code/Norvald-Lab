import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from norvald_lab.api import create_app
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.config import validate_spec
from norvald_lab.runner import ExperimentRunner
from norvald_lab.runtime import DemoProvider, build_registry, corpus_runtime
from norvald_lab.storage import read_verified_records, verify_experiment
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry
from norvald_lab.vendor.norvald_execution.providers.openai_compatible_provider import OpenAICompatibleProvider


def raw(root, expid):
    return [r.payload for r in read_verified_records(root, expid)]


@pytest.mark.asyncio
async def test_independent_blind_self_and_peer_with_repetition_pairing(tmp_path):
    runner = ExperimentRunner(tmp_path)
    spec = demo_spec("b1")
    spec["repetitions"] = 2
    original = copy.deepcopy(spec)
    prepared = runner.prepare(spec)
    spec["task"]["objective"] = "MODIFICADO DEPOIS"
    assert not tmp_path.joinpath("experiments").exists()  # prepare é puro
    result = await runner.run(prepared, monitor_capacity=False)
    assert result["status"] == "complete" and result["executed"] == 6
    assert prepared.spec["task"] == original["task"]
    baseline = raw(tmp_path, "b1")
    by_id = {r["observation_id"]: r for r in baseline}
    assert len({r["logical_execution_id"] for r in baseline}) == 6
    assert all(not r["request"]["studio_metadata"]["source_observation_ids"] for r in baseline)
    for exposure, expid in (("self", "b3"), ("exposed", "e")):
        spec2 = derive_spec(tmp_path, "b1", expid, exposure)
        prepared2 = runner.prepare(spec2)
        requests = [json.loads(r) for r in prepared2.requests_json]
        if exposure == "exposed":
            for repetition in (1, 2):
                same_wave = [r["context"]["working_context"] for r in requests if r["context"]["metadata"]["repetition_index"] == repetition]
                assert len(set(same_wave)) == 1  # IDs e conteúdo idênticos na leva
        await runner.run(prepared2, monitor_capacity=False)
        for record in raw(tmp_path, expid):
            meta = record["request"]["studio_metadata"]
            assert len(meta["source_observation_ids"]) == (1 if exposure == "self" else 3)
            for observation_id in meta["source_observation_ids"]:
                origin = by_id[observation_id]
                assert origin["request"]["studio_metadata"]["repetition_index"] == meta["repetition_index"]
                if exposure == "self":
                    assert origin["participant_id"] == record["participant_id"]
    assert verify_experiment(tmp_path, "b1")["valid"]
    assert json.loads((tmp_path / "experiments/b1/spec.json").read_text())["task"] == original["task"]
    b3req = json.loads((tmp_path / "experiments/b3/requests.json").read_text())
    ereq = json.loads((tmp_path / "experiments/e/requests.json").read_text())
    for a, b in zip(b3req, ereq):
        assert a["instructions"] == b["instructions"]
        assert a["shared_instructions"] == b["shared_instructions"]
        assert a["user_message"] == b["user_message"]


@pytest.mark.asyncio
async def test_refuses_reused_id_and_tampered_origin(tmp_path):
    runner = ExperimentRunner(tmp_path)
    prepared = runner.prepare(demo_spec("b1"))
    await runner.run(prepared, monitor_capacity=False)
    with pytest.raises(FileExistsError):
        await runner.run(prepared, monitor_capacity=False)
    target = next((tmp_path / "experiments/b1/raw").rglob("*.jsonl"))
    target.write_text(target.read_text().replace("Escolha simulada", "ALTERADO"))
    assert not verify_experiment(tmp_path, "b1")["valid"]
    with pytest.raises(ValueError, match="íntegra"):
        derive_spec(tmp_path, "b1", "e", "exposed")


@pytest.mark.asyncio
async def test_changed_corpus_rejected_before_new_calls(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(demo_spec("b1")), monitor_capacity=False)
    derived = derive_spec(tmp_path, "b1", "e", "exposed")
    derived["documents"][0]["text"] = "Outro documento"
    with pytest.raises(ValueError, match="diferem"):
        runner.prepare(derived)
    assert not (tmp_path / "experiments/e").exists()


class TrackingProvider(DemoProvider):
    def __init__(self, fail=None):
        self.active = 0
        self.peak = 0
        self.seen = []
        self.fail = fail
    async def execute(self, request, model):
        self.active += 1
        self.peak = max(self.peak, self.active)
        self.seen.append(request)
        try:
            await asyncio.sleep(0.01)
            if request.agent_id == self.fail:
                raise ValueError("falha controlada")
            result = await super().execute(request, model)
            result.reasoning = "trace observado"
            return result
        finally:
            self.active -= 1


def registry_for(spec, provider):
    registry = AgentRegistry()
    for name in spec["providers"]:
        registry.register_provider(name, provider, kind=spec["providers"][name]["kind"])
    for p in spec["participants"]:
        registry.register_agent(p["id"], p["provider"], p["model"])
    return registry


@pytest.mark.asyncio
async def test_concurrency_frozen_requests_failure_and_reasoning_capture(tmp_path):
    spec = demo_spec("falha")
    spec["budget"] = {"max_concurrency": 3, "max_concurrency_per_provider": 1}
    provider = TrackingProvider(fail="analista-2")
    runner = ExperimentRunner(tmp_path)
    result = await runner.run(runner.prepare(spec), registry=registry_for(spec, provider), monitor_capacity=False)
    assert provider.peak == 1
    assert result["failures"] == 1 and result["status"] == "incomplete"
    assert verify_experiment(tmp_path, "falha")["valid"]
    assert len({req.context.working_context for req in provider.seen}) == 1
    paths = list((tmp_path / "experiments/falha/raw").rglob("*.jsonl"))
    records = [json.loads(line) for path in paths for line in path.read_text().splitlines()]
    assert len(records) == 3
    assert sum(r["error"] is not None for r in records) == 1
    assert all(r["result"]["reasoning"] == "trace observado" for r in records if r["result"])
    csv = (tmp_path / "experiments/falha/outcomes.csv").read_text()
    assert "failed" in csv


@pytest.mark.asyncio
async def test_cancellation_leaves_aborted_audit(tmp_path):
    started = asyncio.Event()
    class Slow(DemoProvider):
        async def execute(self, request, model):
            started.set()
            await asyncio.Event().wait()
    spec = demo_spec("cancelado")
    runner = ExperimentRunner(tmp_path)
    task = asyncio.create_task(runner.run(runner.prepare(spec), registry=registry_for(spec, Slow()), monitor_capacity=False))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    check = verify_experiment(tmp_path, "cancelado")
    assert check["valid"] and check["status"] == "aborted"


@pytest.mark.asyncio
async def test_real_adapter_payload_and_capture_without_external_network(tmp_path, monkeypatch):
    spec = demo_spec("adapter")
    spec["mode"] = "live"
    spec["providers"] = {"simulador": {"kind": "openrouter", "credential_env": "LAB_TEST_KEY", "base_url": "https://example.invalid/v1"}}
    for p in spec["participants"]:
        p["reasoning_effort"] = "high"
        p["sampling"] = {"max_tokens": 128}
    monkeypatch.setenv("LAB_TEST_KEY", "SECRET-TEST-NOT-FOR-DATASET")
    payloads = []
    def handler(request):
        payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "req-test", "choices": [{"message": {"content": "resposta observada", "reasoning_content": "trace exposto"}}], "usage": {"prompt_tokens": 12, "completion_tokens": 3}})
    provider = OpenAICompatibleProvider("https://example.invalid/v1", "SECRET-TEST-NOT-FOR-DATASET", provider_label="openrouter")
    await provider._client.aclose()
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False)
    try:
        runner = ExperimentRunner(tmp_path)
        result = await runner.run(runner.prepare(spec), registry=registry_for(spec, provider), allow_live=True, monitor_capacity=False)
        assert result["status"] == "complete"
        assert len(payloads) == 3
        assert all(p["reasoning"]["effort"] == "high" for p in payloads)
        assert all(r["result"]["reasoning"] == "trace exposto" for r in raw(tmp_path, "adapter"))
        assert all(r["result"]["input_tokens"] == 12 for r in raw(tmp_path, "adapter"))
        assert all("SECRET-TEST-NOT-FOR-DATASET" not in p.read_text() for p in tmp_path.rglob("*") if p.is_file())
    finally:
        await provider._client.aclose()


@pytest.mark.asyncio
async def test_tool_loop_is_reused_and_audited(tmp_path):
    class ToolProvider(DemoProvider):
        SUPPORTS_TOOL_USE = True
        async def execute(self, request, model):
            if not request.tool_exchanges:
                return ExecutionResult(content="", tokens=0, duration_seconds=0, provider="demo", model=model, tool_calls=[ToolCall("read-1", "read_document", {"document_id": "texto-demo"})])
            assert "Material fictício" in request.tool_exchanges[0].results[0].content
            return await super().execute(request, model)
    spec = demo_spec("tools")
    spec["condition"].update(tools="corpus", max_tool_calls=2, max_tool_iterations=3)
    runner = ExperimentRunner(tmp_path)
    result = await runner.run(runner.prepare(spec), registry=registry_for(spec, ToolProvider()), monitor_capacity=False)
    assert result["status"] == "complete", str(result["executions"])
    assert len(raw(tmp_path, "tools")) == 3  # followups não contam como novos agentes
    assert all(r["result"]["metadata"]["tool_calls"] for r in raw(tmp_path, "tools"))


@pytest.mark.parametrize("mutation", [
    lambda s: s.update(experiment_id="../escape"),
    lambda s: s["participants"].append(copy.deepcopy(s["participants"][0])),
    lambda s: s["condition"].update(exposure="exposed"),
    lambda s: s["participants"][0].update(sampling={"temperature": float("nan")}),
    lambda s: s["providers"]["simulador"].update(api_key="segredo"),
    lambda s: s.update(mode="live"),
    lambda s: s["providers"]["simulador"].update(base_url="https://user:password@example.invalid"),
])
def test_invalid_configuration_rejected(mutation):
    spec = demo_spec("invalid")
    mutation(spec)
    with pytest.raises(ValueError):
        validate_spec(spec)


def test_studio_data_path_is_not_inherited(tmp_path, monkeypatch):
    monkeypatch.setenv("NORVALD_DATA_DIR", str(tmp_path / "studio"))
    monkeypatch.setenv("NORVALD_LAB_DATA_DIR", str(tmp_path / "lab"))
    assert ExperimentRunner().root == tmp_path / "lab"


def test_api_runs_and_reads_without_studio(tmp_path):
    with TestClient(create_app(tmp_path, enable_demo=True)) as client:
        assert client.get("/health").json()["studio_required"] is False
        accepted = client.post("/api/experiments", json=demo_spec("api-demo"))
        assert accepted.status_code == 202
        # Aguarda o trabalho no loop real da aplicação, sem esperar rede externa.
        async def settle():
            tasks = list(client.app.state.jobs.values())
            await asyncio.gather(*tasks)
        client.portal.call(settle)
        assert client.get("/api/experiments/api-demo").json()["status"] == "complete"
        assert client.get("/api/experiments/api-demo/verify").json()["valid"]
        assert len(client.get("/api/experiments/api-demo/raw").json()) == 3
        assert client.post("/api/experiments", json=demo_spec("api-demo")).status_code == 409
        live = demo_spec("api-live")
        live["mode"] = "live"
        live["providers"] = {"simulador": {"kind": "openai", "credential_env": "UNSET_LAB_TEST"}}
        assert client.post("/api/experiments", json=live).status_code == 403


def test_no_import_of_studio_application_or_unversioned_src():
    import ast
    root = Path(__file__).parents[1] / "norvald_lab"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            assert not any(n == "backend" or n.startswith("backend.") or n.startswith("src.") for n in names), path
