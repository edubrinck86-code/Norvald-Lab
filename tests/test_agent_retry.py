"""Uma nova tentativa por participante (piloto-mmlu-1, 11/11/2026).

No piloto, 8 de 140 respostas não trouxeram opção aceita; B1 incompleto bloqueia
B3, EP e E da pergunta. `budget.max_agent_attempts` (padrão 1) permite repetir a
chamada idêntica uma vez; cada tentativa é uma observação própria.
"""
import asyncio
import copy
import csv
import hashlib
import json
import re

import pytest

from norvald_lab.application.arof.outcome_extract import latest_attempt_rows, rows_from_raw
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.config import validate_spec
from norvald_lab.herd.specs import blind_spec
from norvald_lab.observer import snapshot
from norvald_lab.runner import ExperimentRunner
from norvald_lab.runtime import DemoProvider
from norvald_lab.storage import read_verified_records, verify_experiment
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# Calculados ANTES da mudança (11/11/2026), sobre demo_spec("h1") sem o campo novo, com os UUIDs
# trocados por <uuid> e sem created_at no manifesto.
ANTES = {
    "fingerprint": "e9de146620559f4715bc8d3d216d82dbee2829572d6d9350b68960872e536595",
    "snapshot": "8b8d751a4540e671730c775d537534d632f2f9952c04742c137bb6b883161bcb",
    "requests": "43796f8f8acda07e801db877f9fdd16449c7d1bbe94344f5b891593923d1998e",
    "manifest": "28550e0c7e7b9aed902cdf47bc1a1e9e66354af9bc235cbdbf5212c1ed2547ac",
}
VICTIM = "analista-2"


class FlakyProvider(DemoProvider):
    """Falha (ou devolve lixo) nas primeiras `bad` chamadas de um participante; depois responde normal."""

    def __init__(self, *, bad=1, mode="raise"):
        self.bad = bad
        self.mode = mode
        self.calls = {}
        self.requests = []

    async def execute(self, request, model):
        count = self.calls[request.agent_id] = self.calls.get(request.agent_id, 0) + 1
        self.requests.append(request)
        result = await super().execute(request, model)
        if request.agent_id == VICTIM and count <= self.bad:
            if self.mode == "raise":
                raise ValueError("falha controlada")
            result.content = "Pensei muito e não declarei nada."  # sem bloco CONTRIBUTION
        elif request.agent_id == VICTIM:
            result.content = result.content.replace("Escolha simulada", "SEGUNDA-TENTATIVA")
        return result


def registry_for(spec, provider):
    registry = AgentRegistry()
    for name in spec["providers"]:
        registry.register_provider(name, provider, kind=spec["providers"][name]["kind"])
    for p in spec["participants"]:
        registry.register_agent(p["id"], p["provider"], p["model"])
    return registry


def spec_with(expid, attempts):
    spec = demo_spec(expid)
    if attempts is not None:
        spec["budget"] = {"max_agent_attempts": attempts}
    return spec


async def collect(tmp_path, expid, provider, attempts=2, monitor=False):
    spec = spec_with(expid, attempts)
    runner = ExperimentRunner(tmp_path)
    result = await runner.run(runner.prepare(spec), registry=registry_for(spec, provider), monitor_capacity=monitor)
    return runner, result


def raws(tmp_path, expid):
    paths = sorted((tmp_path / "experiments" / expid / "raw").rglob("*.jsonl"))
    return [json.loads(line) for p in paths for line in p.read_text().splitlines()]


@pytest.mark.asyncio
async def test_error_on_first_attempt_is_retried_and_experiment_completes(tmp_path):
    provider = FlakyProvider(bad=1)
    runner, result = await collect(tmp_path, "b1", provider, monitor=True)
    assert result["status"] == "complete" and result["failures"] == 0 and result["executed"] == 3
    records = raws(tmp_path, "b1")
    victim = sorted((r["attempt_index"], r["error"] is not None) for r in records if r["participant_id"] == VICTIM)
    assert victim == [(1, True), (2, False)]
    assert sorted(r["attempt_index"] for r in records if r["participant_id"] != VICTIM) == [1, 1]
    # a chamada repetida é idêntica à primeira
    first, second = [r for r in provider.requests if r.agent_id == VICTIM]
    assert first == second
    assert verify_experiment(tmp_path, "b1")["valid"]
    manifest = json.loads((tmp_path / "experiments/b1/manifest.json").read_text())
    assert manifest["metadata"]["agent_attempts_per_execution"] == 2
    assert manifest["budget"]["max_attempts"] == 6 and manifest["budget"]["planned_logical_executions"] == 3
    capacity = result["capacity"]
    assert (capacity["logical_executions"], capacity["attempts"], capacity["failures"]) == (3, 4, 1)
    # outcomes.csv: uma linha por tentativa, com attempt_index; a falha da 1ª fica medível
    rows = list(csv.DictReader((tmp_path / "experiments/b1/outcomes.csv").open(encoding="utf-8")))
    assert sorted((r["participant_id"], r["attempt_index"], r["status"]) for r in rows if r["participant_id"] == VICTIM) == [(VICTIM, "1", "failed"), (VICTIM, "2", "ok")]
    paths = sorted((tmp_path / "experiments/b1/raw").rglob("*.jsonl"))
    latest = latest_attempt_rows(rows_from_raw(paths, experiment_id="b1", all_attempts=True))
    assert len(latest) == 3 and all(r.status == "ok" for r in latest)
    assert len(rows_from_raw(paths, experiment_id="b1")) == 3  # padrão antigo: só a última
    # a bancada e os critérios leem a última tentativa de cada participante
    state = snapshot(tmp_path, "b1", "complete")
    assert len(state["contribution_checks"]) == 3 and len(state["contribution_checks_all"]) == 4
    assert all(c["usable"] for c in state["contribution_checks"])
    # a condição derivada não é bloqueada
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "b3", "self"))
    assert len(prepared.requests_json) == 3


@pytest.mark.asyncio
async def test_answer_without_valid_option_is_retried_and_source_loading_uses_attempt_two(tmp_path):
    provider = FlakyProvider(bad=1, mode="garbage")
    runner, result = await collect(tmp_path, "b1", provider)
    assert result["status"] == "complete"
    victim = sorted(r["attempt_index"] for r in raws(tmp_path, "b1") if r["participant_id"] == VICTIM)
    assert victim == [1, 2]
    state = snapshot(tmp_path, "b1", "complete")
    codes = {(c["participant_id"], c["attempt_index"]): c["code"] for c in state["contribution_checks_all"]}
    assert codes[(VICTIM, 1)] == "missing_block" and codes[(VICTIM, 2)] == "usable"
    # B3 do participante enxerga a contribuição da tentativa 2 e nada da 1
    prepared = runner.prepare(derive_spec(tmp_path, "b1", "b3", "self"))
    request = next(json.loads(r) for r in prepared.requests_json if json.loads(r)["agent_id"] == VICTIM)
    assert "SEGUNDA-TENTATIVA" in request["wave_instructions"]
    assert "Pensei muito" not in json.dumps(request)


@pytest.mark.asyncio
async def test_two_failures_with_two_attempts_leave_experiment_incomplete_and_block_derived(tmp_path):
    provider = FlakyProvider(bad=2)
    runner, result = await collect(tmp_path, "b1", provider)
    assert result["status"] == "incomplete" and result["failures"] == 1 and result["executed"] == 3
    assert sum(1 for r in raws(tmp_path, "b1") if r["participant_id"] == VICTIM) == 2
    assert provider.calls[VICTIM] == 2  # no máximo duas, nunca uma terceira
    with pytest.raises(ValueError):
        derive_spec(tmp_path, "b1", "b3", "self")


@pytest.mark.asyncio
async def test_default_does_not_retry(tmp_path):
    provider = FlakyProvider(bad=1)
    _, result = await collect(tmp_path, "b1", provider, attempts=None)
    assert result["status"] == "incomplete" and provider.calls[VICTIM] == 1
    assert [r["attempt_index"] for r in raws(tmp_path, "b1")] == [1, 1, 1]


@pytest.mark.asyncio
async def test_default_spec_generates_the_same_requests_and_manifest_as_before(tmp_path):
    runner = ExperimentRunner(tmp_path)
    prepared = runner.prepare(demo_spec("h1"))
    assert "max_agent_attempts" not in prepared.spec.get("budget", {})
    requests = []
    for raw in prepared.requests_json:
        request = json.loads(raw)
        requests.append(json.dumps(request, sort_keys=True))
    digest = lambda text: hashlib.sha256(UUID.sub("<uuid>", text).encode()).hexdigest()
    assert prepared.condition_fingerprint == ANTES["fingerprint"]
    assert digest(prepared.snapshot_json) == ANTES["snapshot"]
    assert digest("\n".join(requests)) == ANTES["requests"]
    await runner.run(prepared, monitor_capacity=False)
    manifest = json.loads((tmp_path / "experiments/h1/manifest.json").read_text())
    del manifest["created_at"]
    assert hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest() == ANTES["manifest"]
    assert manifest["metadata"]["agent_attempts_per_execution"] == 1


@pytest.mark.parametrize("value", [0, 4, -1, True, "2", 1.0, None])
def test_config_rejects_attempts_outside_one_to_three(value):
    spec = demo_spec("c")
    spec["budget"] = {"max_agent_attempts": value}
    with pytest.raises(ValueError, match="max_agent_attempts"):
        validate_spec(spec)


@pytest.mark.parametrize("value", [1, 2, 3])
def test_config_accepts_one_to_three_and_does_not_write_the_default(value):
    spec = demo_spec("c")
    spec["budget"] = {"max_agent_attempts": value}
    assert validate_spec(spec)["budget"]["max_agent_attempts"] == value
    assert "max_agent_attempts" not in validate_spec(demo_spec("c"))["budget"]


@pytest.mark.asyncio
async def test_herd_blind_spec_takes_attempts_from_panel_and_derived_specs_keep_it(tmp_path):
    panel = {"mode": "demo", "providers": {"simulador": {"kind": "demo"}}, "instructions": "Escolha uma opção.", "sampling": {},
             "participants": [{"provider": "simulador", "model": "demo-v1"} for _ in range(3)], "max_agent_attempts": 2}
    question = {"id": "q1", "question": "Qual?", "options": [{"id": "option-a", "content": "A"}, {"id": "option-b", "content": "B"}]}
    spec = blind_spec(question, panel, run_id="r", condition_id="B1")
    assert spec["budget"]["max_agent_attempts"] == 2
    assert "max_agent_attempts" not in blind_spec(question, {k: v for k, v in panel.items() if k != "max_agent_attempts"}, run_id="r", condition_id="B1")["budget"]
    runner = ExperimentRunner(tmp_path)
    result = await runner.run(runner.prepare(spec), monitor_capacity=False)
    assert result["status"] == "complete"
    derived = derive_spec(tmp_path, spec["experiment_id"], "r-q1-b3", "self", condition_id="B3")
    assert derived["budget"]["max_agent_attempts"] == 2
    assert runner.prepare(derived).spec["budget"]["max_agent_attempts"] == 2
